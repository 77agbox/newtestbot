from aiogram import Bot, Dispatcher, types
from aiogram.fsm.executor import start_polling  # Новый импорт
from config import BOT_TOKEN

bot = Bot(token=BOT_TOKEN, parse_mode=types.ParseMode.HTML)  # Новый формат
dp = Dispatcher(bot)

if __name__ == '__main__':
    from handlers import register_handlers
    register_handlers(dp)
    start_polling(dp, skip_updates=True)  # Новый формат
