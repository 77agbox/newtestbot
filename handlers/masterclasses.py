from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram import Router

router = Router()

@router.message(Command("masterclasses"))
async def show_masterclasses(message: types.Message):
    # Пример вывода мастер-классов
    text = "Доступные мастер-классы:\n1. Мастер-класс по керамике\n2. Мастер-класс по кулинарии"
    await message.answer(text)
