from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from config import ADMIN_ID
import json
import os
from datetime import datetime

router = Router()

def save_user(user):
    # Логика сохранения пользователя в users.json
    path = "data/users.json"
    if not os.path.exists("data"):
        os.makedirs("data")
        
    users = {}
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            try:
                users = json.load(f)
            except:
                users = {}
    
    u_id = str(user.id)
    users[u_id] = {
        "username": user.username,
        "last_active": str(datetime.now())
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2, ensure_ascii=False)

@router.message(Command("start"))
@router.callback_query(F.data == "to_main")
async def main_menu(event: types.Message | types.CallbackQuery, state: FSMContext):
    # Сбрасываем любые активные состояния (FSM), чтобы поиск или ввод не зависали
    await state.clear()

    # Определяем, куда отправлять ответ
    if isinstance(event, types.Message):
        save_user(event.from_user)
        is_callback = False
    else:
        is_callback = True

    builder = InlineKeyboardBuilder()
    # Собираем меню (callback_data должны совпадать с именами в bot.py)
    builder.row(types.InlineKeyboardButton(text="👾 Боссы", callback_data="m_bosses"),
                types.InlineKeyboardButton(text="⚔️ События", callback_data="m_events"))
    
    builder.row(types.InlineKeyboardButton(text="🛡️ Классы", callback_data="m_classes"),
                types.InlineKeyboardButton(text="👥 NPC", callback_data="m_npc"))
    
    builder.row(types.InlineKeyboardButton(text="🧮 Калькулятор", callback_data="m_calc"),
                types.InlineKeyboardButton(text="🎣 Рыбалка", callback_data="m_fishing"))
    
    builder.row(types.InlineKeyboardButton(text="🧪 Алхимия", callback_data="m_alchemy"),
                types.InlineKeyboardButton(text="📋 Чек-лист", callback_data="m_checklist"))
    
    builder.row(types.InlineKeyboardButton(text="🎲 Мне скучно", callback_data="m_random"))
    
    builder.row(types.InlineKeyboardButton(text="🌍 Сиды", callback_data="m_seeds"))
    
    builder.row(types.InlineKeyboardButton(text="🔍 Поиск по Вики", callback_data="m_wiki"))

    text = "🛠 **Terraria Tactical Assistant**\n\nПривет, Террариец! Я твой личный гид. Выбери раздел для изучения:"
    
    if not is_callback:
        # Ответ на команду /start
        await event.answer(text, reply_markup=builder.as_markup(), parse_mode="Markdown")
    else:
        # Ответ на кнопку "В меню" (редактируем старое сообщение)
        try:
            await event.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="Markdown")
        except Exception:
            # Если сообщение нельзя отредактировать (например, оно слишком старое), шлем новое
            await event.message.answer(text, reply_markup=builder.as_markup(), parse_mode="Markdown")
        # Закрываем "часики" на кнопке
        await event.answer()
