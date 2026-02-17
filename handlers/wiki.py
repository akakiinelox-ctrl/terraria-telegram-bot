import requests
import re
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.utils.keyboard import InlineKeyboardBuilder

router = Router()

class WikiStates(StatesGroup):
    waiting_for_query = State()

def clean_extract(text):
    """Очистка текста от технических символов и пустых строк"""
    if not text: return ""
    # Убираем странные символы и лишние пробелы
    text = re.sub(r'\s+', ' ', text)
    text = text.replace(" ( )", "")
    return text.strip()

@router.callback_query(F.data == "m_wiki")
async def wiki_start(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(WikiStates.waiting_for_query)
    await callback.message.edit_text("🔍 <b>База Знаний Террарии</b>\n\nВведите название предмета (например: <i>Зенит, Плантера</i>):", parse_mode="HTML")

@router.message(WikiStates.waiting_for_query)
async def wiki_fetch(message: types.Message, state: FSMContext):
    query = message.text.strip()
    msg = await message.answer("📡 <i>Запрашиваю данные...</i>", parse_mode="HTML")
    
    # Используем официальное API MediaWiki. Оно создано для ботов.
    # Мы обращаемся к Wiki.gg, так как она стабильнее.
    URL = "https://terraria.wiki.gg/ru/api.php"
    
    params = {
        "action": "query",
        "format": "json",
        "prop": "extracts|pageimages",
        "titles": query,
        "exintro": True,      # Берем только вступление статьи
        "explaintext": True,  # ВАЖНО: возвращает чистый текст без HTML-мусора
        "redirects": 1,       # Автоматически переходит на правильную страницу
        "piprop": "original"  # Ищет картинку в высоком качестве
    }

    try:
        response = requests.get(URL, params=params, timeout=10).json()
        pages = response.get("query", {}).get("pages", {})
        
        # Берем первую найденную страницу
        page_id = list(pages.keys())[0]
        page_data = pages[page_id]

        if page_id == "-1":
            # Если не нашли - попробуем поискать через внутренний поиск
            search_params = {"action": "query", "list": "search", "srsearch": query, "format": "json"}
            s_res = requests.get(URL, params=search_params).json()
            if s_res.get("query", {}).get("search"):
                new_query = s_res["query"]["search"][0]["title"]
                # Повторяем запрос с исправленным именем
                params["titles"] = new_query
                response = requests.get(URL, params=params).json()
                page_data = response["query"]["pages"][list(response["query"]["pages"].keys())[0]]
            else:
                await msg.edit_text("❌ <b>Ничего не найдено.</b> Проверьте название.")
                await state.clear()
                return

        title = page_data.get("title", "Инфо")
        extract = clean_extract(page_data.get("extract", ""))
        img_url = page_data.get("original", {}).get("source")

        # Если текста всё равно мало, берем запасной вариант
        if len(extract) < 10:
            extract = "Описание на русском языке отсутствует или находится в разработке."

        builder = InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="🏠 Меню", callback_data="to_main"))
        
        # Ограничиваем длину текста для Telegram (макс 1024 с картинкой)
        caption = f"📖 <b>{title.upper()}</b>\n━━━━━━━━━━━━━━\n\n{extract[:900]}..."

        if img_url:
            await message.answer_photo(photo=img_url, caption=caption, reply_markup=builder.as_markup(), parse_mode="HTML")
        else:
            await message.answer(caption, reply_markup=builder.as_markup(), parse_mode="HTML")
            
        await msg.delete()

    except Exception as e:
        await msg.edit_text(f"⚠️ <b>Системная ошибка:</b> {e}")
    
    await state.clear()
