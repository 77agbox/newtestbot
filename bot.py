import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import CommandStart
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

# ================= CONFIG =================

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

logging.basicConfig(level=logging.INFO)

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

dp = Dispatcher(storage=MemoryStorage())

# ================= FSM =================

class SupportForm(StatesGroup):
    text = State()

class PackageForm(StatesGroup):
    people = State()
    name = State()

# ================= UTILS =================

def profile_link(user):
    return (
        f'<a href="https://t.me/{user.username}">@{user.username}</a>'
        if user.username else f'<a href="tg://user?id={user.id}">Профиль</a>'
    )

def main_menu(user_id):
    buttons = [
        [InlineKeyboardButton(text="🎨 Кружки", callback_data="clubs")],
        [InlineKeyboardButton(text="🧩 Мастер-классы", callback_data="masters")],
        [InlineKeyboardButton(text="🎉 Пакетные туры", callback_data="packages")],
        [InlineKeyboardButton(text="✉ Написать в поддержку", callback_data="support")]
    ]

    if user_id == ADMIN_ID:
        buttons.append(
            [InlineKeyboardButton(text="⚙ Админ панель", callback_data="admin")]
        )

    return InlineKeyboardMarkup(inline_keyboard=buttons)

# ================= START =================

@dp.message(CommandStart())
async def start(message: Message):
    await message.answer(
        "Приветствую! Я Бот Виктор!\n"
        "Я помогу вам выбрать интересные занятия в нашем центре.\n\n"
        "Выберите раздел:",
        reply_markup=main_menu(message.from_user.id)
    )

# ================= МЕНЮ =================

@dp.callback_query(F.data == "menu")
async def menu(callback: CallbackQuery):
    await callback.message.edit_text(
        "Главное меню:",
        reply_markup=main_menu(callback.from_user.id)
    )
    await callback.answer()

# ================= КРУЖКИ =================

@dp.callback_query(F.data == "clubs")
async def clubs(callback: CallbackQuery):
    await callback.message.answer(
        "Раздел кружков подключён.\n(Здесь будет логика фильтрации.)"
    )
    await callback.answer()

# ================= МАСТЕР-КЛАССЫ =================

@dp.callback_query(F.data == "masters")
async def masters(callback: CallbackQuery):
    await callback.message.answer(
        "Раздел мастер-классов подключён.\n(Здесь будет список МК.)"
    )
    await callback.answer()

# ================= ПАКЕТЫ =================

@dp.callback_query(F.data == "packages")
async def packages(callback: CallbackQuery, state: FSMContext):
    await state.set_state(PackageForm.people)
    await callback.message.answer("Введите количество человек (минимум 5):")
    await callback.answer()

@dp.message(PackageForm.people)
async def package_people(message: Message, state: FSMContext):
    if not message.text.isdigit() or int(message.text) < 5:
        await message.answer("Минимум 5 человек.")
        return

    await state.set_state(PackageForm.name)
    await message.answer("Введите ваше имя:")

@dp.message(PackageForm.name)
async def package_finish(message: Message, state: FSMContext):
    await bot.send_message(
        ADMIN_ID,
        f"🎉 Новая заявка\n\n"
        f"Профиль: {profile_link(message.from_user)}\n"
        f"Имя: {message.text}"
    )
    await message.answer("Заявка отправлена администратору ✅")
    await state.clear()

# ================= ПОДДЕРЖКА =================

@dp.callback_query(F.data == "support")
async def support_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(SupportForm.text)
    await callback.message.answer("Напишите ваше сообщение:")
    await callback.answer()

@dp.message(SupportForm.text)
async def support_send(message: Message, state: FSMContext):
    await bot.send_message(
        ADMIN_ID,
        f"✉ Поддержка\n\n"
        f"Профиль: {profile_link(message.from_user)}\n"
        f"{message.text}",
        disable_web_page_preview=True
    )
    await message.answer("Сообщение отправлено администратору ✅")
    await state.clear()

# ================= АДМИН =================

@dp.callback_query(F.data == "admin")
async def admin(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Нет доступа", show_alert=True)
        return

    await callback.message.answer("Админ панель подключена.")
    await callback.answer()

# ================= RUN =================

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
