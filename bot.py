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

# ================= УТИЛИТЫ =================

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
        parts = text.split("-")
        if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
            return int(parts[0]), int(parts[1])
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

# ================= КЛАВИАТУРЫ =================

def main_menu(user_id):
    buttons = [
        [InlineKeyboardButton(text="🎨 Кружки", callback_data="clubs")],
        [InlineKeyboardButton(text="🧩 Мастер-классы", callback_data="masters")],
        [InlineKeyboardButton(text="🎉 Пакетные туры", callback_data="packages")],
        [InlineKeyboardButton(text="✉ Написать в поддержку", callback_data="support")]
    ]
    if user_id == ADMIN_ID:
        buttons.append([InlineKeyboardButton(text="⚙ Админ панель", callback_data="admin")])
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
        f"✉ Сообщение в поддержку\n\n"
        f"Профиль: {profile_link(message.from_user)}\n"
        f"TG ID: {message.from_user.id}\n\n"
        f"{message.text}",
        disable_web_page_preview=True
    )
    await message.answer("Сообщение отправлено администратору ✅")
    await state.clear()

# ================= ПАКЕТНЫЕ ТУРЫ =================

PACKAGE_MODULES = {
    "Картинг": [2200, 2100, 2000],
    "Симрейсинг": [1600, 1500, 1400],
    "Практическая стрельба": [1600, 1500, 1400],
    "Лазертаг": [1600, 1500, 1400],
    "Керамика": [1600, 1500, 1400],
    "Мягкая игрушка": [1300, 1200, 1100],
}

@dp.callback_query(F.data == "packages")
async def start_package(callback: CallbackQuery, state: FSMContext):
    await state.set_state(PackageForm.people)
    await callback.message.answer("Введите количество человек (минимум 5):")
    await callback.answer()

@dp.message(PackageForm.people)
async def package_people(message: Message, state: FSMContext):
    if not message.text.isdigit() or int(message.text) < 5:
        await message.answer("Минимум 5 человек.")
        return
    await state.update_data(people=int(message.text), selected=[])
    await state.set_state(PackageForm.activities)

    buttons = [
        [InlineKeyboardButton(text=name, callback_data=f"act_{i}")]
        for i, name in enumerate(PACKAGE_MODULES.keys())
    ]
    buttons.append([InlineKeyboardButton(text="🟢 Готово", callback_data="act_done")])

    await message.answer("Выберите 1–3 активности:",
                         reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

@dp.callback_query(F.data.startswith("act_"))
async def choose_activity(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    selected = data.get("selected", [])

    if callback.data == "act_done":
        if not 1 <= len(selected) <= 3:
            await callback.answer("Выберите 1–3 активности", show_alert=True)
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
    await callback.answer("Выбор обновлён")

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
        f"🛒 Новая заявка\n\n"
        f"Клиент: {name}\n"
        f"Телефон: {phone}\n"
        f"Профиль: {profile_link(message.from_user)}\n"
        f"TG ID: {message.from_user.id}\n\n"
        f"Группа: {people}\n"
        f"Активности: {', '.join(selected)}\n"
        f"С человека: {per_person} ₽\n"
        f"Общая сумма: {total} ₽",
        disable_web_page_preview=True
    )

    await message.answer("Заявка отправлена администратору ✅")
    await state.clear()

# ================= ЗАПУСК =================

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
