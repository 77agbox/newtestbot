from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram import Router

router = Router()

@router.message(Command("packages"))
async def show_packages(message: types.Message):
    text = "Пакетные туры:\n1. Активности для групп\n2. Праздники и события"
    await message.answer(text)
