from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.utils.keyboard import InlineKeyboardBuilder

router = Router()

class WikiStates(StatesGroup):
    waiting_for_query = State()

@router.callback_query(F.data == "m_wiki")
@router.callback_query(F.data == "wiki_retry") # Добавляем обработку повтора
async def wiki_start(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(WikiStates.waiting_for_query)
    # Используем edit_text, чтобы меню не дублировалось, если нажали "Искать снова"
    await callback.message.edit_text(
        "🔍 <b>База Знаний Terraria</b>\n\nВведите название предмета, босса или события:",
        parse_mode="HTML"
    )

@router.message(WikiStates.waiting_for_query)
async def wiki_link_generator(message: types.Message, state: FSMContext):
    query = message.text.strip()
    
    # Форматируем название для ссылки (первая буква заглавная, пробелы через _)
    formatted_query = query.capitalize().replace(" ", "_")
    wiki_url = f"https://terraria.wiki.gg/ru/wiki/{formatted_query}"
    
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🌐 Открыть страницу", url=wiki_url))
    # Новая кнопка перезапуска поиска
    builder.row(types.InlineKeyboardButton(text="🔄 Искать снова", callback_data="wiki_retry"))
    builder.row(types.InlineKeyboardButton(text="🏠 Главное меню", callback_data="to_main"))
    
    await message.answer(
        f"📖 <b>Результат для: {query}</b>\n\nНажмите на кнопку ниже, чтобы перейти к статье.",
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    
    # Мы очищаем состояние, чтобы бот не реагировал на каждое сообщение в чате,
    # но кнопка "wiki_retry" вернет пользователя в режим поиска.
    await state.clear()
