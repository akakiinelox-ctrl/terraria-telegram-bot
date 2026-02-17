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
    await callback.message.answer("🔍 <b>Что ищем на Вики?</b>\n<i>Например: Плантера, Мурамаса, Скелетрон</i>", parse_mode="HTML")

@router.message(WikiStates.waiting_for_query)
async def wiki_fetch(message: types.Message, state: FSMContext):
    user_query = message.text.strip()
    msg = await message.answer("📡 <i>Ищу в архивах...</i>", parse_mode="HTML")
    
    correct_title = await get_wiki_page_title(user_query)
    
    if not correct_title:
        await msg.edit_text("❌ <b>Ничего не найдено.</b>\nПопробуй изменить запрос.")
        await state.clear()
        return

    url = f"https://terraria.fandom.com/ru/wiki/{correct_title.replace(' ', '_')}"
    
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, 'lxml')
        
        # 1. Поиск картинки (безопасный)
        img_url = None
        aside = soup.find('aside', class_='portable-infobox')
        if aside:
            img_tag = aside.find('img')
            if img_tag:
                img_url = img_tag.get('src')

        # 2. Поиск контента (добавлена проверка на None)
        content = soup.find('div', class_='mw-parser-output')
        
        description = "Описание временно недоступно."
        
        if content:
            # Очищаем контент от мусора перед сбором текста
            for extra in content.find_all(['div', 'table', 'aside', 'script', 'style']):
                extra.decompose()
            
            paragraphs = content.find_all('p', recursive=False)
            if paragraphs:
                temp_desc = ""
                for p in paragraphs:
                    txt = clean_text(p.text)
                    if len(txt) > 40:
                        temp_desc += txt + "\n\n"
                    if len(temp_desc) > 800:
                        break
                if temp_desc:
                    description = temp_desc
        else:
            description = "Не удалось найти текстовый блок на странице. Возможно, это страница-список."

        builder = InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="🏠 В меню", callback_data="to_main"))
        caption = f"📖 <b>{correct_title.upper()}</b>\n━━━━━━━━━━━━━━\n\n{description}"

        if img_url:
            await message.answer_photo(photo=img_url, caption=caption[:1024], reply_markup=builder.as_markup(), parse_mode="HTML")
        else:
            await message.answer(caption[:4096], reply_markup=builder.as_markup(), parse_mode="HTML")
            
        await msg.delete()

    except Exception as e:
        await msg.edit_text(f"⚠️ <b>Ошибка парсинга:</b> {str(e)}")
        print(f"Wiki Error: {e}") # Это поможет увидеть ошибку в логах
    
    await state.clear()
