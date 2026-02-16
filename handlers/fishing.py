from aiogram import Router, types, F
from aiogram.utils.keyboard import InlineKeyboardBuilder
import json
import os

router = Router()

def get_data():
    path = "data/fishing.json"
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

@router.callback_query(F.data == "m_fishing")
async def fishing_menu(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🐠 Квестовая рыба", callback_data="fish_q"))
    builder.row(types.InlineKeyboardButton(text="📦 Рыболовные ящики", callback_data="fish_c"))
    builder.row(types.InlineKeyboardButton(text="🏠 В меню", callback_data="to_main"))
    await callback.message.edit_text("🎣 <b>Справочник Рыболова</b>\n\nЗдесь ты найдешь информацию о квестах Рыбака и содержимом ящиков.", reply_markup=builder.as_markup(), parse_mode="HTML")

@router.callback_query(F.data == "fish_q")
async def fish_biomes(callback: types.CallbackQuery):
    data = get_data().get("quests", {})
    builder = InlineKeyboardBuilder()
    for biome in data.keys():
        builder.add(types.InlineKeyboardButton(text=biome, callback_data=f"fq_b:{biome}"))
    builder.adjust(2).row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="m_fishing"))
    await callback.message.edit_text("📍 <b>Выбери биом, который указал Рыбак:</b>", reply_markup=builder.as_markup(), parse_mode="HTML")

@router.callback_query(F.data.startswith("fq_b:"))
async def fish_list(callback: types.CallbackQuery):
    biome = callback.data.split(":")[1]
    data = get_data().get("quests", {}).get(biome, [])
    
    text = f"📍 <b>Биом: {biome}</b>\n━━━━━━━━━━━━━━\n\n"
    for fish in data:
        text += f"🐟 <b>{fish['name']}</b>\n"
        text += f"└ 📏 Слой: <i>{fish.get('height', 'Любой')}</i>\n"
        text += f"└ 💡 {fish['info']}\n\n"
    
    builder = InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="fish_q"))
    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")

@router.callback_query(F.data == "fish_c")
async def fishing_crates(callback: types.CallbackQuery):
    data = get_data().get("crates", [])
    text = "📦 <b>Рыболовные ящики</b>\n━━━━━━━━━━━━━━\n\n"
    for crate in data:
        text += f"🔹 <b>{crate['name']}</b>\n"
        text += f"└ 🎁 Лут: {crate['drop']}\n"
        text += f"└ 🍀 Шанс: {crate['chance']}\n\n"
    
    builder = InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="m_fishing"))
    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")

