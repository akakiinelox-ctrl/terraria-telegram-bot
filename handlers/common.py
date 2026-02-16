from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config import ADMIN_ID
import json
import os

router = Router()

def save_user(user):
    # Логика сохранения пользователя в users.json
    path = "data/users.json"
    users = {}
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            users = json.load(f)
    
    u_id = str(user.id)
    users[u_id] = {
        "username": user.username,
        "last_active": str(types.DateTime.now())
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2, ensure_ascii=False)

@router.message(Command("start"))
@router.callback_query(F.data == "to_main")
async def main_menu(event: types.Message | types.CallbackQuery):
    # Если это сообщение (команда /start)
    if isinstance(event, types.Message):
        save_user(event.from_user)
        target = event
    else: # Если это нажатие кнопки "В меню"
        target = event.message

    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="👾 Боссы", callback_data="m_bosses"),
                types.InlineKeyboardButton(text="⚔️ События", callback_data="m_events"))
    builder.row(types.InlineKeyboardButton(text="🛡️ Классы", callback_data="m_classes"),
                types.InlineKeyboardButton(text="👥 NPC", callback_data="m_npcs"))
    builder.row(types.InlineKeyboardButton(text="🧮 Калькулятор", callback_data="m_calc"),
                types.InlineKeyboardButton(text="🎣 Рыбалка", callback_data="m_fishing"))
    builder.row(types.InlineKeyboardButton(text="🧪 Алхимия", callback_data="m_alchemy"),
                types.InlineKeyboardButton(text="📋 Чек-лист", callback_data="m_checklist"))
    builder.row(types.InlineKeyboardButton(text="🎲 Мне скучно", callback_data="m_random"))
    
    text = "🛠 **Terraria Tactical Assistant**\n\nПривет, Террариец! Я твой личный гид. Выбери раздел для изучения:"
    
    if isinstance(event, types.Message):
        await target.answer(text, reply_markup=builder.as_markup(), parse_mode="Markdown")
    else:
        await target.edit_text(text, reply_markup=builder.as_markup(), parse_mode="Markdown")

