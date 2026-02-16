from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.utils.keyboard import InlineKeyboardBuilder
import json
import os

router = Router()

class CraftSearch(StatesGroup):
    waiting_for_name = State()

def search_in_json(query):
    # Бот будет искать по всем файлам в папке data/crafts/
    path = "data/crafts/"
    query = query.lower()
    results = []
    
    if not os.path.exists(path): return []

    for file in os.listdir(path):
        if file.endswith(".json"):
            with open(os.path.join(path, file), 'r', encoding='utf-8') as f:
                data = json.load(f)
                for item_id, info in data.items():
                    if query in info['name'].lower():
                        results.append(info)
    return results

@router.callback_query(F.data == "m_crafting")
async def craft_main(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🔍 Найти рецепт (Поиск)", callback_data="cr_search"))
    builder.row(types.InlineKeyboardButton(text="🏠 Главное меню", callback_data="to_main"))
    await callback.message.edit_text("⚒ **Глобальная кузня**\n\nВ моей базе тысячи предметов. Просто напиши название предмета, и я скажу, как его сделать.", reply_markup=builder.as_markup())

@router.callback_query(F.data == "cr_search")
async def start_search(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(CraftSearch.waiting_for_name)
    await callback.message.answer("📝 **Введите название предмета (или часть названия):**")

@router.message(CraftSearch.waiting_for_name)
async def process_search(message: types.Message, state: FSMContext):
    results = search_in_json(message.text)
    
    if not results:
        await message.answer("❌ Ничего не найдено. Попробуй другое название.")
    else:
        for item in results[:5]: # Показываем первые 5 совпадений
            text = f"⚙️ **{item['name']}**\n━━━━━━━━━━━━━━\n📜 **Рецепт:** {item['recipe']}\n📍 **Станция:** {item['station']}"
            await message.answer(text, parse_mode="Markdown")
    
    await state.clear()
