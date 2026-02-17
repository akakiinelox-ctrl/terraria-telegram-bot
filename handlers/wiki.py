import requests
import re
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.utils.keyboard import InlineKeyboardBuilder

router = Router()

class WikiStates(StatesGroup):
    waiting_for_query = State()

def clean_wiki_text(text):
    # Убираем технические пометки и ссылки в скобках
    text = re.sub(r'\{.*?\}', '', text)
    text = re.sub(r'\[\[.*?\|(.*?)\]\]', r'\1', text) # [[Ссылка|Текст]] -> Текст
    text = re.sub(r'\[\[(.*?)\]\]', r'\1', text)     # [[Текст]] -> Текст
    text = re.sub(r'\'{2,}', '', text)               # Убираем жирный/курсив ''
    return text.strip()

@router.callback_query(F.data == "m_wiki")
async def wiki_start(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(WikiStates.waiting_for_query)
    await callback.message.answer("🔍 <b>Глобальный поиск по Wiki.gg</b>\n\nВведите название (например: <i>Зенит, Плантера, Пчеловод</i>):", parse_mode="HTML")

@router.message(WikiStates.waiting_for_query)
async def wiki_fetch(message: types.Message, state: FSMContext):
    user_query = message.text.strip()
    msg = await message.answer("📡 <i>Запрос к центральному архиву...</i>", parse_mode="HTML")
    
    # Мы используем API, которое возвращает ГОТОВЫЙ ТЕКСТ (prop=extracts)
    url = "https://terraria.wiki.gg/ru/api.php"
    
    params = {
        "action": "query",
        "format": "json",
        "prop": "extracts|pageimages",
        "titles": user_query,
        "exintro": True,      # Взять только вступление (самая суть)
        "explaintext": True,  # ВЕРНУТЬ ЧИСТЫЙ ТЕКСТ БЕЗ HTML ТЕГОВ
        "redirects": 1,       # Автоматически исправлять регистр и редиректы
        "piprop": "original"  # Получить ссылку на картинку
    }

    try:
        response = requests.get(url, params=params, timeout=10).json()
        pages = response.get("query", {}).get("pages", {})
        
        if not pages or "-1" in pages:
            # Если не нашли по точному названию, пробуем поиск по списку
            search_params = {
                "action": "query",
                "list": "search",
                "srsearch": user_query,
                "format": "json",
                "srlimit": 1
            }
            s_res = requests.get(url, params=search_params).json()
            if s_res.get("query", {}).get("search"):
                # Нашли через поиск - повторяем основной запрос с правильным названием
                correct_title = s_res["query"]["search"][0]["title"]
                params["titles"] = correct_title
                response = requests.get(url, params=params).json()
                pages = response.get("query", {}).get("pages", {})

        page_id = list(pages.keys())[0]
        
        if page_id == "-1":
            await msg.edit_text("❌ <b>Ничего не найдено.</b> Попробуй уточнить название.")
            await state.clear()
            return

        page_data = pages[page_id]
        title = page_data.get("title", "Информация")
        text = page_data.get("extract", "")
        
        # Обрезаем текст, если он слишком длинный (лимит Telegram)
        if len(text) > 850:
            text = text[:850] + "..."
            
        if not text:
            text = "К сожалению, описание для этого предмета в базе API отсутствует. Проверьте правильность написания."

        # Картинка
        img_url = page_data.get("original", {}).get("source")

        builder = InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="🏠 Меню", callback_data="to_main"))
        caption = f"📖 <b>{title.upper()}</b>\n━━━━━━━━━━━━━━\n\n{text}"

        if img_url:
            await message.answer_photo(photo=img_url, caption=caption[:1024], reply_markup=builder.as_markup(), parse_mode="HTML")
        else:
            await message.answer(caption[:4096], reply_markup=builder.as_markup(), parse_mode="HTML")
            
        await msg.delete()

    except Exception as e:
        await msg.edit_text(f"⚠️ <b>Критическая ошибка:</b> {str(e)}")
    
    await state.clear()
