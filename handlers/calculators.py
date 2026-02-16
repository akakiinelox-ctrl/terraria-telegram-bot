from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.utils.keyboard import InlineKeyboardBuilder

router = Router()

class CalcStates(StatesGroup):
    wait_goblin = State()
    wait_ore_count = State()

# Данные для расчетов
ORE_RATIOS = {
    "Медь/Олово (3:1)": 3,
    "Железо/Свинец (3:1)": 3,
    "Серебро/Вольфрам (4:1)": 4,
    "Золото/Платина (4:1)": 4,
    "Демонит/Кримтан (3:1)": 3,
    "Метеорит (3:1)": 3,
    "Адский камень (3:1 + обсидиан)": 3,
    "Адамантит/Титан (5:1)": 5,
    "Хлорофит (6:1)": 6
}

ARMOR_SETS = {
    "🥇 Золото/Платина": 90,
    "🌋 Литая (Адская)": 45,
    "🛡️ Святая броня": 54,
    "🌿 Хлорофитовая": 54,
    "🐢 Черепашья": 54,
    "👻 Спектральная": 54,
    " Beetle (Жук)": 54
}

@router.callback_query(F.data == "m_calc")
async def calc_menu(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="💰 Скидки Гоблина", callback_data="c_goblin"))
    builder.row(types.InlineKeyboardButton(text="⛏️ Калькулятор руды", callback_data="c_ore_list"))
    builder.row(types.InlineKeyboardButton(text="🛡️ Ресурсы на броню", callback_data="c_armor"))
    builder.row(types.InlineKeyboardButton(text="🏠 В меню", callback_data="to_main"))
    await callback.message.edit_text("🧮 <b>Инженерный отдел</b>\n\nВыберите инструмент для расчета:", reply_markup=builder.as_markup(), parse_mode="HTML")

# --- ЛОГИКА ГОБЛИНА ---
@router.callback_query(F.data == "c_goblin")
async def gob_start(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(CalcStates.wait_goblin)
    await callback.message.answer("💰 <b>Введите цену перековки, которую видите у Гоблина (в золоте):</b>", parse_mode="HTML")

@router.message(CalcStates.wait_goblin)
async def gob_res(message: types.Message, state: FSMContext):
    try:
        p = float(message.text.replace(",", "."))
        res = (
            f"💰 <b>Расчет цен перековки:</b>\n\n"
            f"😐 <b>Обычная цена:</b> {p} золота\n"
            f"😊 <b>Со скидкой (17%):</b> <code>{round(p*0.83, 2)}</code>\n"
            f"❤️ <b>Макс. счастье (33%):</b> <code>{round(p*0.67, 2)}</code>\n\n"
            f"💡 <i>Чтобы Гоблин дал макс. скидку, посели его под землей вместе с Механиком!</i>"
        )
        builder = InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="m_calc"))
        await message.answer(res, reply_markup=builder.as_markup(), parse_mode="HTML")
        await state.clear()
    except:
        await message.answer("❌ Введите только число (например: 12.5)")

# --- ЛОГИКА РУДЫ ---
@router.callback_query(F.data == "c_ore_list")
async def ore_list(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    for name, ratio in ORE_RATIOS.items():
        builder.row(types.InlineKeyboardButton(text=name, callback_data=f"ore_val:{ratio}"))
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="m_calc"))
    await callback.message.edit_text("⛏ <b>Выберите тип руды:</b>", reply_markup=builder.as_markup(), parse_mode="HTML")

@router.callback_query(F.data.startswith("ore_val:"))
async def ore_input(callback: types.CallbackQuery, state: FSMContext):
    ratio = int(callback.data.split(":")[1])
    await state.update_data(ratio=ratio)
    await state.set_state(CalcStates.wait_ore_count)
    await callback.message.answer("🔢 <b>Сколько слитков вы хотите получить?</b>", parse_mode="HTML")

@router.message(CalcStates.wait_ore_count)
async def ore_res(message: types.Message, state: FSMContext):
    data = await state.get_data()
    try:
        bars = int(message.text)
        total = bars * data['ratio']
        await message.answer(f"✅ Для <b>{bars}</b> слитков тебе понадобится <b>{total}</b> ед. руды.", 
                             reply_markup=InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="m_calc")).as_markup(),
                             parse_mode="HTML")
        await state.clear()
    except:
        await message.answer("❌ Введите целое число!")

# --- ЛОГИКА БРОНИ ---
@router.callback_query(F.data == "c_armor")
async def armor_list(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    for name, count in ARMOR_SETS.items():
        builder.row(types.InlineKeyboardButton(text=name, callback_data=f"arm_res:{name}:{count}"))
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="m_calc"))
    await callback.message.edit_text("🛡️ <b>Выберите сет брони:</b>\n<i>Я рассчитаю общее количество слитков на весь комплект.</i>", reply_markup=builder.as_markup(), parse_mode="HTML")

@router.callback_query(F.data.startswith("arm_res:"))
async def armor_res(callback: types.CallbackQuery):
    _, name, count = callback.data.split(":")
    text = (f"🛡️ <b>Комплект: {name}</b>\n\n"
            f"📦 Всего нужно: <b>{count} слитков</b>\n"
            f"└ Шлем: 15-20\n"
            f"└ Нагрудник: 20-25\n"
            f"└ Ботинки: 15-20\n\n"
            f"⛏ <i>Не забудь проверить калькулятор руды, чтобы знать сколько копать!</i>")
    builder = InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="c_armor"))
    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")
