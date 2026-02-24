import os
import json
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext

router = Router()

# Путь к папке с данными
DATA_PATH = "data/"

@router.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    # --- Блок сохранения пользователя ---
    user_id = str(message.from_user.id)
    users_file = os.path.join(DATA_PATH, "users.json")
    
    # Создаем папку data, если её вдруг нет
    if not os.path.exists(DATA_PATH):
        os.makedirs(DATA_PATH)

    # Читаем существующий файл или создаем пустой словарь
    try:
        with open(users_file, "r", encoding="utf-8") as f:
            users_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        users_data = {}

    # Если пользователя еще нет в базе — добавляем его
    if user_id not in users_data:
        users_data[user_id] = {
            "username": message.from_user.username,
            "first_name": message.from_user.first_name
        }
        # Перезаписываем файл с новым пользователем
        with open(users_file, "w", encoding="utf-8") as f:
            json.dump(users_data, f, ensure_ascii=False, indent=4)
            
    # Вызываем Главное меню после старта
    await main_menu(message, state)


@router.callback_query(F.data == "to_main")
async def main_menu(event: types.Message | types.CallbackQuery, state: FSMContext):
    await state.clear()
    
    # Определяем, отвечаем мы на сообщение или на кнопку
    target = event if isinstance(event, types.Message) else event.message

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
    builder.row(types.InlineKeyboardButton(text="🌍 Сиды", callback_data="m_seeds"))
    builder.row(types.InlineKeyboardButton(text="🔍 Поиск по Вики", callback_data="m_wiki"))
    
    # Кнопка поддержки (донат) — в самом низу
    builder.row(types.InlineKeyboardButton(
        text="❤️ Поддержать бота",
        callback_data="donate_menu"
    ))

    text = "🛠 **Terraria Tactical Assistant**\n\nВыбери раздел:"
    
    if isinstance(event, types.Message):
        await target.answer(text, reply_markup=builder.as_markup(), parse_mode="Markdown")
    else:
        await target.edit_text(text, reply_markup=builder.as_markup(), parse_mode="Markdown")
        await event.answer()


@router.callback_query(F.data == "donate_menu")
async def donate_menu(callback: types.CallbackQuery):
    text = (
        "❤️ <b>Поддержать развитие бота</b>\n\n"
        "Terraria Tactical Assistant создаётся для всех фанатов Terraria бесплатно, "
        "но поддержка позволяет быстрее добавлять новые фичи, улучшать гайды и держать бота онлайн 24/7.\n\n"
        "Спасибо огромное каждому, кто помогает! 💙\n\n"
        "💳 Способы поддержать:\n"
        "• <a href='https://www.donationalerts.com/r/твоя_ссылка'>DonationAlerts</a> (карты, крипта, QIWI и др.)\n"
        "• <a href='https://boosty.to/твоя_ссылка'>Boosty</a> (подписка от 100 ₽/мес с эксклюзивом)\n"
        "• Перевод на карту: 4444 1111 2222 3333 (укажи в комментарии @твой_ник)\n\n"
        "Любая сумма — это уже огромная мотивация продолжать развивать бота!"
    )

    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="to_main"))

    await callback.message.edit_text(
        text,
        reply_markup=builder.as_markup(),
        parse_mode="HTML",
        disable_web_page_preview=True
    )
    await callback.answer()