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
    # Убираем ссылки в квадратных скобках [1], [2] и лишние пробелы
    text = re.sub(r'\[.*?\]', '', text)
    text = text.replace('править', '').replace('править код', '')
    return " ".join(text.split())

@router.callback_query(F.data == "m_wiki")
async def wiki_start(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(WikiStates.waiting_for_query)
    await callback.message.answer("🔍 <b>Напиши название (предмет, босс, событие):</b>\n<i>Пример: Терра-меч, Плантера, Кровавая луна</i>", parse_mode="HTML")

@router.message(WikiStates.waiting_for_query)
async def wiki_fetch(message: types.Message, state: FSMContext):
    # Форматируем запрос: первая буква заглавная, пробелы -> нижнее подчеркивание
    raw_query = message.text.strip()
    query = raw_query.capitalize().replace(" ", "_")
    url = f"https://terraria.fandom.com/ru/wiki/{query}"
    
    msg = await message.answer("📡 <i>Связываюсь с архивами Википедии...</i>", parse_mode="HTML")
    
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            await msg.edit_text("❌ <b>Ничего не найдено.</b>\nПопробуй написать точное название с большой буквы.")
            await state.clear()
            return

        soup = BeautifulSoup(response.text, 'lxml')
        
        # Вытягиваем картинку из инфобокса (правая колонка)
        img_url = None
        aside = soup.find('aside', class_='portable-infobox')
        if aside:
            img_tag = aside.find('img')
            if img_tag:
                img_url = img_tag.get('src')

        # Собираем текстовое описание
        content = soup.find('div', class_='mw-parser-output')
        paragraphs = content.find_all('p', recursive=False)
        
        description = ""
        for p in paragraphs:
            txt = clean_text(p.text)
            if len(txt) > 30: # Игнорируем пустые или слишком короткие строки
                description += txt + "\n\n"
            if len(description) > 700: # Лимит, чтобы влезло в сообщение
                break

        if not description:
            description = "К сожалению, не удалось извлечь текстовое описание, но вы можете перейти по ссылке."

        builder = InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="to_main"))
        
        caption = f"📖 <b>{raw_query.upper()}</b>\n━━━━━━━━━━━━━━\n\n{description}"
        
        if img_url:
            await message.answer_photo(photo=img_url, caption=caption[:1024], reply_markup=builder.as_markup(), parse_mode="HTML")
        else:
            await message.answer(caption[:4096], reply_markup=builder.as_markup(), parse_mode="HTML")
            
        await msg.delete()

    except Exception as e:
        await msg.edit_text(f"⚠️ <b>Ошибка парсинга:</b> {str(e)}")
    
    await state.clear()
