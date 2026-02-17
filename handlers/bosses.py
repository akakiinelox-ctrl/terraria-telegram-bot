from aiogram import Router, types, F
from aiogram.utils.keyboard import InlineKeyboardBuilder
import json
import os

router = Router()

def get_data():
    # Путь к файлу. Если запускаешь локально, убедись, что папка data рядом с bot.py
    path = "data/bosses.json"
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    print(f"❌ Ошибка: Файл {path} не найден!")
    return {}

# ГЛАВНОЕ МЕНЮ БОССОВ
@router.callback_query(F.data == "m_bosses")
async def bosses_main(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🟢 До-Хардмод", callback_data="b_l:pre_hm"),
                types.InlineKeyboardButton(text="🔴 Хардмод", callback_data="b_l:hm"))
    builder.row(types.InlineKeyboardButton(text="🏠 Главное меню", callback_data="to_main"))
    await callback.message.edit_text("👹 <b>Выберите этап игры:</b>", reply_markup=builder.as_markup(), parse_mode="HTML")

# СПИСОК БОССОВ
@router.callback_query(F.data.startswith("b_l:"))
async def bosses_list(callback: types.CallbackQuery):
    stage = callback.data.split(":")[1]
    data = get_data().get(stage, {})
    
    if not data:
        await callback.answer("Ошибка: данные не найдены", show_alert=True)
        return

    builder = InlineKeyboardBuilder()
    for k, v in data.items():
        builder.row(types.InlineKeyboardButton(text=v['name'], callback_data=f"b_s:{stage}:{k}"))
    
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="m_bosses"))
    builder.row(types.InlineKeyboardButton(text="🏠 Главное меню", callback_data="to_main"))
    await callback.message.edit_text("🎯 <b>Выберите босса:</b>", reply_markup=builder.as_markup(), parse_mode="HTML")

# ВЫБРАННЫЙ БОСС
@router.callback_query(F.data.startswith("b_s:"))
async def boss_selected(callback: types.CallbackQuery):
    try:
        _, stage, key = callback.data.split(":")
        boss = get_data()[stage][key]
    except KeyError:
        await callback.answer("Ошибка данных босса", show_alert=True)
        return

    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🛡️ Экипировка", callback_data=f"b_g:{stage}:{key}"),
                types.InlineKeyboardButton(text="🎁 Дроп", callback_data=f"b_f:{stage}:{key}:drops"))
    builder.row(types.InlineKeyboardButton(text="⚔️ Тактика", callback_data=f"b_f:{stage}:{key}:tactics"),
                types.InlineKeyboardButton(text="🏟️ Арена", callback_data=f"b_f:{stage}:{key}:arena"))
    builder.row(types.InlineKeyboardButton(text="⬅️ К списку", callback_data=f"b_l:{stage}"))
    builder.row(types.InlineKeyboardButton(text="🏠 Главное меню", callback_data="to_main"))
    
    await callback.message.edit_text(f"📖 <b>{boss['name']}</b>\n\n{boss.get('general', 'Описание отсутствует')}", reply_markup=builder.as_markup(), parse_mode="HTML")

# ИНФО О БОССЕ (ДРОП, ТАКТИКА)
@router.callback_query(F.data.startswith("b_f:"))
async def boss_field(callback: types.CallbackQuery):
    _, stage, key, field = callback.data.split(":")
    boss = get_data()[stage][key]
    text = boss.get(field, "Нет данных.")
    
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data=f"b_s:{stage}:{key}"))
    builder.row(types.InlineKeyboardButton(text="📜 Список боссов", callback_data=f"b_l:{stage}"))
    builder.row(types.InlineKeyboardButton(text="🏠 Главное меню", callback_data="to_main"))
    await callback.message.edit_text(f"📝 <b>Инфо:</b>\n\n{text}", reply_markup=builder.as_markup(), parse_mode="HTML")

# ВЫБОР КЛАССА
@router.callback_query(F.data.startswith("b_g:"))
async def boss_gear(callback: types.CallbackQuery):
    _, stage, key = callback.data.split(":")
    builder = InlineKeyboardBuilder()
    clss = {"warrior": "⚔️ Воин", "ranger": "🎯 Стрелок", "mage": "🔮 Маг", "summoner": "🐍 Призыв"}
    for cid, name in clss.items():
        builder.row(types.InlineKeyboardButton(text=name, callback_data=f"b_gc:{stage}:{key}:{cid}"))
    
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data=f"b_s:{stage}:{key}"))
    # -- ДОБАВЛЕНЫ КНОПКИ НИЖЕ --
    builder.row(types.InlineKeyboardButton(text="📜 Список боссов", callback_data=f"b_l:{stage}"),
                types.InlineKeyboardButton(text="🏠 Главное меню", callback_data="to_main"))
    
    await callback.message.edit_text("🛡️ <b>Выберите ваш класс:</b>", reply_markup=builder.as_markup(), parse_mode="HTML")

# СПИСОК ПРЕДМЕТОВ
@router.callback_query(F.data.startswith("b_gc:"))
async def boss_gear_list(callback: types.CallbackQuery):
    _, stage, key, cid = callback.data.split(":")
    items = get_data()[stage][key].get('classes', {}).get(cid, [])
    
    builder = InlineKeyboardBuilder()
    for i, item in enumerate(items):
        builder.row(types.InlineKeyboardButton(text=item['name'], callback_data=f"b_gi:{stage}:{key}:{cid}:{i}"))
    
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data=f"b_g:{stage}:{key}"))
    # -- ДОБАВЛЕНА КНОПКА НИЖЕ --
    builder.row(types.InlineKeyboardButton(text="🏠 Главное меню", callback_data="to_main"))
    
    await callback.message.edit_text("🎒 <b>Рекомендуемые предметы:</b>\n<i>(Нажми на предмет, чтобы увидеть крафт)</i>", reply_markup=builder.as_markup(), parse_mode="HTML")

# ПОКАЗ КРАФТА
@router.callback_query(F.data.startswith("b_gi:"))
async def boss_item_craft(callback: types.CallbackQuery):
    _, stage, key, cid, index = callback.data.split(":")
    items = get_data()[stage][key]['classes'][cid]
    item = items[int(index)]
    await callback.answer(f"🛠 Крафт: {item.get('craft', 'Нет данных')}", show_alert=True)
