from aiogram import Router, types, F
from aiogram.utils.keyboard import InlineKeyboardBuilder
import json
import os

router = Router()

def get_data():
    path = "data/classes.json"
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

@router.callback_query(F.data == "m_classes")
async def classes_main(callback: types.CallbackQuery):
    data = get_data()
    builder = InlineKeyboardBuilder()
    # Собираем список классов из ключей JSON (warrior, ranger и т.д.)
    for key, val in data.items():
        builder.row(types.InlineKeyboardButton(text=val['name'], callback_data=f"cl_s:{key}"))
    builder.row(types.InlineKeyboardButton(text="🏠 В меню", callback_data="to_main"))
    await callback.message.edit_text("🛡️ <b>Выберите ваш класс для изучения билда:</b>", reply_markup=builder.as_markup(), parse_mode="HTML")

@router.callback_query(F.data.startswith("cl_s:"))
async def class_stages(callback: types.CallbackQuery):
    cid = callback.data.split(":")[1]
    builder = InlineKeyboardBuilder()
    # Список этапов (можно сделать динамическим из JSON, если структура совпадает)
    sts = {"start": "🟢 Старт", "pre_hm": "🟡 До-ХМ", "hm_start": "🔴 Ранний ХМ", "endgame": "🟣 Финал"}
    for k, v in sts.items():
        builder.add(types.InlineKeyboardButton(text=v, callback_data=f"cl_c:{cid}:{k}"))
    builder.adjust(2).row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="m_classes"))
    await callback.message.edit_text("📅 <b>Выберите этап прохождения:</b>", reply_markup=builder.as_markup(), parse_mode="HTML")

@router.callback_query(F.data.startswith("cl_c:"))
async def class_categories(callback: types.CallbackQuery):
    _, cid, sid = callback.data.split(":")
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🛡️ Броня", callback_data=f"cl_i:{cid}:{sid}:armor"),
                types.InlineKeyboardButton(text="⚔️ Оружие", callback_data=f"cl_i:{cid}:{sid}:weapons"))
    builder.row(types.InlineKeyboardButton(text="💍 Аксессуары", callback_data=f"cl_i:{cid}:{sid}:accessories"))
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data=f"cl_s:{cid}"))
    await callback.message.edit_text("🎒 <b>Что именно вас интересует?</b>", reply_markup=builder.as_markup(), parse_mode="HTML")

@router.callback_query(F.data.startswith("cl_i:"))
async def class_items_list(callback: types.CallbackQuery):
    _, cid, sid, cat = callback.data.split(":")
    # Получаем данные из глубокой структуры JSON
    class_data = get_data().get(cid, {})
    items = class_data.get("stages", {}).get(sid, {}).get(cat, [])
    
    builder = InlineKeyboardBuilder()
    for i, itm in enumerate(items):
        builder.row(types.InlineKeyboardButton(text=itm['name'], callback_data=f"cl_inf:{cid}:{sid}:{cat}:{i}"))
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data=f"cl_c:{cid}:{sid}"))
    
    await callback.message.edit_text("📦 <b>Лучшие предметы данного типа:</b>", reply_markup=builder.as_markup(), parse_mode="HTML")

@router.callback_query(F.data.startswith("cl_inf:"))
async def class_item_alert(callback: types.CallbackQuery):
    _, cid, sid, cat, i = callback.data.split(":")
    item = get_data()[cid]['stages'][sid][cat][int(i)]
    # Выводим инфо через alert (всплывающее окно)
    await callback.answer(f"🛠 {item['name']}\n\n{item['info']}", show_alert=True)

