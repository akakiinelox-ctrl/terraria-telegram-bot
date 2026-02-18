import os
import json
from aiogram import Router, types, F
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.types import InputMediaPhoto

router = Router()

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---

def get_data():
    """Читает JSON с боссами"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(current_dir)
    path = os.path.join(base_dir, "data", "bosses.json")
    
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def get_boss_by_id(boss_id):
    """Ищет босса в Pre-HM или HM"""
    data = get_data()
    if boss_id in data.get("pre_hm", {}):
        return data["pre_hm"][boss_id]
    if boss_id in data.get("hm", {}):
        return data["hm"][boss_id]
    return None

# --- ГЛАВНОЕ МЕНЮ БОССОВ ---

@router.callback_query(F.data == "m_bosses")
async def bosses_main_menu(callback: types.CallbackQuery):
    # Если мы вернулись из меню с картинкой, удаляем её и шлем текст
    if callback.message.photo:
        await callback.message.delete()
        func_reply = callback.message.answer
    else:
        func_reply = callback.message.edit_text

    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🟢 До Хардмода", callback_data="b_mode:pre_hm"))
    builder.row(types.InlineKeyboardButton(text="🔴 Хардмод", callback_data="b_mode:hm"))
    builder.row(types.InlineKeyboardButton(text="🏠 Главное меню", callback_data="to_main"))
    
    await func_reply(
        "👾 <b>Бестиарий Террарии</b>\n\nВыберите этап игры, чтобы увидеть список боссов:",
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )

# --- СПИСОК БОССОВ (PRE-HM / HM) ---

@router.callback_query(F.data.startswith("b_mode:"))
async def boss_list(callback: types.CallbackQuery):
    mode = callback.data.split(":")[1]
    data = get_data().get(mode, {})
    
    # Если возвращаемся от картинки к списку -> удаляем картинку, шлем текст
    if callback.message.photo:
        await callback.message.delete()
        func_reply = callback.message.answer
    else:
        func_reply = callback.message.edit_text

    builder = InlineKeyboardBuilder()
    
    # Генерируем кнопки для каждого босса
    for key, val in data.items():
        builder.row(types.InlineKeyboardButton(text=val['name'], callback_data=f"b_open:{key}"))
        
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="m_bosses"))
    builder.row(types.InlineKeyboardButton(text="🏠 Домой", callback_data="to_main"))
    
    title = "🟢 <b>Боссы До-Хардмода</b>" if mode == "pre_hm" else "🔴 <b>Боссы Хардмода</b>"
    await func_reply(f"{title}\nВыберите врага:", reply_markup=builder.as_markup(), parse_mode="HTML")

# --- КАРТОЧКА БОССА (С КАРТИНКОЙ) ---

@router.callback_query(F.data.startswith("b_open:"))
async def boss_view(callback: types.CallbackQuery):
    boss_id = callback.data.split(":")[1]
    boss = get_boss_by_id(boss_id)
    
    if not boss:
        await callback.answer("Ошибка: Босс не найден!")
        return

    # Клавиатура управления
    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(text="⚔️ Тактика", callback_data=f"b_tab:tactics:{boss_id}"),
        types.InlineKeyboardButton(text="🏟 Арена", callback_data=f"b_tab:arena:{boss_id}")
    )
    builder.row(
        types.InlineKeyboardButton(text="💎 Дроп", callback_data=f"b_tab:drops:{boss_id}"),
        types.InlineKeyboardButton(text="🛡 Экипировка", callback_data=f"b_class_sel:{boss_id}")
    )
    
    # Определяем, куда вернуться (HM или Pre-HM)
    data = get_data()
    parent_mode = "pre_hm" if boss_id in data.get("pre_hm", {}) else "hm"
    builder.row(types.InlineKeyboardButton(text="⬅️ К списку", callback_data=f"b_mode:{parent_mode}"))

    text = f"<b>{boss['name']}</b>\n━━━━━━━━━━━━━━\n{boss['general']}"
    img_id = boss.get("arena_img", "")

    # ЛОГИКА ОТПРАВКИ:
    # 1. Если есть картинка -> Удаляем старое (текст), шлем фото.
    # 2. Если картинки нет -> Просто редактируем текст.
    
    try:
        if img_id:
            await callback.message.delete() # Удаляем старое меню
            await callback.message.answer_photo(
                photo=img_id,
                caption=text,
                reply_markup=builder.as_markup(),
                parse_mode="HTML"
            )
        else:
            # Если картинки нет, работаем как раньше
            if callback.message.photo:
                await callback.message.delete()
                await callback.message.answer(text, reply_markup=builder.as_markup(), parse_mode="HTML")
            else:
                await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")
    except Exception as e:
        # Если картинка битая (неверный ID), шлем без неё
        await callback.message.answer(f"⚠️ Ошибка фото. \n\n{text}", reply_markup=builder.as_markup(), parse_mode="HTML")

# --- ПЕРЕКЛЮЧЕНИЕ ВКЛАДОК (ТАКТИКА / АРЕНА / ДРОП) ---

@router.callback_query(F.data.startswith("b_tab:"))
async def boss_tab(callback: types.CallbackQuery):
    _, tab, boss_id = callback.data.split(":")
    boss = get_boss_by_id(boss_id)
    
    # Заголовки для вкладок
    headers = {
        "tactics": "⚔️ <b>Тактика победы:</b>",
        "arena": "🏟 <b>Подготовка арены:</b>",
        "drops": "💎 <b>Ценный дроп:</b>"
    }
    
    content = boss.get(tab, "Информация отсутствует.")
    text = f"<b>{boss['name']}</b>\n━━━━━━━━━━━━━━\n{headers[tab]}\n\n{content}"

    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(text="📜 Инфо", callback_data=f"b_tab:general:{boss_id}") if tab != "general" else types.InlineKeyboardButton(text="⏺ Инфо", callback_data="ignore"),
        types.InlineKeyboardButton(text="⚔️ Тактика", callback_data=f"b_tab:tactics:{boss_id}") if tab != "tactics" else types.InlineKeyboardButton(text="⏺ Тактика", callback_data="ignore")
    )
    builder.row(
        types.InlineKeyboardButton(text="🏟 Арена", callback_data=f"b_tab:arena:{boss_id}") if tab != "arena" else types.InlineKeyboardButton(text="⏺ Арена", callback_data="ignore"),
        types.InlineKeyboardButton(text="💎 Дроп", callback_data=f"b_tab:drops:{boss_id}") if tab != "drops" else types.InlineKeyboardButton(text="⏺ Дроп", callback_data="ignore")
    )
    builder.row(types.InlineKeyboardButton(text="🛡 Экипировка", callback_data=f"b_class_sel:{boss_id}"))
    
    # Кнопка назад
    data = get_data()
    parent_mode = "pre_hm" if boss_id in data.get("pre_hm", {}) else "hm"
    builder.row(types.InlineKeyboardButton(text="⬅️ К списку", callback_data=f"b_mode:{parent_mode}"))

    # Если мы уже в режиме "General" (вернулись с вкладки)
    if tab == "general":
        text = f"<b>{boss['name']}</b>\n━━━━━━━━━━━━━━\n{boss['general']}"

    # Редактируем подпись (caption), если это фото, или текст, если это текст
    if callback.message.photo:
        if tab == "general":
             await callback.message.edit_caption(caption=text, reply_markup=builder.as_markup(), parse_mode="HTML")
        else:
             await callback.message.edit_caption(caption=text, reply_markup=builder.as_markup(), parse_mode="HTML")
    else:
        await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")

# --- ВЫБОР КЛАССА ДЛЯ ЭКИПИРОВКИ ---

@router.callback_query(F.data.startswith("b_class_sel:"))
async def boss_class_select(callback: types.CallbackQuery):
    boss_id = callback.data.split(":")[1]
    
    # Если мы на фото, удаляем его, чтобы показать меню классов (текстовое)
    if callback.message.photo:
        await callback.message.delete()
        func_reply = callback.message.answer
    else:
        func_reply = callback.message.edit_text

    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="⚔️ Воин", callback_data=f"b_cls:warrior:{boss_id}"),
                types.InlineKeyboardButton(text="🏹 Стрелок", callback_data=f"b_cls:ranger:{boss_id}"))
    builder.row(types.InlineKeyboardButton(text="🧙‍♂️ Маг", callback_data=f"b_cls:mage:{boss_id}"),
                types.InlineKeyboardButton(text="🐲 Призыватель", callback_data=f"b_cls:summoner:{boss_id}"))
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад к боссу", callback_data=f"b_open:{boss_id}"))

    await func_reply("🛡 <b>Выбор класса:</b>\n\nКакую экипировку будем собирать?", reply_markup=builder.as_markup(), parse_mode="HTML")

# --- ПОКАЗ ПРЕДМЕТОВ КЛАССА ---

@router.callback_query(F.data.startswith("b_cls:"))
async def boss_class_items(callback: types.CallbackQuery):
    _, role, boss_id = callback.data.split(":")
    boss = get_boss_by_id(boss_id)
    items = boss["classes"].get(role, [])

    builder = InlineKeyboardBuilder()
    for item in items:
        # Сохраняем имя предмета в callback, чтобы показать рецепт
        # Обрезаем имя, если длинное, чтобы влезло в лимит
        short_name = item['name'][:20]
        # Используем индекс, чтобы достать точный крафт
        idx = items.index(item)
        builder.row(types.InlineKeyboardButton(text=item['name'], callback_data=f"b_cr:{boss_id}:{role}:{idx}"))
    
    builder.row(types.InlineKeyboardButton(text="⬅️ Другой класс", callback_data=f"b_class_sel:{boss_id}"))
    builder.row(types.InlineKeyboardButton(text="🏠 К боссу", callback_data=f"b_open:{boss_id}"))

    roles_ru = {"warrior": "Воина", "ranger": "Стрелка", "mage": "Мага", "summoner": "Призывателя"}
    await callback.message.edit_text(f"🎒 <b>Экипировка {roles_ru.get(role)}:</b>\n\nНажми на предмет, чтобы увидеть крафт.", reply_markup=builder.as_markup(), parse_mode="HTML")

# --- ПОКАЗ КРАФТА (Alert) ---

@router.callback_query(F.data.startswith("b_cr:"))
async def boss_item_craft(callback: types.CallbackQuery):
    _, boss_id, role, idx_str = callback.data.split(":")
    idx = int(idx_str)
    
    boss = get_boss_by_id(boss_id)
    item = boss["classes"][role][idx]
    
    # Показываем всплывающее окно (alert)
    await callback.answer(f"{item['name']}\n\n{item['craft']}", show_alert=True)
