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
    # Убираем [1], [править] и лишние пробелы
    text = re.sub(r'\[.*?\]', '', text)
    text = text.replace('править', '').replace('править код', '')
    return " ".join(text.split())

@router.callback_query(F.data == "m_wiki")
async def wiki_start(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(WikiStates.waiting_for_query)
    await callback.message.answer("🔍 <b>Поиск по Wiki.gg / Fandom</b>\n\nВведите название (например: <i>Плантера, Зенит, Мурамаса</i>):", parse_mode="HTML")

@router.message(WikiStates.waiting_for_query)
async def wiki_fetch(message: types.Message, state: FSMContext):
    user_query = message.text.strip()
    msg = await message.answer("📡 <i>Считываю данные со страницы...</i>", parse_mode="HTML")
    
    # Сначала найдем правильный URL через поиск
    search_url = "https://terraria.fandom.com/ru/api.php"
    search_params = {
        "action": "query",
        "list": "search",
        "srsearch": user_query,
        "format": "json",
        "srlimit": 1
    }

    try:
        s_res = requests.get(search_url, params=search_params, headers=HEADERS).json()
        if not s_res.get("query", {}).get("search"):
            await msg.edit_text("❌ <b>Ничего не найдено.</b>")
            return

        title = s_res["query"]["search"][0]["title"]
        url = f"https://terraria.fandom.com/ru/wiki/{title.replace(' ', '_')}"
        
        # ЗАГРУЖАЕМ СТРАНИЦУ ПОЛНОСТЬЮ
        page_res = requests.get(url, headers=HEADERS)
        page_res.encoding = 'utf-8'
        soup = BeautifulSoup(page_res.text, 'lxml')

        # 1. Ищем картинку в инфобоксе
        img_url = None
        aside = soup.find('aside') or soup.find('table', class_='infobox')
        if aside:
            img_tag = aside.find('img')
            if img_tag:
                img_url = img_tag.get('src')
                if img_url.startswith('//'): img_url = "https:" + img_url

        # 2. Ищем текст (Прямой парсинг HTML)
        description = ""
        content = soup.find('div', class_='mw-parser-output')
        
        if content:
            # Находим все параграфы, которые НЕ находятся внутри таблиц или инфобоксов
            paragraphs = content.find_all('p', recursive=False)
            
            # Если на верхнем уровне нет <p>, ищем по всей статье, но берем первый длинный
            if not paragraphs:
                paragraphs = content.find_all('p')

            for p in paragraphs:
                txt = clean_text(p.text)
                if len(txt) > 50: # Берем первый нормальный абзац
                    description = txt
                    break
        
        if not description:
            description = "Не удалось извлечь текст. Страница слишком сложная для автоматического чтения."

        builder = InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="🏠 Меню", callback_data="to_main"))
        caption = f"📖 <b>{title.upper()}</b>\n━━━━━━━━━━━━━━\n\n{description[:900]}"

        if img_url:
            await message.answer_photo(photo=img_url, caption=caption[:1024], reply_markup=builder.as_markup(), parse_mode="HTML")
        else:
            await message.answer(caption[:4096], reply_markup=builder.as_markup(), parse_mode="HTML")
        
        await msg.delete()

    except Exception as e:
        await msg.edit_text(f"⚠️ Ошибка: {e}")
    
    await state.clear()
