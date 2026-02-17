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

def clean_text(text):
    # Убираем ссылки [1], [править] и лишние пробелы
    text = re.sub(r'\[.*?\]', '', text)
    text = text.replace('править', '').replace('править код', '')
    return " ".join(text.split())

async def get_wiki_page_title(query):
    search_url = "https://terraria.fandom.com/ru/api.php"
    params = {
        "action": "query",
        "list": "search",
        "srsearch": query,
        "format": "json",
        "srlimit": 1
    }
    try:
        r = requests.get(search_url, params=params, timeout=5)
        data = r.json()
        if 'query' in data and data['query']['search']:
            return data['query']['search'][0]['title']
    except:
        return None
    return None

@router.callback_query(F.data == "m_wiki")
async def wiki_start(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(WikiStates.waiting_for_query)
    await callback.message.answer("🔍 <b>Что ищем на Вики?</b>\n<i>Например: Плантера, Зенит, Стена плоти</i>", parse_mode="HTML")

@router.message(WikiStates.waiting_for_query)
async def wiki_fetch(message: types.Message, state: FSMContext):
    user_query = message.text.strip()
    msg = await message.answer("📡 <i>Ищу в архивах...</i>", parse_mode="HTML")
    
    correct_title = await get_wiki_page_title(user_query)
    
    if not correct_title:
        await msg.edit_text("❌ <b>Ничего не найдено.</b>")
        await state.clear()
        return

    url = f"https://terraria.fandom.com/ru/wiki/{correct_title.replace(' ', '_')}"
    
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = 'utf-8' # Гарантируем правильную кодировку
        soup = BeautifulSoup(response.text, 'lxml')
        
        # 1. Поиск картинки
        img_url = None
        aside = soup.find('aside', class_='portable-infobox')
        if aside:
            img_tag = aside.find('img')
            if img_tag:
                img_url = img_tag.get('src')

        # 2. Поиск контента (План Б)
        # Сначала ищем в стандартном блоке
        content = soup.find('div', class_='mw-parser-output')
        
        # Если не нашли или там пусто, ищем просто все параграфы в статье
        paragraphs = []
        if content:
            # Чистим мусор
            for extra in content.find_all(['div', 'table', 'aside', 'script', 'style', 'blockquote']):
                extra.decompose()
            paragraphs = content.find_all('p', recursive=False)
        
        # Если в основном блоке пусто, пробуем найти любые P на странице
        if not paragraphs:
            paragraphs = soup.find_all('p')

        description = ""
        count = 0
        for p in paragraphs:
            txt = clean_text(p.text)
            # Игнорируем слишком короткие строки и служебные фразы
            if len(txt) > 50: 
                description += txt + "\n\n"
                count += 1
            if count >= 3: # Берем первые 3 абзаца
                break

        if not description:
            description = "Не удалось извлечь текст. Попробуйте уточнить запрос или проверьте страницу вручную."

        builder = InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="🏠 В меню", callback_data="to_main"))
        caption = f"📖 <b>{correct_title.upper()}</b>\n━━━━━━━━━━━━━━\n\n{description}"

        if img_url:
            # Ограничиваем длину подписи к фото (лимит Telegram 1024 символа)
            await message.answer_photo(photo=img_url, caption=caption[:1024], reply_markup=builder.as_markup(), parse_mode="HTML")
        else:
            await message.answer(caption[:4096], reply_markup=builder.as_markup(), parse_mode="HTML")
            
        await msg.delete()

    except Exception as e:
        await msg.edit_text(f"⚠️ <b>Ошибка:</b> {str(e)}")
    
    await state.clear()
