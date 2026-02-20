import os
import json
from aiogram import Router, types, F
from aiogram.filters import Command

# Импортируем твой ID и путь к данным из файла конфигурации
from config import ADMIN_ID, DATA_PATH 

router = Router()

@router.message(F.from_user.id == ADMIN_ID, Command("stats"))
async def get_bot_stats(message: types.Message):
    users_count = 0
    users_file = os.path.join(DATA_PATH, "users.json")
    
    # Пробуем посчитать пользователей, если ты их сохраняешь в users.json
    if os.path.exists(users_file):
        try:
            with open(users_file, "r", encoding="utf-8") as f:
                users_data = json.load(f)
                users_count = len(users_data)
        except json.JSONDecodeError:
            await message.answer("⚠️ Ошибка: файл users.json поврежден!")
            return

    text = (
        "👑 <b>Панель Администратора</b>\n"
        "━━━━━━━━━━━━━━\n"
        f"👥 Зарегистрировано пользователей: <b>{users_count}</b>\n\n"
        "⚙️ <i>Системы работают в штатном режиме.</i>"
    )
    
    await message.answer(text, parse_mode="HTML")

# Заглушка, если кто-то чужой попытается ввести /stats
@router.message(Command("stats"))
async def not_admin_stats(message: types.Message):
    await message.answer("⛔️ У вас нет доступа к этой команде.")
