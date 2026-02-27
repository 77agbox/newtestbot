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


class PackageForm(StatesGroup):
    people = State()
    activities = State()
    name = State()
    phone = State()

# ================= ДАННЫЕ =================

PACKAGE_MODULES = {
    "Картинг": [2200, 2100, 2000],
    "Симрейсинг": [1600, 1500, 1400],
    "Практическая стрельба": [1600, 1500, 1400],
    "Лазертаг": [1600, 1500, 1400],
    "Керамика": [1600, 1500, 1400],
    "Мягкая игрушка": [1300, 1200, 1100],
}

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
        [InlineKeyboardButton(text="🎉 Пакетные туры", callback_data="packages")],
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
    buttons = [
        [InlineKeyboardButton(text=d, callback_data=f"dir_{i}")]
        for i, d in enumerate(directions)
    ]
    buttons.append([InlineKeyboardButton(text="⬅ В меню", callback_data="menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def club_keyboard(clubs):
    buttons = [
        [InlineKeyboardButton(text=c["name"], callback_data=f"club_{i}")]
        for i, c in enumerate(clubs)
    ]
    buttons.append([InlineKeyboardButton(text="⬅ Назад", callback_data="back_dir")])
    buttons.append([InlineKeyboardButton(text="⬅ В меню", callback_data="menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def activities_keyboard(selected=None):
    selected = selected or []
    buttons = []

    for i, name in enumerate(PACKAGE_MODULES.keys()):
        text = f"{'✅ ' if name in selected else ''}{name}"
        buttons.append([InlineKeyboardButton(text=text, callback_data=f"act_{i}")])

    buttons.append([InlineKeyboardButton(text="🟢 Готово", callback_data="act_done")])
    buttons.append([InlineKeyboardButton(text="⬅ В меню", callback_data="menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# ================= START =================

@dp.message(CommandStart())
async def start(message: Message):
    await message.answer(
        "<b>Бот «Виктор»</b>\nДетско-юношеский центр «Виктория»\n\nВыберите раздел:",
        reply_markup=main_menu(message.from_user.id)
    )

# ================= МЕНЮ =================

@dp.callback_query(F.data == "menu")
async def menu(callback: CallbackQuery, state: FSMContext):
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
        f"✉ Поддержка\nИмя: {callback.from_user.full_name}\nTG ID: {callback.from_user.id}"
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

        address = str(club["address"]).lower()

        if addr_key == "gaz" and "газопровод" in address:
            filtered.append(club)
        elif addr_key == "ann" and "варшав" in address:
            filtered.append(club)
        elif addr_key == "tech" and "нагатин" in address:
            filtered.append(club)
        elif addr_key == "sher" and ("пушкин" in address or "щербинка" in address):
            filtered.append(club)
        elif addr_key == "online" and not address.strip():
            filtered.append(club)

    if not filtered:
        await callback.message.answer("Кружков не найдено.")
        await state.clear()
        await callback.answer()
        return

    await state.update_data(filtered=filtered)
    await state.set_state(ClubForm.direction)

    directions = sorted(set(c["direction"] for c in filtered))

    await callback.message.answer(
        "Выберите направление:",
        reply_markup=direction_keyboard(directions)
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("dir_"))
async def clubs_direction(callback: CallbackQuery, state: FSMContext):
    index = int(callback.data.split("_")[1])
    data = await state.get_data()

    directions = sorted(set(c["direction"] for c in data["filtered"]))

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
    club = data["filtered"][index]

    text = (
        f"<b>{club['name']}</b>\n\n"
        f"Возраст: {club['age']}\n"
        f"Педагог: {club['teacher']}\n"
        f"Адрес: {club['address']}\n\n"
        f"<a href='{club['link']}'>Подробнее</a>"
    )

    await callback.message.answer(text)
    await callback.answer()

# ================= ПАКЕТНЫЕ ТУРЫ =================

@dp.callback_query(F.data == "packages")
async def start_package(callback: CallbackQuery, state: FSMContext):
    await state.set_state(PackageForm.people)
    await callback.message.edit_text("Введите количество человек (минимум 5):")
    await callback.answer()


@dp.message(PackageForm.people)
async def package_people(message: Message, state: FSMContext):
    if not message.text.isdigit() or int(message.text) < 5:
        await message.answer("Минимум 5 человек.")
        return

    await state.update_data(people=int(message.text), selected=[])
    await state.set_state(PackageForm.activities)

    await message.answer("Выберите активности:", reply_markup=activities_keyboard())


@dp.callback_query(F.data.startswith("act_"))
async def choose_activity(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    selected = data.get("selected", [])

    if callback.data == "act_done":
        if not 1 <= len(selected) <= 3:
            await callback.answer("Выберите 1-3 активности", show_alert=True)
            return

        await state.set_state(PackageForm.name)
        await callback.message.answer("Введите ваше имя:")
        await callback.answer()
        return

    index = int(callback.data.split("_")[1])
    activity = list(PACKAGE_MODULES.keys())[index]

    if activity in selected:
        selected.remove(activity)
    else:
        if len(selected) >= 3:
            await callback.answer("Максимум 3 активности", show_alert=True)
            return
        selected.append(activity)

    await state.update_data(selected=selected)

    await callback.message.edit_reply_markup(
        reply_markup=activities_keyboard(selected)
    )
    await callback.answer()


@dp.message(PackageForm.name)
async def package_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(PackageForm.phone)
    await message.answer("Введите телефон:")


@dp.message(PackageForm.phone)
async def package_finish(message: Message, state: FSMContext):
    data = await state.get_data()

    people = data["people"]
    selected = data["selected"]
    name = data["name"]
    phone = message.text

    price_index = len(selected) - 1

    total = 0
    per_person = 0

    for act in selected:
        price = PACKAGE_MODULES[act][price_index]
        total += price * people
        per_person += price

    await bot.send_message(
        ADMIN_ID,
        f"🛒 Новая заявка\n\nИмя: {name}\nТелефон: {phone}\n"
        f"TG ID: {message.from_user.id}\n"
        f"Группа: {people}\nАктивности: {', '.join(selected)}\n"
        f"С человека: {per_person} ₽\nОбщая сумма: {total} ₽"
    )

    await message.answer(
        f"✅ Заявка принята!\nС человека: {per_person} ₽\nОбщая сумма: {total} ₽",
        reply_markup=main_menu(message.from_user.id)
    )

    await state.clear()

# ================= ЗАПУСК =================

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
