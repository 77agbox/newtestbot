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

# ================= УТИЛИТЫ =================

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
        [InlineKeyboardButton(text="✉ Поддержка", callback_data="support")]
    ]
    if user_id == ADMIN_ID:
        buttons.append([InlineKeyboardButton(text="⚙ Админ панель", callback_data="admin")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# ================= START =================

@dp.message(CommandStart())
async def start(message: Message):
    await message.answer(
        "<b>Бот «Виктор»</b>\nДетско-юношеский центр «Виктория»\n\nВыберите раздел:",
        reply_markup=main_menu(message.from_user.id)
    )

# ================= ПОДДЕРЖКА =================

@dp.callback_query(F.data == "support")
async def support(callback: CallbackQuery):
    await bot.send_message(
        ADMIN_ID,
        f"✉ Поддержка\nИмя: {callback.from_user.full_name}\nTG ID: {callback.from_user.id}"
    )
    await callback.answer("Сообщение отправлено админу ✅", show_alert=True)

# ================= МАСТЕР-КЛАССЫ =================

@dp.callback_query(F.data == "masters")
async def show_masters(callback: CallbackQuery):
    masters = load_masterclasses()
    if not masters:
        await callback.message.answer("Мастер-классы пока не добавлены.")
    else:
        buttons = [
            [InlineKeyboardButton(text=m["title"], callback_data=f"master_{i}")]
            for i, m in enumerate(masters)
        ]
        buttons.append([InlineKeyboardButton(text="⬅ В меню", callback_data="menu")])
        await callback.message.answer(
            "Доступные мастер-классы:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
        )
    await callback.answer()

@dp.callback_query(F.data.startswith("master_"))
async def master_card(callback: CallbackQuery):
    index = int(callback.data.split("_")[1])
    masters = load_masterclasses()
    m = masters[index]
    text = (
        f"<b>{m['title']}</b>\n\n{m['description']}\n\n"
        f"📅 {m['date']}\n💰 {m['price']} ₽\n👩‍🏫 {m['teacher']}\n\n"
        f"<a href='{m['link']}'>Подробнее</a>"
    )
    await callback.message.answer(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✉ Записаться", callback_data=f"enroll_{index}")],
            [InlineKeyboardButton(text="⬅ Назад", callback_data="masters")]
        ])
    )
    await callback.answer()

@dp.callback_query(F.data.startswith("enroll_"))
async def enroll_master(callback: CallbackQuery):
    index = int(callback.data.split("_")[1])
    masters = load_masterclasses()
    m = masters[index]
    await bot.send_message(
        ADMIN_ID,
        f"📚 Запись на МК\n{m['title']}\nИмя: {callback.from_user.full_name}\nTG ID: {callback.from_user.id}"
    )
    await callback.answer("Заявка отправлена админу ✅", show_alert=True)

# ================= АДМИН =================

@dp.callback_query(F.data == "admin")
async def admin_panel(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Нет доступа", show_alert=True)
        return
    await callback.message.answer(
        "Админ панель:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➕ Добавить МК", callback_data="add_master")],
            [InlineKeyboardButton(text="❌ Удалить МК", callback_data="delete_master")],
            [InlineKeyboardButton(text="⬅ В меню", callback_data="menu")]
        ])
    )
    await callback.answer()

@dp.callback_query(F.data == "add_master")
async def add_master(callback: CallbackQuery, state: FSMContext):
    await state.set_state(MasterForm.title)
    await callback.message.answer("Введите название мастер-класса:")
    await callback.answer()

@dp.message(MasterForm.title)
async def m_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    await state.set_state(MasterForm.description)
    await message.answer("Описание:")

@dp.message(MasterForm.description)
async def m_desc(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await state.set_state(MasterForm.date)
    await message.answer("Дата и время:")

@dp.message(MasterForm.date)
async def m_date(message: Message, state: FSMContext):
    await state.update_data(date=message.text)
    await state.set_state(MasterForm.price)
    await message.answer("Стоимость:")

@dp.message(MasterForm.price)
async def m_price(message: Message, state: FSMContext):
    await state.update_data(price=message.text)
    await state.set_state(MasterForm.teacher)
    await message.answer("Педагог:")

@dp.message(MasterForm.teacher)
async def m_teacher(message: Message, state: FSMContext):
    await state.update_data(teacher=message.text)
    await state.set_state(MasterForm.link)
    await message.answer("Ссылка:")

@dp.message(MasterForm.link)
async def m_save(message: Message, state: FSMContext):
    data = await state.get_data()
    data["link"] = message.text
    masters = load_masterclasses()
    masters.append(data)
    save_masterclasses(masters)
    await message.answer("Мастер-класс добавлен ✅")
    await state.clear()

@dp.callback_query(F.data == "delete_master")
async def delete_master(callback: CallbackQuery):
    masters = load_masterclasses()
    buttons = [
        [InlineKeyboardButton(text=f"❌ {m['title']}", callback_data=f"del_{i}")]
        for i, m in enumerate(masters)
    ]
    await callback.message.answer(
        "Выберите МК для удаления:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )
    await callback.answer()

@dp.callback_query(F.data.startswith("del_"))
async def confirm_delete(callback: CallbackQuery):
    index = int(callback.data.split("_")[1])
    masters = load_masterclasses()
    masters.pop(index)
    save_masterclasses(masters)
    await callback.answer("Удалено ✅", show_alert=True)

# ================= ЗАПУСК =================

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
