import asyncio
import logging
import os
import sys
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from dotenv import load_dotenv

# 1. ЗАГРУЗКА ИМПОРТОВ
# ВАЖНО: Названия здесь должны точь-в-точь совпадать с именами файлов в папке handlers!
# Я добавил 'crafting', которого не хватало в твоем списке.
from handlers import (
    common, 
    npc, 
    bosses, 
    events, 
    classes, 
    fishing, 
    alchemy, 
    checklist, 
    calculators,  # Убедись, что файл называется calculators.py, а не calc.py
    randomizer, 
    world_seeds, 
    wiki,
    crafting      # <-- Добавил этот импорт, иначе была ошибка
)

# Загружаем токен из .env (это безопаснее, чем config.py)
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

async def main():
    # Настройка логов
    logging.basicConfig(level=logging.INFO)

    # Проверка токена
    if not TOKEN:
        print("❌ Ошибка: Токен не найден! Проверь файл .env")
        return

    bot = Bot(token=TOKEN)
    dp = Dispatcher()

    print("🔄 Подключение модулей...")

    # 2. ПОДКЛЮЧЕНИЕ РОУТЕРОВ
    # Порядок важен: специфичные модули сначала, общие (common) — в конце.
    
    dp.include_router(crafting.router)
    dp.include_router(npc.router)
    dp.include_router(bosses.router)
    dp.include_router(events.router)
    dp.include_router(classes.router)
    dp.include_router(fishing.router)
    dp.include_router(alchemy.router)
    dp.include_router(checklist.router)
    dp.include_router(calculators.router)
    dp.include_router(randomizer.router)
    dp.include_router(world_seeds.router)
    dp.include_router(wiki.router)

    # Common всегда последний, так как там ловится команда /start
    dp.include_router(common.router)

    # Меню команд
    await bot.set_my_commands([
        BotCommand(command="start", description="🏠 Главное меню"),
        BotCommand(command="wiki", description="📖 Поиск"),
    ])

    print("✅ Все модули подключены! Бот запускается...")

    # Удаляем старые обновления (чтобы бот не отвечал на старые сообщения)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("🛑 Бот выключен вручную.")
    except Exception as e:
        print(f"❌ Критическая ошибка при запуске: {e}")
