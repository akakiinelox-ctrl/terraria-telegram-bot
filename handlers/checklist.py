from aiogram import Router, types, F
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

router = Router()

class ChecklistState(StatesGroup):
    viewing = State()

CHECKLIST_DATA = {
    "start": {
        "name": "🌱 Начало (Pre-Boss)",
        "items": [
            "🏠 Построить 5+ домов (Гид, Торговец...)",
            "❤️ Найти 5 Кристаллов жизни (100 -> 200 HP)",
            "💎 Сет Золотой или Платиновой брони",
            "🔗 Найти или скрафтить Крюк-кошку",
            "⛏️ Кирка для добычи Метеорита/Демонита"
        ]
    },
    "pre_hm": {
        "name": "🌋 Финал Pre-HM",
        "items": [
            "⚔️ Собрать Грань Ночи (Night's Edge)",
            "❤️ Максимизировать HP до 400",
            "🌋 Построить дорогу в Аду (1500+ блоков)",
            "🌳 Выкопать рвы вокруг базы от порчи",
            "🎒 Перековать аксессуары на +4 защиты/урона"
        ]
    },
    "hardmode_start": {
        "name": "⚙️ Ранний Хардмод",
        "items": [
            ("⚒️ Разбить 3+ алтаря и сделать наковальню"),
            ("🧚 Выбить первые крылья (Ангел/Демон/Лиственные)"),
            ("🍏 Найти Фрукты жизни в джунглях (400 -> 500 HP)"),
            ("🛡️ Скрафтить броню из Титана или Адамантита"),
            ("🔑 Выбить Ключ-форму или Световой ключ")
        ]
    }
}

@router.callback_query(F.data == "m_checklist")
async def checklist_menu(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    builder = InlineKeyboardBuilder()
    for key, val in CHECKLIST_DATA.items():
        builder.row(types.InlineKeyboardButton(text=f"📍 {val['name']}", callback_data=f"chk_o:{key}"))
    builder.row(types.InlineKeyboardButton(text="🏠 В меню", callback_data="to_main"))
    await callback.message.edit_text("📋 <b>Интерактивный чек-лист</b>\n\nВыбери этап, чтобы отмечать выполненные задачи:", reply_markup=builder.as_markup(), parse_mode="HTML")

@router.callback_query(F.data.startswith("chk_o:"))
async def checklist_open(callback: types.CallbackQuery, state: FSMContext):
    cat = callback.data.split(":")[1]
    await state.update_data(current_cat=cat, completed=[])
    await render_list(callback.message, cat, [])

async def render_list(message: types.Message, cat, completed_indices):
    items = CHECKLIST_DATA[cat]['items']
    builder = InlineKeyboardBuilder()
    
    for i, item in enumerate(items):
        icon = "✅" if i in completed_indices else "⭕"
        builder.row(types.InlineKeyboardButton(text=f"{icon} {item}", callback_data=f"chk_t:{i}"))
    
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="m_checklist"))
    
    text = f"📋 <b>Этап: {CHECKLIST_DATA[cat]['name']}</b>\nНажимай на задачи, чтобы отметить их:"
    await message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")

@router.callback_query(F.data.startswith("chk_t:"))
async def checklist_toggle(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    index = int(callback.data.split(":")[1])
    completed = data.get('completed', [])
    
    if index in completed:
        completed.remove(index)
    else:
        completed.append(index)
    
    await state.update_data(completed=completed)
    await render_list(callback.message, data['current_cat'], completed)

