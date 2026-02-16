from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.utils.keyboard import InlineKeyboardBuilder
import json
import os

router = Router()

class CraftSearch(StatesGroup):
    waiting_for_name = State()

def get_all_crafts():
    path = "data/crafts/"
    all_data = {}
    if not os.path.exists(path): return all_data
    
    for file in os.listdir(path):
        if file.endswith(".json"):
            with open(os.path.join(path, file), 'r', encoding='utf-8') as f:
                all_data.update(json.load(f))
    return all_data

@router.callback_query(F.data == "m_crafting")
async def craft_main(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🔍 Найти рецепт", callback_data="cr_search"))
    builder.row(types.InlineKeyboardButton(text="🏠 Главное меню", callback_data="to_main"))
    await callback.message.edit_text("⚒ **Глобальный справочник крафтов**\n\nПросто введи название предмета, и я выдам рецепт и станцию для крафта.", reply_markup=builder.as_markup())

@router.callback_query(F.data == "cr_search")
async def start_search(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(CraftSearch.waiting_for_name)
    await callback.message.answer("📝 **Напиши название предмета:**\n<i>(Можно часть названия, например: 'Зенит' или 'Крылья')</i>")

@router.message(CraftSearch.waiting_for_name)
async def process_search(message: types.Message, state: FSMContext):
    query = message.text.lower()
    data = get_all_crafts()
    results = []

    for key, info in data.items():
        if query in info['name'].lower():
            results.append(info)

    if not results:
        await message.answer("❌ Ничего не найдено. Попробуй другое название или проверь опечатки.")
    else:
        # Если результатов много, показываем только первые 5, чтобы не спамить
        for item in results[:5]:
            text = (f"⚙️ <b>{item['name']}</b>\n"
                    f"━━━━━━━━━━━━━━\n"
                    f"📜 <b>Рецепт:</b> {item['recipe']}\n"
                    f"📍 <b>Станция:</b> {item['station']}")
            await message.answer(text, parse_mode="HTML")
        
        if len(results) > 5:
            await message.answer(f"<i>Показано 5 результатов из {len(results)}. Уточни поиск, если не нашел нужного.</i>", parse_mode="HTML")
    
    await state.clear()
