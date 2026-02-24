import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

# Импортируем все роутеры
from handlers import (
    common, npc, bosses, events, classes,
    fishing, alchemy, checklist, calculators,
    randomizer, world_seeds, wiki, admin
)

# Токен бота берётся из переменной окружения
# (лучше так, чем хардкодить)
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 599835907  # твой ID, если нужно

async def main():
    logging.basicConfig(level=logging.INFO)

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    # Подключаем все роутеры
    # Порядок важен: сначала более специфичные, потом общие
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
    dp.include_router(admin.router)
    dp.include_router(common.router)  # common обычно последним

    # Удаляем старый webhook (если был)
    await bot.delete_webhook(drop_pending_updates=True)

    print("Бот успешно запущен!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот остановлен пользователем")
    except Exception as e:
        print(f"Критическая ошибка при запуске: {e}")