from aiogram import types
from aiogram import Router
from config import ADMIN_ID

router = Router()

@router.message(lambda message: message.text.lower() == "написать в поддержку")
async def write_to_support(message: types.Message):
    tg_id = message.from_user.id
    await message.bot.send_message(ADMIN_ID, f"Новый запрос от пользователя: {tg_id}")
    await message.answer("Ваш запрос отправлен в поддержку. Мы скоро с вами свяжемся.")
