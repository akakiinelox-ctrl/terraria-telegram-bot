from aiogram import Router, types, F
from aiogram.utils.keyboard import InlineKeyboardBuilder
import json
import os

router = Router()

def get_data():
    # Используем абсолютный путь для надежности
    path = "data/bosses.json"
    
    if not os.path.exists(path):
        print(f"❌ ОШИБКА: Файл {path} не найден! Проверь папку data.")
        return {}
        
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            # print("✅ JSON с боссами загружен успешно") # Раскомментируй для отладки
            return data
    except Exception as e:
        print(f"❌ ОШИБКА ЧТЕНИЯ JSON: {e}")
        return {}

# --- 1. ГЛАВНОЕ МЕНЮ РАЗДЕЛА ---
@router.callback_query(F.data == "m_bosses")
async def bosses_main(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    # Добавляем кнопки проще - через builder.button
    builder.button(text="🟢 До-Хардмод", callback_data="b_l:pre_hm")
    builder.button(text="🔴 Хардмод", callback_data="b_l:hm")
    builder.button(text="🏠 Главное меню", callback_data="to_main")
    
    # Делаем сетку: 2 кнопки в ряду, потом 1 (Домой)
    builder.adjust(2, 1)
    
    await callback.message.edit_text(
        "👹 <b>Выберите этап игры:</b>", 
        reply_markup=builder.as_markup(), 
        parse_mode="HTML"
    )

# --- 2. СПИСОК БОССОВ ---
@router.callback_query(F.data.startswith("b_l:"))
async def bosses_list(callback: types.CallbackQuery):
    stage = callback.data.split(":")[1]
    data = get_data().get(stage, {})
    
    if not data:
        # Если JSON пустой или не прочитался
        await callback.answer("⚠️ Ошибка: Список боссов пуст! Проверь JSON.", show_alert=True)
        return

    builder = InlineKeyboardBuilder()
    
    # Генерация кнопок боссов
    for key, val in data.items():
        builder.button(text=val['name'], callback_data=f"b_s:{stage}:{key}")
    
    # Навигация
    builder.button(text="⬅️ Назад", callback_data="m_bosses")
    builder.button(text="🏠 Домой", callback_data="to_main")
    
    # Сетка: по 2 босса в ряд, кнопки навигации внизу
    builder.adjust(2) 
    
    await callback.message.edit_text(
        "🎯 <b>Выберите босса:</b>", 
        reply_markup=builder.as_markup(), 
        parse_mode="HTML"
    )

# --- 3. ВЫБРАННЫЙ БОСС ---
@router.callback_query(F.data.startswith("b_s:"))
async def boss_selected(callback: types.CallbackQuery):
    _, stage, key = callback.data.split(":")
    # Безопасное получение данных
    boss_data = get_data().get(stage, {}).get(key)
    
    if not boss_data:
        await callback.answer("Ошибка: данные босса не найдены", show_alert=True)
        return

    builder = InlineKeyboardBuilder()
    builder.button(text="🛡️ Экипировка", callback_data=f"b_g:{stage}:{key}")
    builder.button(text="🎁 Дроп", callback_data=f"b_f:{stage}:{key}:drops")
    builder.button(text="⚔️ Тактика", callback_data=f"b_f:{stage}:{key}:tactics")
    builder.button(text="🏟️ Арена", callback_data=f"b_f:{stage}:{key}:arena")
    
    # Навигация
    builder.button(text="⬅️ Назад", callback_data=f"b_l:{stage}")
    builder.button(text="🏠 Домой", callback_data="to_main")
    
    # Сетка: 2x2 для меню босса, потом навигация
    builder.adjust(2, 2, 2)
    
    await callback.message.edit_text(
        f"📖 <b>{boss_data['name']}</b>\n\n{boss_data.get('general', 'Описание отсутствует.')}", 
        reply_markup=builder.as_markup(), 
        parse_mode="HTML"
    )

# --- 4. ИНФО О БОССЕ ---
@router.callback_query(F.data.startswith("b_f:"))
async def boss_field(callback: types.CallbackQuery):
    _, stage, key, field = callback.data.split(":")
    boss_data = get_data().get(stage, {}).get(key, {})
    
    text = boss_data.get(field, "Данных нет.")
    
    builder = InlineKeyboardBuilder()
    builder.button(text="⬅️ К боссу", callback_data=f"b_s:{stage}:{key}")
    builder.button(text="📜 Список", callback_data=f"b_l:{stage}")
    builder.button(text="🏠 Домой", callback_data="to_main")
    builder.adjust(1, 2)
    
    await callback.message.edit_text(
        f"📝 <b>Информация:</b>\n\n{text}", 
        reply_markup=builder.as_markup(), 
        parse_mode="HTML"
    )

# --- 5. ВЫБОР КЛАССА ---
@router.callback_query(F.data.startswith("b_g:"))
async def boss_gear(callback: types.CallbackQuery):
    _, stage, key = callback.data.split(":")
    
    builder = InlineKeyboardBuilder()
    # Хардкодим классы, так как они всегда одинаковые
    classes = [
        ("⚔️ Воин", "warrior"), ("🎯 Стрелок", "ranger"),
        ("🔮 Маг", "mage"), ("🐍 Призыв", "summoner")
    ]
    
    for label, code in classes:
        builder.button(text=label, callback_data=f"b_gc:{stage}:{key}:{code}")
        
    builder.button(text="⬅️ К боссу", callback_data=f"b_s:{stage}:{key}")
    builder.button(text="🏠 Домой", callback_data="to_main")
    
    builder.adjust(2, 2, 2)
    
    await callback.message.edit_text(
        "🛡️ <b>Выберите ваш класс:</b>", 
        reply_markup=builder.as_markup(), 
        parse_mode="HTML"
    )

# --- 6. СПИСОК ПРЕДМЕТОВ ---
@router.callback_query(F.data.startswith("b_gc:"))
async def boss_gear_list(callback: types.CallbackQuery):
    try:
        _, stage, key, cid = callback.data.split(":")
        items = get_data()[stage][key]['classes'][cid]
    except (KeyError, IndexError):
        await callback.answer("Ошибка: нет предметов для этого класса", show_alert=True)
        return

    builder = InlineKeyboardBuilder()
    for i, item in enumerate(items):
        # Передаем индекс предмета
        builder.button(text=item['name'], callback_data=f"b_gi:{stage}:{key}:{cid}:{i}")
        
    builder.button(text="⬅️ Назад", callback_data=f"b_g:{stage}:{key}")
    builder.button(text="🏠 Домой", callback_data="to_main")
    builder.adjust(1) # Все предметы в столбик
    
    await callback.message.edit_text(
        "🎒 <b>Рекомендуемые предметы:</b>\n<i>(Нажми, чтобы увидеть крафт)</i>", 
        reply_markup=builder.as_markup(), 
        parse_mode="HTML"
    )

# --- 7. ПОКАЗ КРАФТА (Alert) ---
@router.callback_query(F.data.startswith("b_gi:"))
async def boss_item_craft(callback: types.CallbackQuery):
    _, stage, key, cid, index = callback.data.split(":")
    items = get_data()[stage][key]['classes'][cid]
    item_data = items[int(index)]
    
    await callback.answer(
        f"🛠 {item_data['name']}\n\n{item_data.get('craft', 'Крафт не указан')}", 
        show_alert=True
    )
