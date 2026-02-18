from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext

router = Router()

@router.message(Command("start"))
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

    text = "🛠 **Terraria Tactical Assistant**\n\nВыбери раздел:"
    
    if isinstance(event, types.Message):
        await target.answer(text, reply_markup=builder.as_markup(), parse_mode="Markdown")
    else:
        await target.edit_text(text, reply_markup=builder.as_markup(), parse_mode="Markdown")
        await event.answer()
