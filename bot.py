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

# ================= FSM =================

class ClubForm(StatesGroup):
    age = State()
    address = State()
    direction = State()
    clubs = State()

# ================= UTIL =================

def profile_link(user):
    return (
        f'<a href="https://t.me/{user.username}">@{user.username}</a>'
        if user.username else f'<a href="tg://user?id={user.id}">Профиль</a>'
    )

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
        [InlineKeyboardButton(text="⬅ В меню", callback_data="menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def address_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Главное здание", callback_data="addr_0")],
        [InlineKeyboardButton(text="МХС Аннино", callback_data="addr_1")],
        [InlineKeyboardButton(text="СП Юный техник", callback_data="addr_2")],
        [InlineKeyboardButton(text="СП Щербинка", callback_data="addr_3")],
        [InlineKeyboardButton(text="Онлайн", callback_data="addr_4")],
        [InlineKeyboardButton(text="⬅ В меню", callback_data="menu")]
    ])

# ================= START =================

@dp.message(CommandStart())
async def start(message: Message):
    await message.answer(
        "Приветствую! Я Бот Виктор!\n"
        "Я помогу вам выбрать интересные занятия в нашем центре.\n\n"
        "Выберите раздел:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🎨 Кружки", callback_data="clubs")]
        ])
    )

# ================= MENU =================

@dp.callback_query(F.data == "menu")
async def menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "Главное меню:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🎨 Кружки", callback_data="clubs")]
        ])
    )
    await callback.answer()

# ================= CLUBS =================

@dp.callback_query(F.data == "clubs")
async def clubs_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(ClubForm.age)
    await callback.message.edit_text("Укажите возраст:")
    await callback.answer()

@dp.message(ClubForm.age)
async def clubs_age(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Введите возраст числом.")
        return

    await state.update_data(age=int(message.text))
    await state.set_state(ClubForm.address)

    await message.answer("Выберите подразделение:",
                         reply_markup=address_keyboard())

@dp.callback_query(F.data.startswith("addr_"))
async def clubs_address(callback: CallbackQuery, state: FSMContext):
    index = int(callback.data.split("_")[1])
    data = await state.get_data()
    clubs = load_clubs()

    address_filters = [
        "газопровод",
        "варшав",
        "нагатин",
        "пушкин",
        ""  # онлайн
    ]

    filtered = []

    for club in clubs:
        min_age, max_age = parse_age_range(str(club["age"]))
        if min_age is None:
            continue

        if not (min_age <= data["age"] <= max_age):
            continue

        address = str(club["address"]).lower()

        if index == 4:
            if not address.strip():
                filtered.append(club)
        else:
            if address_filters[index] in address:
                filtered.append(club)

    if not filtered:
        await callback.message.answer("Подходящих кружков нет.")
        await state.clear()
        await callback.answer()
        return

    directions = sorted(set(c["direction"] for c in filtered))
    await state.update_data(clubs=filtered)

    buttons = [
        [InlineKeyboardButton(text=d, callback_data=f"dir_{i}")]
        for i, d in enumerate(directions)
    ]
    buttons.append([InlineKeyboardButton(text="⬅ В меню", callback_data="menu")])

    await callback.message.answer(
        "Выберите направление:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )
    await state.set_state(ClubForm.direction)
    await callback.answer()

@dp.callback_query(F.data.startswith("dir_"))
async def clubs_direction(callback: CallbackQuery, state: FSMContext):
    index = int(callback.data.split("_")[1])
    data = await state.get_data()

    clubs = data["clubs"]
    directions = sorted(set(c["direction"] for c in clubs))
    selected_direction = directions[index]

    result = [c for c in clubs if c["direction"] == selected_direction]

    buttons = [
        [InlineKeyboardButton(text=c["name"], callback_data=f"club_{i}")]
        for i, c in enumerate(result)
    ]
    buttons.append([InlineKeyboardButton(text="⬅ Назад", callback_data="clubs")])

    await state.update_data(clubs=result)

    await callback.message.answer(
        "Выберите кружок:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )
    await callback.answer()

@dp.callback_query(F.data.startswith("club_"))
async def club_card(callback: CallbackQuery, state: FSMContext):
    index = int(callback.data.split("_")[1])
    data = await state.get_data()

    club = data["clubs"][index]

    text = (
        f"<b>{club['name']}</b>\n\n"
        f"Возраст: {club['age']}\n"
        f"Педагог: {club['teacher']}\n"
        f"Адрес: {club['address']}\n\n"
        f"<a href='{club['link']}'>Записаться</a>"
    )

    await callback.message.answer(text)
    await callback.answer()

# ================= RUN =================

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
