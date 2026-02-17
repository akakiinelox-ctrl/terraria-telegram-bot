import os
import json
from aiogram import Router, types, F
from aiogram.utils.keyboard import InlineKeyboardBuilder

router = Router()

def get_data():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(current_dir)
    path = os.path.join(base_dir, "data", "bosses.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

@router.callback_query(F.data == "m_bosses")
async def bosses_main(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🟢 До-Хардмод", callback_data="b_l:pre_hm"),
                types.InlineKeyboardButton(text="🔴 Хардмод", callback_data="b_l:hm"))
    builder.row(types.InlineKeyboardButton(text="🏠 Главное меню", callback_data="to_main"))
    await callback.message.edit_text("👹 <b>Выберите этап игры:</b>", reply_markup=builder.as_markup(), parse_mode="HTML")

@router.callback_query(F.data.startswith("b_l:"))
async def bosses_list(callback: types.CallbackQuery):
    stage = callback.data.split(":")[1]
    data = get_data().get(stage, {})
    builder = InlineKeyboardBuilder()
    for k, v in data.items():
        builder.row(types.InlineKeyboardButton(text=v['name'], callback_data=f"b_s:{stage}:{k}"))
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="m_bosses"))
    builder.row(types.InlineKeyboardButton(text="🏠 Главное меню", callback_data="to_main"))
    await callback.message.edit_text("🎯 <b>Выберите босса:</b>", reply_markup=builder.as_markup(), parse_mode="HTML")

@router.callback_query(F.data.startswith("b_s:"))
async def boss_selected(callback: types.CallbackQuery):
    _, stage, key = callback.data.split(":")
    boss = get_data()[stage][key]
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🛡️ Экипировка", callback_data=f"b_g:{stage}:{key}"),
                types.InlineKeyboardButton(text="🎁 Дроп", callback_data=f"b_f:{stage}:{key}:drops"))
    builder.row(types.InlineKeyboardButton(text="⚔️ Тактика", callback_data=f"b_f:{stage}:{key}:tactics"),
                types.InlineKeyboardButton(text="🏟️ Арена", callback_data=f"b_f:{stage}:{key}:arena"))
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data=f"b_l:{stage}"))
    builder.row(types.InlineKeyboardButton(text="🏠 Главное меню", callback_data="to_main"))
    await callback.message.edit_text(f"📖 <b>{boss['name']}</b>\n\n{boss['general']}", reply_markup=builder.as_markup(), parse_mode="HTML")

@router.callback_query(F.data.startswith("b_f:"))
async def boss_field(callback: types.CallbackQuery):
    _, stage, key, field = callback.data.split(":")
    boss = get_data()[stage][key]
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data=f"b_s:{stage}:{key}"))
    builder.row(types.InlineKeyboardButton(text="🏠 Главное меню", callback_data="to_main"))
    await callback.message.edit_text(f"📝 <b>Инфо:</b>\n\n{boss.get(field, '...')}", reply_markup=builder.as_markup(), parse_mode="HTML")

@router.callback_query(F.data.startswith("b_g:"))
async def boss_gear(callback: types.CallbackQuery):
    _, stage, key = callback.data.split(":")
    builder = InlineKeyboardBuilder()
    clss = {"warrior": "⚔️ Воин", "ranger": "🎯 Стрелок", "mage": "🔮 Маг", "summoner": "🐍 Призыв"}
    for cid, name in clss.items():
        builder.row(types.InlineKeyboardButton(text=name, callback_data=f"b_gc:{stage}:{key}:{cid}"))
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data=f"b_s:{stage}:{key}"))
    builder.row(types.InlineKeyboardButton(text="🏠 Главное меню", callback_data="to_main"))
    await callback.message.edit_text("🛡️ <b>Выберите ваш класс:</b>", reply_markup=builder.as_markup(), parse_mode="HTML")

@router.callback_query(F.data.startswith("b_gc:"))
async def boss_gear_list(callback: types.CallbackQuery):
    _, stage, key, cid = callback.data.split(":")
    items = get_data()[stage][key]['classes'][cid]
    builder = InlineKeyboardBuilder()
    for i, item in enumerate(items):
        builder.row(types.InlineKeyboardButton(text=item['name'], callback_data=f"b_gi:{stage}:{key}:{cid}:{i}"))
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data=f"b_g:{stage}:{key}"))
    builder.row(types.InlineKeyboardButton(text="🏠 Главное меню", callback_data="to_main"))
    await callback.message.edit_text("🎒 <b>Рекомендуемые предметы:</b>", reply_markup=builder.as_markup(), parse_mode="HTML")

@router.callback_query(F.data.startswith("b_gi:"))
async def boss_item_craft(callback: types.CallbackQuery):
    _, stage, key, cid, index = callback.data.split(":")
    item = get_data()[stage][key]['classes'][cid][int(index)]
    await callback.answer(f"🛠 Крафт: {item['craft']}", show_alert=True)
