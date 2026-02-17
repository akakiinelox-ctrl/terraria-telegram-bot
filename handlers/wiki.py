import requests
from bs4 import BeautifulSoup
import re
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.utils.keyboard import InlineKeyboardBuilder

router = Router()

class WikiStates(StatesGroup):
    waiting_for_query = State()

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36'
}

def clean_text(text):
    text = re.sub(r'\[.*?\]', '', text)
    text = text.replace('править', '').replace('править код', '')
    return " ".join(text.split())

@router.callback_query(F.data == "m_wiki")
async def wiki_start(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(WikiStates.waiting_for_query)
    await callback.message.answer("🔍 <b>База знаний Wiki.gg</b>\n\nВведите название (например: <i>Зенит, Плантера, Мурамаса</i>):", parse_mode="HTML")

@router.message(WikiStates.waiting_for_query)
async def wiki_fetch(message: types.Message, state: FSMContext):
    user_query = message.text.strip()
    msg = await message.answer("📡 <i>Сканирую базу данных...</i>", parse_mode="HTML")
    
    api_url = "https://terraria.wiki.gg/ru/api.php"
    
    try:
        # 1. Поиск точного заголовка через API
        search_params = {
            "action": "query",
            "list": "search",
            "srsearch": user_query,
            "format": "json",
            "srlimit": 1
        }
        search_res = requests.get(api_url, params=search_params, headers=HEADERS).json()
        
        if not search_res.get("query", {}).get("search"):
            await msg.edit_text("❌ <b>Предмет не найден.</b> Проверьте название.")
            await state.clear()
            return

        page_title = search_res["query"]["search"][0]["title"]
        page_url = f"https://terraria.wiki.gg/ru/wiki/{page_title.replace(' ', '_')}"
        
        # 2. Глубокий парсинг страницы
        response = requests.get(page_url, headers=HEADERS)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'lxml')
        
        # Удаляем мусор сразу
        content = soup.find('div', class_='mw-parser-output')
        if content:
            for junk in content.find_all(['table', 'aside', 'script', 'style', 'div'], class_=lambda x: x != 'mw-parser-output'):
                if junk.get('class') and ('infobox' in junk.get('class') or 'navbox' in junk.get('class')):
                    junk.decompose()

        # 3. Собираем описание (Берем все P, пока не наберем текст)
        description = ""
        # Сначала пробуем найти параграфы, которые не пустые
        paragraphs = content.find_all('p') if content else []
        
        for p in paragraphs:
            txt = clean_text(p.text)
            if len(txt) > 30:
                description += txt + "\n\n"
            if len(description) > 600: # Оптимальная длина для ТГ
                break
        
        # Если параграфы подвели, берем первый попавшийся текст из div
        if not description.strip() and content:
            description = clean_text(content.get_text(separator=" ").split("править")[0])[:600] + "..."

        # 4. Поиск картинки (самый надежный способ)
        img_url = None
        # Ищем в любой таблице-инфобоксе или просто первую большую картинку
        img_tag = soup.find('table', class_='infobox')
        if img_tag:
            img_tag = img_tag.find('img')
        
        if not img_tag:
            img_tag = soup.find('img', alt=page_title) or soup.find('img')

        if img_tag:
            img_url = img_tag.get('src')
            if img_url and img_url.startswith('/'):
                img_url = "https://terraria.wiki.gg" + img_url

        # Формируем ответ
        builder = InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="🏠 Меню", callback_data="to_main"))
        caption = f"📖 <b>{page_title.upper()}</b>\n━━━━━━━━━━━━━━\n\n{description}"

        if img_url and (img_url.endswith('.png') or img_url.endswith('.jpg')):
            await message.answer_photo(photo=img_url, caption=caption[:1024], reply_markup=builder.as_markup(), parse_mode="HTML")
        else:
            await message.answer(caption[:4096], reply_markup=builder.as_markup(), parse_mode="HTML")
            
        await msg.delete()

    except Exception as e:
        await msg.edit_text(f"⚠️ <b>Ошибка:</b> {str(e)}")
    
    await state.clear()
