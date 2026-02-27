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
    address_key = State()
    direction = State()
    filtered = State()

# ================= ВСПОМОГАТЕЛЬНЫЕ =================

def parse_age_range(age_text: str):
    if not age_text:
        return None, None

    text = age_text.lower().replace("лет", "").replace(" ", "")

    if "-" in text:
        parts = text.split("-")
        if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
            return int(parts[0]), int(parts[1])

    if "+" in text:
        number = text.replace("+", "")
        if number.isdigit():
            return int(number), 99

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

# ================= КЛАВИАТУРЫ =================

def main_menu(user_id):
    buttons = [
        [InlineKeyboardButton(text="🎨 Кружки", callback_data="clubs")],
        [InlineKeyboardButton(text="✉ Написать в поддержку", callback_data="support")]
    ]

    if user_id == ADMIN_ID:
        buttons.append(
            [InlineKeyboardButton(text="⚙ Админ панель", callback_data="admin")]
        )

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def address_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Главное здание", callback_data="addr_gaz")],
        [InlineKeyboardButton(text="МХС Аннино", callback_data="addr_ann")],
        [InlineKeyboardButton(text="СП Юный техник", callback_data="addr_tech")],
        [InlineKeyboardButton(text="СП Щербинка", callback_data="addr_sher")],
        [InlineKeyboardButton(text="Онлайн", callback_data="addr_online")],
        [InlineKeyboardButton(text="⬅ В меню", callback_data="menu")]
    ])


def direction_keyboard(directions):
    buttons = []
    for i, d in enumerate(directions):
        buttons.append(
            [InlineKeyboardButton(text=d, callback_data=f"dir_{i}")]
        )

    buttons.append([InlineKeyboardButton(text="⬅ В меню", callback_data="menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def club_keyboard(clubs):
    buttons = []
    for i, c in enumerate(clubs):
        buttons.append(
            [InlineKeyboardButton(text=c["name"], callback_data=f"club_{i}")]
        )

    buttons.append([InlineKeyboardButton(text="⬅ Назад", callback_data="back_dir")])
    buttons.append([InlineKeyboardButton(text="⬅ В меню", callback_data="menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# ================= START =================

@dp.message(CommandStart())
async def start(message: Message):
    text = (
        "<b>Бот «Виктор»</b>\n"
        "Детско-юношеский центр «Виктория»\n\n"
        "Выберите интересующий раздел:"
    )
    await message.answer(text, reply_markup=main_menu(message.from_user.id))

# ================= МЕНЮ =================

@dp.callback_query(F.data == "menu")
async def back_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "Главное меню:",
        reply_markup=main_menu(callback.from_user.id)
    )
    await callback.answer()

# ================= ПОДДЕРЖКА =================

@dp.callback_query(F.data == "support")
async def support(callback: CallbackQuery):
    await bot.send_message(
        ADMIN_ID,
        f"✉ Обращение в поддержку\n"
        f"Имя: {callback.from_user.full_name}\n"
        f"TG ID: {callback.from_user.id}"
    )
    await callback.answer("Сообщение отправлено администратору ✅", show_alert=True)

# ================= КРУЖКИ =================

@dp.callback_query(F.data == "clubs")
async def clubs_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(ClubForm.age)
    await callback.message.edit_text("Укажите возраст.")
    await callback.answer()


@dp.message(ClubForm.age)
async def clubs_age(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Введите возраст числом.")
        return

    await state.update_data(age=int(message.text))
    await state.set_state(ClubForm.address_key)

    await message.answer("Выберите подразделение:", reply_markup=address_keyboard())


@dp.callback_query(F.data.startswith("addr_"))
async def clubs_address(callback: CallbackQuery, state: FSMContext):
    addr_key = callback.data.split("_")[1]
    data = await state.get_data()
    clubs = load_clubs()

    filtered = []

    for club in clubs:
        min_age, max_age = parse_age_range(str(club["age"]))

        if min_age is None:
            continue

        if not (min_age <= data["age"] <= max_age):
            continue

        address_text = str(club["address"]).lower()

        if addr_key == "gaz" and "газопровод" in address_text:
            filtered.append(club)

        elif addr_key == "ann" and "варшав" in address_text:
            filtered.append(club)

        elif addr_key == "tech" and "нагатин" in address_text:
            filtered.append(club)

        elif addr_key == "sher" and ("пушкин" in address_text or "щербинка" in address_text):
            filtered.append(club)

        elif addr_key == "online" and not address_text.strip():
            filtered.append(club)

    if not filtered:
        await callback.message.answer("К сожалению, подходящих кружков не найдено.")
        await state.clear()
        await callback.answer()
        return

    await state.update_data(filtered=filtered)
    await state.set_state(ClubForm.direction)

    directions = sorted(list(set([c["direction"] for c in filtered])))

    await callback.message.answer(
        "Выберите направление:",
        reply_markup=direction_keyboard(directions)
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("dir_"))
async def clubs_direction(callback: CallbackQuery, state: FSMContext):
    index = int(callback.data.split("_")[1])
    data = await state.get_data()

    directions = sorted(list(set([c["direction"] for c in data["filtered"]])))

    if index >= len(directions):
        await callback.answer("Ошибка выбора", show_alert=True)
        return

    selected_direction = directions[index]
    result = [c for c in data["filtered"] if c["direction"] == selected_direction]

    await state.update_data(filtered=result)

    await callback.message.answer(
        "Выберите кружок:",
        reply_markup=club_keyboard(result)
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("club_"))
async def club_card(callback: CallbackQuery, state: FSMContext):
    index = int(callback.data.split("_")[1])
    data = await state.get_data()
    clubs = data["filtered"]

    if index >= len(clubs):
        await callback.answer("Ошибка выбора", show_alert=True)
        return

    club = clubs[index]

    text = (
        f"<b>{club['name']}</b>\n\n"
        f"Возраст: {club['age']}\n"
        f"Педагог: {club['teacher']}\n"
        f"Адрес: {club['address']}\n\n"
        f"<a href='{club['link']}'>Подробнее</a>"
    )

    await callback.message.answer(text)
    await callback.answer()


@dp.callback_query(F.data == "back_dir")
async def back_to_directions(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    directions = sorted(list(set([c["direction"] for c in data["filtered"]])))

    await callback.message.answer(
        "Выберите направление:",
        reply_markup=direction_keyboard(directions)
    )
    await callback.answer()

# ================= ЗАПУСК =================

async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
