import random
from aiogram import Router, types, F
from aiogram.utils.keyboard import InlineKeyboardBuilder

router = Router()

CHALLENGES = {
    "class": [
        "🏹 <b>Лучник:</b> Используй только деревянные стрелы до Скелетрона.",
        "🧙 <b>Маг:</b> Носи только кактусовую броню до убийства Стены Плоти.",
        "🐍 <b>Призыватель:</b> Победи Королеву Слизней, используя только хлысты.",
        "⚔️ <b>Воин:</b> Не используй мечи со снарядами (только чистый ближний бой)."
    ],
    "goal": [
        "🏺 Найди и собери 10 разных статуй за один заход.",
        "🏰 Построй дом для NPC на парящем острове.",
        "🌋 Осуши небольшое озеро лавы в аду.",
        "🧱 Собери 999 блоков метеорита."
    ],
    "hard": [
        "💀 <b>Хардкор:</b> Победи Глаз Ктулху, не используя зелья лечения.",
        "🧨 <b>Подрывник:</b> Убивай боссов только взрывчаткой.",
        "🌑 <b>Ночной кошмар:</b> Проведи всю ночь в джунглях без факелов."
    ]
}

@router.callback_query(F.data == "m_random")
async def random_menu(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🎭 Рандомный челлендж", callback_data="rnd_get"))
    builder.row(types.InlineKeyboardButton(text="🏠 В меню", callback_data="to_main"))
    await callback.message.edit_text("🎲 <b>Генератор безумия</b>\n\nЕсли тебе скучно — я подберу испытание.", reply_markup=builder.as_markup(), parse_mode="HTML")

@router.callback_query(F.data == "rnd_get")
async def random_res(callback: types.CallbackQuery):
    cat = random.choice(list(CHALLENGES.keys()))
    task = random.choice(CHALLENGES[cat])
    
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🔄 Еще один", callback_data="rnd_get"))
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="m_random"))
    
    await callback.message.edit_text(f"🎲 <b>Твоя задача:</b>\n\n{task}", reply_markup=builder.as_markup(), parse_mode="HTML")

