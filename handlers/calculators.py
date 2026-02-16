from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.utils.keyboard import InlineKeyboardBuilder

router = Router()

class CalcStates(StatesGroup):
    wait_goblin = State()
    wait_ore = State()

@router.callback_query(F.data == "m_calc")
async def calc_menu(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="💰 Цены Гоблина", callback_data="calc_g"))
    builder.row(types.InlineKeyboardButton(text="⛏️ Расчет руды", callback_data="calc_o"))
    builder.row(types.InlineKeyboardButton(text="🏠 В меню", callback_data="to_main"))
    await callback.message.edit_text("🧮 <b>Технический отдел</b>\n\nВыбери нужный калькулятор:", reply_markup=builder.as_markup(), parse_mode="HTML")

@router.callback_query(F.data == "calc_g")
async def goblin_start(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(CalcStates.wait_goblin)
    await callback.message.answer("💰 <b>Введите базовую цену перековки (в золоте):</b>", parse_mode="HTML")

@router.message(CalcStates.wait_goblin)
async def goblin_res(message: types.Message, state: FSMContext):
    try:
        p = float(message.text.replace(",", "."))
        res = (f"💰 <b>Расчет для {p} золота:</b>\n\n"
               f"😐 База: <code>{p}</code>\n"
               f"😊 Счастье (17%): <code>{round(p*0.83, 2)}</code>\n"
               f"❤️ Макс. счастье (33%): <code>{round(p*0.67, 2)}</code>")
        await message.answer(res, parse_mode="HTML")
        await state.clear()
    except:
        await message.answer("❌ Введите число!")

@router.callback_query(F.data == "calc_o")
async def ore_start(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(CalcStates.wait_ore)
    await callback.message.answer("⛏️ <b>Сколько слитков ты хочешь? (соотношение 4:1):</b>", parse_mode="HTML")

@router.message(CalcStates.wait_ore)
async def ore_res(message: types.Message, state: FSMContext):
    try:
        bars = int(message.text)
        await message.answer(f"⛏️ Для {bars} слитков тебе нужно <b>{bars * 4}</b> единиц руды.", parse_mode="HTML")
        await state.clear()
    except:
        await message.answer("❌ Введите целое число!")

