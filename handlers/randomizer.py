import random
from aiogram import Router, types, F
from aiogram.utils.keyboard import InlineKeyboardBuilder

router = Router()

CHALLENGES = {
    "easy": [
        "🌲 Победи Глаз Ктулху, используя только метательные ножи.",
        "🏡 Построй 5 домов, используя только кактусы.",
        "⛏️ Найди 5 Кристаллов Жизни за один игровой день."
    ],
    "hard": [
        "🌋 Убей Стену Плоти, будучи одетым в броню из пчел.",
        "🌑 Проведи всю ночь в Джунглях Хардмода без факелов.",
        "🧨 Используй только взрывчатку для убийства Скелетрона."
    ],
    "insane": [
        "💀 <b>True Melee:</b> Убей Плантеру мечом без вылетающих снарядов.",
        "🧜‍♂️ Победи Герцога Рыброна до убийства Механических боссов.",
        "🧘 <b>No Hit:</b> Победи Короля Слизней, не получив ни одного удара."
    ],
    "fun": [
        "🎭 Перекрась всех NPC в разные цвета.",
        "⛳ Построй поле для гольфа через весь биом Пустыни.",
        "🐰 Собери коллекцию из 10 разных видов зайцев в сундук."
    ]
}

@router.callback_query(F.data == "m_random")
async def random_menu(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🟢 Легкие", callback_data="r_get:easy"),
                types.InlineKeyboardButton(text="🟡 Сложные", callback_data="r_get:hard"))
    builder.row(types.InlineKeyboardButton(text="🔴 БЕЗУМИЕ", callback_data="r_get:insane"),
                types.InlineKeyboardButton(text="🎈 Фан", callback_data="r_get:fun"))
    builder.row(types.InlineKeyboardButton(text="🏠 В меню", callback_data="to_main"))
    await callback.message.edit_text("🎲 <b>ГЕНЕРАТОР ИСПЫТАНИЙ</b>\n\nВыбери уровень сложности для своего следующего приключения:", reply_markup=builder.as_markup(), parse_mode="HTML")

@router.callback_query(F.data.startswith("r_get:"))
async def get_challenge(callback: types.CallbackQuery):
    diff = callback.data.split(":")[1]
    task = random.choice(CHALLENGES[diff])
    
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🔄 Другой", callback_data=f"r_get:{diff}"))
    builder.row(types.InlineKeyboardButton(text="⬅️ К сложностям", callback_data="m_random"))
    
    await callback.message.edit_text(f"🎲 <b>ТВОЯ ЗАДАЧА:</b>\n\n{task}", reply_markup=builder.as_markup(), parse_mode="HTML")

