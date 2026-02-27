import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from config import BOT_TOKEN

# Настройка логирования
logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN, parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot)

# Регистрация обработчиков
from handlers import register_handlers
register_handlers(dp)

# Основная функция для запуска бота
async def main():
    await dp.start_polling()

if __name__ == '__main__':
    asyncio.run(main())
