from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.utils.keyboard import InlineKeyboardBuilder

router = Router()

class CalcStates(StatesGroup):
    wait_goblin = State()
    wait_ore_count = State()

# Расширенные коэффициенты руды
ORE_RATIOS = {
    "🧱 Медь/Олово (3:1)": 3,
    "⛓️ Железо/Свинец (3:1)": 3,
    "🥈 Серебро/Вольфрам (4:1)": 4,
    "👑 Золото/Платина (4:1)": 4,
    "👿 Демонит/Кримтан (3:1)": 3,
    "☄️ Метеорит (3:1)": 3,
    "🔥 Адский камень (3:1)": 3,
    "💠 Кобальт/Палладий (3:1)": 3,
    "⚒️ Мифрил/Орихалк (4:1)": 4,
    "🔱 Адамантит/Титан (5:1)": 5,
    "🌿 Хлорофит (6:1)": 6,
    "☀️ Люминит (4:1)": 4
}

# Огромный список сетов брони
ARMOR_SETS = {
    "🥇 Платина (Max Pre-Boss)": 90,
    "🌋 Литая (Pre-HM)": 45,
    "🐢 Черепашья (Tank)": 54,
    "🦋 Грибнитовая (Ranger)": 54,
    "👻 Спектральная (Mage)": 54,
    "🎃 Жуткая (Summoner)": 750, # В дереве
    "☀️ Солнечная (Endgame)": 36, # В люминитовых слитках
    "🌀 Вихревая (Endgame)": 36,
    "🔮 Туманная (Endgame)": 36,
    "🌌 Звездная (Endgame)": 36
}

@router.callback_query(F.data == "m_calc")
async def calc_menu(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="💰 Скидки Гоблина", callback_data="c_goblin"))
    builder.row(types.InlineKeyboardButton(text="⛏️ Калькулятор руды", callback_data="c_ore_list"))
    builder.row(types.InlineKeyboardButton(text="🛡️ Ресурсы на броню", callback_data="c_armor"))
    builder.row(types.InlineKeyboardButton(text="🏠 В меню", callback_data="to_main"))
    await callback.message.edit_text("🧮 <b>ИНЖЕНЕРНЫЙ ЦЕХ v2.0</b>\n\nВыбери инструмент для точного расчета ресурсов:", reply_markup=builder.as_markup(), parse_mode="HTML")

@router.callback_query(F.data == "c_goblin")
async def gob_start(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(CalcStates.wait_goblin)
    await callback.message.answer("💰 <b>Введите цену перековки (в золоте):</b>\n<i>Пример: 15.5</i>", parse_mode="HTML")

@router.message(CalcStates.wait_goblin)
async def gob_res(message: types.Message, state: FSMContext):
    try:
        p = float(message.text.replace(",", "."))
        res = (
            f"💰 <b>Результаты перековки:</b>\n"
            f"━━━━━━━━━━━━━━\n"
            f"😐 <b>База:</b> {p}г\n"
            f"😊 <b>С Механиком (17%):</b> <code>{round(p*0.83, 2)}</code>г\n"
            f"❤️ <b>Макс. счастье (33%):</b> <code>{round(p*0.67, 2)}</code>г\n\n"
            f"💡 <i>Совет: Чтобы получить 33%, Гоблин должен жить в Пещерах с Механиком и Красильщиком.</i>"
        )
        await message.answer(res, reply_markup=InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="m_calc")).as_markup(), parse_mode="HTML")
        await state.clear()
    except:
        await message.answer("❌ Ошибка! Введи только число.")

@router.callback_query(F.data == "c_ore_list")
async def ore_list(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    for name, ratio in ORE_RATIOS.items():
        builder.add(types.InlineKeyboardButton(text=name, callback_data=f"ore_val:{ratio}:{name}"))
    builder.adjust(2).row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="m_calc"))
    await callback.message.edit_text("⛏ <b>Какую руду будем плавить?</b>", reply_markup=builder.as_markup(), parse_mode="HTML")

@router.callback_query(F.data.startswith("ore_val:"))
async def ore_input(callback: types.CallbackQuery, state: FSMContext):
    _, ratio, name = callback.data.split(":")
    await state.update_data(ratio=int(ratio), ore_name=name)
    await state.set_state(CalcStates.wait_ore_count)
    await callback.message.answer(f"🔢 <b>Сколько слитков ({name}) тебе нужно?</b>", parse_mode="HTML")

@router.message(CalcStates.wait_ore_count)
async def ore_res(message: types.Message, state: FSMContext):
    data = await state.get_data()
    try:
        bars = int(message.text)
        total = bars * data['ratio']
        await message.answer(f"✅ Для <b>{bars}</b> слитков тебе понадобится <b>{total}</b> ед. руды <i>{data['ore_name']}</i>.", 
                             reply_markup=InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="m_calc")).as_markup(),
                             parse_mode="HTML")
        await state.clear()
    except:
        await message.answer("❌ Введите целое число!")

@router.callback_query(F.data == "c_armor")
async def armor_list(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    for name, count in ARMOR_SETS.items():
        builder.add(types.InlineKeyboardButton(text=name, callback_data=f"arm_res:{name}:{count}"))
    builder.adjust(1).row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="m_calc"))
    await callback.message.edit_text("🛡️ <b>Расчет ресурсов на сеты:</b>", reply_markup=builder.as_markup(), parse_mode="HTML")

@router.callback_query(F.data.startswith("arm_res:"))
async def armor_res(callback: types.CallbackQuery):
    _, name, count = callback.data.split(":")
    text = (f"🛡️ <b>Комплект: {name}</b>\n"
            f"━━━━━━━━━━━━━━\n"
            f"📦 Требуется: <b>{count}</b> ед. материала\n\n"
            f"🧩 <i>Обычно это:\n— Шлем: ~12-15\n— Нагрудник: ~20-24\n— Поножи: ~15-18</i>")
    await callback.message.edit_text(text, reply_markup=InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="c_armor")).as_markup(), parse_mode="HTML")

