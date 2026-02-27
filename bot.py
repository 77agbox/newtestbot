import asyncio
import logging
import os
import json
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
from openpyxl import load_workbook

# ================= CONFIG =================

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

logging.basicConfig(level=logging.INFO)

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

dp = Dispatcher(storage=MemoryStorage())

MASTER_FILE = "masterclasses.json"

# ================= FSM =================

class ClubForm(StatesGroup):
    age = State()
    address = State()
    direction = State()
    filtered = State()

class PackageForm(StatesGroup):
    people = State()
    activities = State()
    name = State()
    phone = State()

class MasterForm(StatesGroup):
    title = State()
    description = State()
    date = State()
    price = State()
    teacher = State()
    link = State()

class SupportForm(StatesGroup):
    text = State()

# ================= UTIL =================

def profile_link(user):
    return (
        f'<a href="https://t.me/{user.username}">@{user.username}</a>'
        if user.username else f'<a href="tg://user?id={user.id}">Профиль</a>'
    )

def load_masterclasses():
    if not os.path.exists(MASTER_FILE):
        with open(MASTER_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)
        return []
    with open(MASTER_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_masterclasses(data):
    with open(MASTER_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def parse_age_range(age_text: str):
    if not age_text:
        return None, None
    text = age_text.lower().replace("лет", "").replace(" ", "")
    if "-" in text:
        a, b = text.split("-")
        if a.isdigit() and b.isdigit():
            return int(a), int(b)
    if "+" in text:
        num = text.replace("+", "")
        if num.isdigit():
            return int(num), 99
    if text.isdigit():
        age = int(text)
        return age, age
    return None, None

def load_clubs():
    wb = load_workbook("joined_clubs.xlsx")
    sheet = wb.active
    clubs = []
    for row in sheet.iter_rows(min_row=2, values_only=True):
        clubs.append({
            "direction": row[0],
            "name": row[1],
            "age": row[2],
            "address": row[3],
            "teacher": row[4],
            "link": row[5],
        })
    return clubs

# ================= KEYBOARDS =================

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

# ================= SUPPORT =================

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

# ================= PACKAGES =================

PACKAGE_MODULES = {
    "Картинг": [2200, 2100, 2000],
    "Симрейсинг": [1600, 1500, 1400],
    "Лазертаг": [1600, 1500, 1400],
}

@dp.callback_query(F.data == "packages")
async def packages_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(PackageForm.people)
    await callback.message.answer("Введите количество человек (минимум 5):")
    await callback.answer()

@dp.message(PackageForm.people)
async def package_people(message: Message, state: FSMContext):
    if not message.text.isdigit() or int(message.text) < 5:
        await message.answer("Минимум 5 человек.")
        return
    await state.update_data(people=int(message.text))
    await state.set_state(PackageForm.name)
    await message.answer("Введите ваше имя:")

@dp.message(PackageForm.name)
async def package_name(message: Message, state: FSMContext):
    await bot.send_message(
        ADMIN_ID,
        f"🎉 Пакетный тур\n\n"
        f"Профиль: {profile_link(message.from_user)}\n"
        f"Имя: {message.text}"
    )
    await message.answer("Заявка отправлена администратору ✅")
    await state.clear()

# ================= ADMIN =================

@dp.callback_query(F.data == "admin")
async def admin(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Нет доступа", show_alert=True)
        return
    await callback.message.answer("Админ панель активна.")
    await callback.answer()

# ================= RUN =================

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
