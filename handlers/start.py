from aiogram import types
from aiogram import Router
from keyboards import bottom_kb

router = Router()

@router.message(Command("start"))
async def start(message: types.Message):
    await message.answer("Привет! Я Бот Виктор! Чем могу помочь?", reply_markup=bottom_kb())
