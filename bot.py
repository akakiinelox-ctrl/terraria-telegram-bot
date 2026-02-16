import asyncio
import logging
from aiogram import Bot, Dispatcher
from config import TOKEN

# Импортируем роутеры из всех файлов в папке handlers
from handlers import common, npc, bosses, events, classes, fishing, alchemy, checklist, calculators, randomizer, world_seeds, pylons
async def main():
    logging.basicConfig(level=logging.INFO)

    bot = Bot(token=TOKEN)
    dp = Dispatcher()

    # Подключаем все модули (роутеры)
    dp.include_router(common.router)
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
    dp.include_router(pylons.router)

    # Запуск бота
    print("Бот запущен и готов к охоте на боссов!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот выключен.")
