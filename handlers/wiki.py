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

# Заголовки, чтобы нас всегда пускали
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36'
}

def clean_text(text):
    # Удаляем сноски [1], [править] и мусорные символы
    text = re.sub(r'\[.*?\]', '', text)
    text = text.replace('править', '').replace('править код', '')
    return " ".join(text.split())

@router.callback_query(F.data == "m_wiki")
async def wiki_start(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(WikiStates.waiting_for_query)
    await callback.message.answer("🔍 <b>База данных Террарии</b>\n\nВведите название предмета, босса или события (на русском):", parse_mode="HTML")

@router.message(WikiStates.waiting_for_query)
async def wiki_fetch(message: types.Message, state: FSMContext):
    user_query = message.text.strip()
    msg = await message.answer("📡 <i>Считываю данные из зашифрованного архива...</i>", parse_mode="HTML")
    
    # Мы переходим на официальную Wiki.gg (она стабильнее)
    search_url = "https://terraria.wiki.gg/ru/api.php"
    
    try:
        # 1. Поиск страницы
        search_params = {
            "action": "query",
            "list": "search",
            "srsearch": user_query,
            "format": "json",
            "srlimit": 1
        }
        
        search_res = requests.get(search_url, params=search_params, headers=HEADERS).json()
        
        if not search_res.get('query', {}).get('search'):
            await msg.edit_text("❌ <b>Объект не найден в базе.</b>\nПопробуйте другое название.")
            await state.clear()
            return

        page_title = search_res['query']['search'][0]['title']
        page_url = f"https://terraria.wiki.gg/ru/wiki/{page_title.replace(' ', '_')}"
        
        # 2. Загрузка страницы
        response = requests.get(page_url, headers=HEADERS)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'lxml')

        # 3. Ищем картинку (в инфобоксе или первую в статье)
        img_url = None
        # Проверяем инфобокс
        infobox = soup.find('table', class_='infobox') or soup.find('aside')
        if infobox:
            img_tag = infobox.find('img')
            if img_tag:
                img_url = img_tag.get('src')
                if img_url.startswith('/'):
                    img_url = "https://terraria.wiki.gg" + img_url

        # 4. Собираем ВЕСЬ текст из первых нескольких абзацев
        content = soup.find('div', class_='mw-parser-output')
        description = ""
        
        if content:
            # Чистим всё лишнее перед чтением
            for junk in content.find_all(['table', 'div', 'aside', 'script', 'style', 'span']):
                if 'class' in junk.attrs and 'mw-headline' in junk['class']:
                    continue # Оставляем заголовки если нужно
                junk.decompose()

            # Собираем текст
            paragraphs = content.find_all('p')
            for p in paragraphs:
                txt = clean_text(p.text)
                if len(txt) > 30:
                    description += txt + "\n\n"
                if len(description) > 900: # Максимум для одного сообщения
                    break

        if not description:
            description = "Текст описания не удалось извлечь автоматически, но объект существует в базе."

        builder = InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="🏠 Главное меню", callback_data="to_main"))
        
        caption = f"📖 <b>{page_title.upper()}</b>\n━━━━━━━━━━━━━━\n\n{description}"

        if img_url:
            await message.answer_photo(photo=img_url, caption=caption[:1024], reply_markup=builder.as_markup(), parse_mode="HTML")
        else:
            await message.answer(caption[:4096], reply_markup=builder.as_markup(), parse_mode="HTML")

        await msg.delete()

    except Exception as e:
        await msg.edit_text(f"⚠️ <b>Системная ошибка:</b> {str(e)}")
    
    await state.clear()
