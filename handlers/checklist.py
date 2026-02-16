from aiogram import Router, types, F
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

router = Router()

class ChecklistState(StatesGroup):
    active_list = State()

CHECKLIST_DATA = {
    "start": {
        "name": "🌱 Начало (Pre-Boss)",
        "items": ["Построить 5 домов", "Найти 5 Кристаллов жизни", "Скрафтить Золотую броню", "Найти Крюк-кошку", "Сделать Обрез или Лук"]
    },
    "pre_hm": {
        "name": "🌋 Финал Pre-HM",
        "items": ["Собрать Грань Ночи", "Максить 400 HP", "Построить дорогу в Аду", "Окружить порчу рвами", "Перековать аксессуары"]
    },
    "hardmode_start": {
        "name": "⚙️ Ранний Хардмод",
        "items": ["Разбить 3 алтаря", "Скрафтить наковальню", "Выбить крылья", "Найти Фрукты жизни", "Сделать броню тира 1"]
    }
}

@router.callback_query(F.data == "m_checklist")
async def checklist_main(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    builder = InlineKeyboardBuilder()
    for key, val in CHECKLIST_DATA.items():
        builder.row(types.InlineKeyboardButton(text=f"📍 {val['name']}", callback_data=f"chk_open:{key}"))
    builder.row(types.InlineKeyboardButton(text="🏠 В меню", callback_data="to_main"))
    await callback.message.edit_text("📋 <b>Интерактивный чек-лист</b>\n\nВыбери этап, чтобы отмечать выполненные задачи:", reply_markup=builder.as_markup(), parse_mode="HTML")

@router.callback_query(F.data.startswith("chk_open:"))
async def checklist_view(callback: types.CallbackQuery, state: FSMContext):
    cat = callback.data.split(":")[1]
    await state.update_data(current_cat=cat, completed=[])
    await render_checklist(callback.message, cat, [])

async def render_checklist(message: types.Message, cat, completed_indices):
    items = CHECKLIST_DATA[cat]['items']
    builder = InlineKeyboardBuilder()
    
    for i, item in enumerate(items):
        icon = "✅" if i in completed_indices else "⭕"
        builder.row(types.InlineKeyboardButton(text=f"{icon} {item}", callback_data=f"chk_tog:{i}"))
    
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="m_checklist"))
    
    text = f"📋 <b>Этап: {CHECKLIST_DATA[cat]['name']}</b>\nНажимай на кнопки, чтобы отметить прогресс:"
    await message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")

@router.callback_query(F.data.startswith("chk_tog:"))
async def checklist_toggle(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    index = int(callback.data.split(":")[1])
    completed = data.get('completed', [])
    
    if index in completed:
        completed.remove(index)
    else:
        completed.append(index)
    
    await state.update_data(completed=completed)
    await render_checklist(callback.message, data['current_cat'], completed)

