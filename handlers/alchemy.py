from aiogram import Router, types, F
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
import json
import os

router = Router()

class AlchemyStates(StatesGroup):
    choosing_ingredients = State()

# Рецепты для интерактивной варки
CRAFT_RECIPES = {
    ("Дневноцвет", "Руда"): "🛡️ Зелье железной кожи (+8 защиты)",
    ("Дневноцвет", "Гриб"): "❤️ Зелье регенерации",
    ("Дневноцвет", "Линза"): "🏹 Зелье лучника",
    ("Луноцвет", "Рыба-призрак"): "👻 Зелье невидимости",
    ("Луноцвет", "Падшая звезда"): "🔮 Зелье маны",
    ("Смертоцвет", "Гемопшик"): "💢 Зелье ярости"
}

def get_data():
    path = "data/alchemy.json"
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

@router.callback_query(F.data == "m_alchemy")
async def alchemy_menu(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🔮 Варить зелье", callback_data="alc_craft"))
    builder.row(types.InlineKeyboardButton(text="📜 Книга рецептов", callback_data="alc_book"))
    builder.row(types.InlineKeyboardButton(text="🏠 В меню", callback_data="to_main"))
    await callback.message.edit_text("🧪 <b>Алхимический стол</b>\n\nЗдесь ты можешь сварить зелье или посмотреть готовые наборы для боя.", reply_markup=builder.as_markup(), parse_mode="HTML")

@router.callback_query(F.data == "alc_craft")
async def start_craft(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(AlchemyStates.choosing_ingredients)
    await state.update_data(mix=[])
    builder = InlineKeyboardBuilder()
    items = ["Дневноцвет", "Луноцвет", "Смертоцвет", "Гриб", "Руда", "Линза", "Падшая звезда", "Рыба-призрак"]
    for item in items:
        builder.add(types.InlineKeyboardButton(text=item, callback_data=f"ing:{item}"))
    builder.adjust(2).row(types.InlineKeyboardButton(text="🔥 Начать варку", callback_data="alc_mix"))
    await callback.message.edit_text("🌿 <b>Выбери 2 ингредиента для котла:</b>", reply_markup=builder.as_markup(), parse_mode="HTML")

@router.callback_query(F.data.startswith("ing:"))
async def add_ing(callback: types.CallbackQuery, state: FSMContext):
    ing = callback.data.split(":")[1]
    data = await state.get_data()
    mix = data.get('mix', [])
    if len(mix) < 2 and ing not in mix:
        mix.append(ing)
        await state.update_data(mix=mix)
        await callback.answer(f"Добавлено: {ing}")
    else:
        await callback.answer("Нельзя добавить больше или этот предмет уже в котле!")

@router.callback_query(F.data == "alc_mix")
async def mix_final(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    mix = data.get('mix', [])
    if len(mix) < 2:
        return await callback.answer("Нужно минимум 2 ингредиента!")
    
    res = CRAFT_RECIPES.get(tuple(sorted(mix)), "💥 Ошибка! Получилась бесполезная жижа...")
    builder = InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="🔄 Еще раз", callback_data="alc_craft")).row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="m_alchemy"))
    await callback.message.edit_text(f"🧪 <b>Результат:</b>\n\n{res}", reply_markup=builder.as_markup(), parse_mode="HTML")
    await state.clear()

@router.callback_query(F.data == "alc_book")
async def alchemy_book(callback: types.CallbackQuery):
    data = get_data().get("sets", {})
    builder = InlineKeyboardBuilder()
    for key, val in data.items():
        builder.row(types.InlineKeyboardButton(text=val['name'], callback_data=f"alc_s:{key}"))
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="m_alchemy"))
    await callback.message.edit_text("📜 <b>Книга проверенных рецептов:</b>", reply_markup=builder.as_markup(), parse_mode="HTML")

@router.callback_query(F.data.startswith("alc_s:"))
async def alchemy_set(callback: types.CallbackQuery):
    set_key = callback.data.split(":")[1]
    alc_set = get_data()["sets"][set_key]
    text = f"🧪 <b>{alc_set['name']}</b>\n━━━━━━━━━━━━━━\n\n"
    for p in alc_set['potions']:
        text += f"🔹 <b>{p['name']}</b>\n└ ✨ {p['effect']}\n└ 🛠 {p['recipe']}\n\n"
    
    builder = InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="alc_book"))
    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")

