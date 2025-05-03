# src/bot/main.py
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
import asyncio
import logging
import os
from dotenv import load_dotenv
from src.db.database import init_db


from handlers import router  # импортируем router, не register_handlers

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")

main_menu_commands = [
    BotCommand(command="/start", description="Загрузить скриншоты из банка"),
    BotCommand(command="/finish_upload", description="Завершить загрузку скриншотов"),
]

async def main():
    logging.basicConfig(level=logging.INFO)

    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)  # регистрируем router
    
    async with init_db():
        await bot.delete_webhook(drop_pending_updates=True)
        await bot.set_my_commands(main_menu_commands)
        await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
