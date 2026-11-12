import asyncio
import logging
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN, ADMIN_IDS
from database.db_requests import init_db
from collector.collector import collector_router
from admin.admin_bot import admin_router

logging.basicConfig(level=logging.INFO)


async def main():
    print(f"🔍 ADMIN_IDS: {ADMIN_IDS}")

    # Инициализируем базу данных
    init_db()
    print("✅ База данных подключена и таблицы созданы.")

    # Настраиваем бота
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    # Подключаем роутеры (admin первым!)
    dp.include_router(admin_router)
    dp.include_router(collector_router)

    # Запускаем
    print("🤖 Бот запущен и слушает сообщения...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())