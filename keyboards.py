from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Главное меню
main_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🟢 Дохардмод", callback_data="stage_prehard")],
    [InlineKeyboardButton(text="🔥 Хардмод", callback_data="stage_hard")],
    [InlineKeyboardButton(text="📚 Общие гайды", callback_data="guides")]
])

# Дохардмод — боссы
prehard_bosses = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="👁 Глаз Ктулху", callback_data="boss_eye")],
    [InlineKeyboardButton(text="🐝 Королева пчёл", callback_data="boss_bee")],
    [InlineKeyboardButton(text="💀 Скелетрон", callback_data="boss_skeletron")],
    [InlineKeyboardButton(text="🧱 Стена плоти", callback_data="boss_wall")],
    [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_main")]
])
