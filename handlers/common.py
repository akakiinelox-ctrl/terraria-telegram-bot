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
    
    # Кнопка доната через Stars — в самом низу
    builder.row(types.InlineKeyboardButton(
        text="⭐ Поддержать Stars",
        callback_data="stars_donate"
    ))

    text = "🛠 **Terraria Tactical Assistant**\n\nВыбери раздел:"
    
    if isinstance(event, types.Message):
        await target.answer(text, reply_markup=builder.as_markup(), parse_mode="Markdown")
    else:
        await target.edit_text(text, reply_markup=builder.as_markup(), parse_mode="Markdown")
        await event.answer()


# Обработчик кнопки "Поддержать Stars" — отправка инвойса
@router.callback_query(F.data == "stars_donate")
async def stars_donate(callback: types.CallbackQuery):
    prices = [
        types.LabeledPrice(label="Маленькая поддержка", amount=50),     # ~0.75$
        types.LabeledPrice(label="Средняя поддержка", amount=100),      # ~1.5$
        types.LabeledPrice(label="Большая поддержка 🔥", amount=500),   # ~7.5$
    ]

    await callback.bot.send_invoice(
        chat_id=callback.from_user.id,
        title="Поддержать Terraria Tactical Assistant",
        description="Спасибо за донат! Это помогает быстрее добавлять новые гайды, фичи и держать бота онлайн 24/7. 💙",
        payload="donate_thanks_stars",  # Можно использовать для логирования или бонусов
        provider_token="",              # Обязательно пустая строка для Stars!
        currency="XTR",                 # Telegram Stars
        prices=prices,
        need_name=False,
        need_phone_number=False,
        need_email=False,
        need_shipping_address=False,
        is_flexible=False,
        reply_markup=None
    )
    await callback.answer("Выбери сумму в Stars ниже ↓")


# Обязательный обработчик pre_checkout_query (Telegram требует подтверждения перед оплатой)
@router.pre_checkout_query()
async def pre_checkout_handler(pre_checkout_query: types.PreCheckoutQuery):
    await pre_checkout_query.bot.answer_pre_checkout_query(
        pre_checkout_query.id,
        ok=True  # Подтверждаем, что всё ок
    )


# Обработчик успешной оплаты — благодарность пользователю
@router.message(F.successful_payment)
async def successful_payment_handler(message: types.Message):
    amount = message.successful_payment.total_amount
    thanks = (
        f"❤️ Огромное спасибо за {amount} Stars!\n\n"
        "Ты реально помогаешь боту жить и развиваться быстрее. "
        "Если хочешь — напиши, какую фичу добавить следующей (квизы, трекер прогресса, крафт-калькулятор и т.д.)!"
    )
    await message.answer(thanks)