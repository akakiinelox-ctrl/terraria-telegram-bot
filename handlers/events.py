from aiogram import Router, types, F
from aiogram.utils.keyboard import InlineKeyboardBuilder
import json
import os

router = Router()

def get_data():
    path = "data/events.json"
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

@router.callback_query(F.data == "m_events")
async def events_main(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🟢 До-Хардмод", callback_data="ev_l:pre_hm"),
                types.InlineKeyboardButton(text="🔴 Хардмод", callback_data="ev_l:hm"))
    builder.row(types.InlineKeyboardButton(text="🏠 В меню", callback_data="to_main"))
    await callback.message.edit_text("📅 <b>Выберите этап игры для событий:</b>", reply_markup=builder.as_markup(), parse_mode="HTML")

@router.callback_query(F.data.startswith("ev_l:"))
async def events_list(callback: types.CallbackQuery):
    stage = callback.data.split(":")[1]
    data = get_data().get(stage, {})
    builder = InlineKeyboardBuilder()
    for k, v in data.items():
        builder.row(types.InlineKeyboardButton(text=v['name'], callback_data=f"ev_i:{stage}:{k}"))
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="m_events"))
    await callback.message.edit_text("🌊 <b>Доступные нашествия и события:</b>", reply_markup=builder.as_markup(), parse_mode="HTML")

@router.callback_query(F.data.startswith("ev_i:"))
async def event_info(callback: types.CallbackQuery):
    _, stage, key = callback.data.split(":")
    ev = get_data().get(stage, {}).get(key)
    if not ev: return
    
    text = (f"⚔️ <b>{ev['name']}</b>\n"
            f"━━━━━━━━━━━━━━\n"
            f"🔥 <b>Сложность:</b> {ev.get('difficulty', '???')}\n"
            f"💰 <b>Профит:</b> {ev.get('profit', '???')}\n\n"
            f"📢 <b>Как вызвать:</b> {ev['trigger']}\n"
            f"🌊 <b>Особенности:</b> {ev['waves']}\n"
            f"🎁 <b>Ценный дроп:</b> {ev['drops']}\n\n"
            f"🛠 <b>ТАКТИКА:</b>\n<i>{ev.get('arena_tip', 'Стандартная арена.')}</i>")
    
    builder = InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data=f"ev_l:{stage}"))
    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")

