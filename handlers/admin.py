from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import ParseMode
from aiogram.dispatcher.filters import Command
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram import Router
from config import ADMIN_ID
from keyboards import bottom_kb

router = Router()

# Состояния для админки
class AdminForm(StatesGroup):
    action = State()

@router.message(Command("admin"))
async def admin_menu(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        await message.answer("Вы в админ панели. Что хотите сделать?", reply_markup=bottom_kb())
    else:
        await message.answer("Вы не администратор!")

# Добавление мастер-классов (пример)
@router.message(Command("add_masterclass"))
async def add_masterclass(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        await message.answer("Введите данные мастер-класса (название, описание и т.д.)")
    else:
        await message.answer("Вы не администратор!")
