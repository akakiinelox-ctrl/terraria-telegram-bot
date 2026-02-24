import os
import json
import asyncio
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import ADMIN_ID, DATA_PATH

router = Router()

# Состояния для рассылки
class BroadcastStates(StatesGroup):
    waiting_content = State()
    waiting_confirm = State()

@router.message(F.from_user.id == ADMIN_ID, Command("stats"))
async def get_bot_stats(message: types.Message):
    users_count = 0
    users_file = os.path.join(DATA_PATH, "users.json")
    
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
        "Команды админа:\n"
        "• /broadcast — начать рассылку\n"
        "• /stats — статистика бота"
    )
    
    await message.answer(text, parse_mode="HTML")

@router.message(F.from_user.id == ADMIN_ID, Command("broadcast"))
async def start_broadcast(message: types.Message, state: FSMContext):
    await message.answer(
        "📢 <b>Новая рассылка</b>\n\n"
        "Отправь сообщение, которое хочешь разослать всем пользователям.\n"
        "Поддерживается: текст + фото + видео + подпись.\n\n"
        "Для отмены — /cancel"
    )
    await state.set_state(BroadcastStates.waiting_content)

@router.message(F.from_user.id == ADMIN_ID, Command("cancel"))
async def cancel_broadcast(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Рассылка отменена.")

@router.message(F.from_user.id == ADMIN_ID, BroadcastStates.waiting_content)
async def receive_broadcast_content(message: types.Message, state: FSMContext):
    # Сохраняем контент в состоянии
    content = {
        "text": message.text or message.caption,
        "photo": message.photo[-1].file_id if message.photo else None,
        "video": message.video.file_id if message.video else None,
        "type": "photo" if message.photo else "video" if message.video else "text"
    }
    
    await state.update_data(broadcast_content=content)
    
    preview_text = "📢 <b>Предпросмотр рассылки:</b>\n\n"
    if content["text"]:
        preview_text += content["text"] + "\n\n"
    preview_text += f"Тип: {content['type']}\n"
    preview_text += "Отправить всем пользователям?"
    
    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(text="✅ Отправить", callback_data="broadcast_confirm"),
        types.InlineKeyboardButton(text="❌ Отмена", callback_data="broadcast_cancel")
    )
    
    if content["photo"]:
        await message.answer_photo(
            photo=content["photo"],
            caption=preview_text,
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
    elif content["video"]:
        await message.answer_video(
            video=content["video"],
            caption=preview_text,
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
    else:
        await message.answer(preview_text, reply_markup=builder.as_markup(), parse_mode="HTML")
    
    await state.set_state(BroadcastStates.waiting_confirm)

@router.callback_query(F.from_user.id == ADMIN_ID, F.data == "broadcast_confirm")
async def confirm_broadcast(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    content = data.get("broadcast_content")
    
    if not content:
        await callback.message.edit_text("Ошибка: контент не найден.")
        await state.clear()
        return
    
    users_file = os.path.join(DATA_PATH, "users.json")
    if not os.path.exists(users_file):
        await callback.message.edit_text("Нет файла users.json")
        return
    
    with open(users_file, "r", encoding="utf-8") as f:
        users = json.load(f)
    
    success = 0
    failed = 0
    
    await callback.message.edit_text("🚀 Рассылка запущена... (это может занять время)")
    
    for user_id in users.keys():
        try:
            if content["type"] == "photo":
                await callback.bot.send_photo(
                    chat_id=user_id,
                    photo=content["photo"],
                    caption=content["text"],
                    parse_mode="HTML"
                )
            elif content["type"] == "video":
                await callback.bot.send_video(
                    chat_id=user_id,
                    video=content["video"],
                    caption=content["text"],
                    parse_mode="HTML"
                )
            else:
                await callback.bot.send_message(
                    chat_id=user_id,
                    text=content["text"],
                    parse_mode="HTML"
                )
            success += 1
        except Exception as e:
            failed += 1
            print(f"Не удалось отправить пользователю {user_id}: {e}")
        
        await asyncio.sleep(0.05)  # Чтобы не словить флуд-лимит
    
    result = (
        f"✅ <b>Рассылка завершена</b>\n\n"
        f"Успешно: {success}\n"
        f"Не удалось: {failed}\n"
        f"Всего пользователей: {len(users)}"
    )
    
    await callback.message.edit_text(result, parse_mode="HTML")
    await state.clear()

@router.callback_query(F.from_user.id == ADMIN_ID, F.data == "broadcast_cancel")
async def cancel_broadcast_callback(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("Рассылка отменена.")
    await callback.answer()

# Заглушка для чужих
@router.message(Command("stats", "broadcast"))
async def not_admin(message: types.Message):
    await message.answer("⛔️ У вас нет доступа к этой команде.")