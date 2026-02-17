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

# Заголовки для имитации браузера
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36'
}

def clean_text(text):
    """Очистка текста от мусора вики-разметки"""
    text = re.sub(r'\[.*?\]', '', text) # Убираем [1], [править]
    text = text.replace('править', '').replace('править код', '')
    return " ".join(text.split())

@router.callback_query(F.data == "m_wiki")
async def wiki_start(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(WikiStates.waiting_for_query)
    await callback.message.answer("🔍 <b>База данных Террарии (Wiki.gg)</b>\n\nВведите название предмета, босса или моба на русском:")

@router.message(WikiStates.waiting_for_query)
async def wiki_fetch(message: types.Message, state: FSMContext):
    user_query = message.text.strip()
    msg = await message.answer("📡 <i>Считываю архивы...</i>", parse_mode="HTML")
    
    api_url = "https://terraria.wiki.gg/ru/api.php"
    
    try:
        # 1. Используем API для поиска и получения текста (extract)
        # Это самый надежный способ получить текст без мусора
        params = {
            "action": "query",
            "format": "json",
            "prop": "extracts|pageimages",
            "exintro": True,      # Только вступление
            "explaintext": True,  # Только чистый текст без HTML
            "titles": user_query,
            "redirects": 1,       # Авто-переход (плантера -> Плантера)
            "piprop": "original"
        }
        
        response = requests.get(api_url, params=params, headers=HEADERS, timeout=10).json()
        pages = response.get("query", {}).get("pages", {})
        page_id = list(pages.keys())[0]

        # Если по прямому названию не нашли, пробуем глобальный поиск
        if page_id == "-1":
            search_params = {
                "action": "query",
                "list": "search",
                "srsearch": user_query,
                "format": "json",
                "srlimit": 1
            }
            s_res = requests.get(api_url, params=search_params, headers=HEADERS).json()
            if s_res.get("query", {}).get("search"):
                user_query = s_res["query"]["search"][0]["title"]
                # Повторяем запрос с правильным титулом
                params["titles"] = user_query
                response = requests.get(api_url, params=params, headers=HEADERS).json()
                pages = response.get("query", {}).get("pages", {})
                page_id = list(pages.keys())[0]

        if page_id == "-1":
            await msg.edit_text("❌ <b>Ничего не найдено.</b> Попробуй другое название.")
            await state.clear()
            return

        page_data = pages[page_id]
        title = page_data.get("title", "Информация")
        description = page_data.get("extract", "")

        # 2. Получаем картинку (через BeautifulSoup, так как API иногда жадничает)
        img_url = None
        # Пробуем взять картинку из API
        if "original" in page_data:
            img_url = page_data["original"].get("source")
        
        # Если API не дало картинку, идем парсить страницу
        if not img_url:
            page_url = f"https://terraria.wiki.gg/ru/wiki/{title.replace(' ', '_')}"
            soup_res = requests.get(page_url, headers=HEADERS)
            soup = BeautifulSoup(soup_res.text, 'lxml')
            
            # Ищем в инфобоксе
            aside = soup.find('aside') or soup.find('table', class_='infobox')
            if aside:
                img_tag = aside.find('img')
                if img_tag:
                    img_url = img_tag.get('src')
                    if img_url and img_url.startswith('/'):
                        img_url = "https://terraria.wiki.gg" + img_url

        # 3. Если API выдало пустой текст, применяем парсинг «План Б»
        if len(description) < 20:
            page_url = f"https://terraria.wiki.gg/ru/wiki/{title.replace(' ', '_')}"
            soup_res = requests.get(page_url, headers=HEADERS)
            soup = BeautifulSoup(soup_res.text, 'lxml')
            content = soup.find('div', class_='mw-parser-output')
            if content:
                # Удаляем таблицы и инфобоксы
                for junk in content.find_all(['table', 'aside', 'div']):
                    junk.decompose()
                paragraphs = content.find_all('p')
                description = ""
                for p in paragraphs:
                    txt = clean_text(p.text)
                    if len(txt) > 40:
                        description += txt + "\n\n"
                    if len(description) > 800: break

        # Окончательная сборка сообщения
        if not description:
            description = "Описание не найдено, но предмет существует в базе."

        builder = InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="🏠 Меню", callback_data="to_main"))
        caption = f"📖 <b>{title.upper()}</b>\n━━━━━━━━━━━━━━\n\n{description[:900]}"

        if img_url:
            await message.answer_photo(photo=img_url, caption=caption[:1024], reply_markup=builder.as_markup(), parse_mode="HTML")
        else:
            await message.answer(caption[:4096], reply_markup=builder.as_markup(), parse_mode="HTML")
            
        await msg.delete()

    except Exception as e:
        await msg.edit_text(f"⚠️ <b>Ошибка:</b> {str(e)}")
    
    await state.clear()
