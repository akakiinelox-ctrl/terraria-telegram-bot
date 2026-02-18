import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from config import TOKEN

# Импортируем только те файлы, которые РЕАЛЬНО есть в папке handlers на GitHub
from handlers import (
    common, npc, bosses, events, classes, 
    fishing, alchemy, checklist, calculators, 
    randomizer, world_seeds, wiki
)

async def main():
    # Настройка логирования для Railway
    logging.basicConfig(level=logging.INFO)

    bot = Bot(token=TOKEN)
    dp = Dispatcher()

    # ПОДКЛЮЧАЕМ РОУТЕРЫ
    # Сначала контентные разделы
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
    
    # common.router ДОЛЖЕН БЫТЬ ПОСЛЕДНИМ (обрабатывает /start и Главное меню)
    dp.include_router(common.router)

    # Очистка старых обновлений
    await bot.delete_webhook(drop_pending_updates=True)

    print("✅ Бот успешно запущен и готов к работе!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("🛑 Бот выключен.")
