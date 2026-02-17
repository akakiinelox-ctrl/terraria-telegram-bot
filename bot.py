import asyncio
import logging
from aiogram import Bot, Dispatcher
from config import TOKEN

# 1. Импортируем только существующие модули (БЕЗ crafting)
from handlers import (
    common, npc, bosses, events, classes, 
    fishing, alchemy, checklist, calculators, 
    randomizer, world_seeds, wiki
)

async def main():
    # Настройка логирования для отслеживания ошибок в консоли Railway
    logging.basicConfig(level=logging.INFO)

    bot = Bot(token=TOKEN)
    dp = Dispatcher()

    # 2. Подключаем роутеры (ПОРЯДОК ВАЖЕН)
    # Сначала все специфические разделы
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
    
    # Главное меню (common) ВСЕГДА должно быть последним в списке
    dp.include_router(common.router)

    # Очистка очереди обновлений, чтобы бот не «лагал» при запуске
    await bot.delete_webhook(drop_pending_updates=True)

    print("✅ Бот успешно запущен (без модуля крафтинга)!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("🛑 Бот выключен.")
