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


# ================== КЛАВИАТУРЫ ==================

def main_menu(admin=False):
    buttons = [
        [InlineKeyboardButton(text="🎨 Кружки", callback_data="clubs")],
        [InlineKeyboardButton(text="🧩 Мастер-классы", callback_data="masters")],
        [InlineKeyboardButton(text="🎉 Пакетные туры", callback_data="packages")],
        [InlineKeyboardButton(text="✉ Написать в поддержку", callback_data="support")]
    ]

    if admin:
        buttons.append(
            [InlineKeyboardButton(text="⚙ Админ панель", callback_data="admin")]
        )

    return InlineKeyboardMarkup(inline_keyboard=buttons)


# ================== START ==================

@dp.message(CommandStart())
async def start(message: Message):
    text = (
        "<b>Бот «Виктор»</b>\n"
        "Детско-юношеский центр «Виктория»\n\n"
        "У нас 4 подразделения:\n"
        "• Главное здание – ул. Газопровод д.4\n"
        "• МХС Аннино – Варшавское ш. 145 стр.1\n"
        "• СП Юный техник – ул. Нагатинская 22к2\n"
        "• СП Щербинка – ул. Пушкинская 3А\n\n"
        "Что вас интересует?"
    )

    await message.answer(
        text,
        reply_markup=main_menu(message.from_user.id == ADMIN_ID)
    )


# ================== ПОДДЕРЖКА ==================

@dp.callback_query(F.data == "support")
async def support(callback: CallbackQuery):
    await bot.send_message(
        ADMIN_ID,
        f"✉ Обращение в поддержку\n"
        f"User: {callback.from_user.full_name}\n"
        f"TG ID: {callback.from_user.id}"
    )

    await callback.message.answer("Ваш запрос отправлен администратору ✅")
    await callback.answer()


# ================== КРУЖКИ ==================

# ================== КРУЖКИ ==================

class ClubForm(StatesGroup):
    age = State()


def parse_age_range(age_text: str):
    """
    Извлекаем минимальный и максимальный возраст из строки.
    Поддерживает:
    6-8
    6 - 8 лет
    от 6 до 8
    7+
    5
    """

    if not age_text:
        return None, None

    text = age_text.lower().replace("лет", "").replace(" ", "")

    # формат 6-8
    if "-" in text:
        parts = text.split("-")
        if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
            return int(parts[0]), int(parts[1])

    # формат от6до8
    if "от" in text and "до" in text:
        try:
            start = int(text.split("от")[1].split("до")[0])
            end = int(text.split("до")[1])
            return start, end
        except:
            pass

    # формат 7+
    if "+" in text:
        number = text.replace("+", "")
        if number.isdigit():
            return int(number), 99

    # формат одно число
    if text.isdigit():
        age = int(text)
        return age, age

    return None, None


def load_clubs():
    wb = load_workbook("joined_clubs.xlsx")
    sheet = wb.active
    data = []

    for row in sheet.iter_rows(min_row=2, values_only=True):
        data.append({
            "direction": row[0],
            "name": row[1],
            "age": row[2],
            "address": row[3],
            "teacher": row[4],
            "link": row[5],
        })
    return data


@dp.callback_query(F.data == "clubs")
async def clubs_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(ClubForm.age)
    await callback.message.answer("Укажите возраст.")
    await callback.answer()


@dp.message(ClubForm.age)
async def clubs_age(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Введите возраст числом.")
        return

    user_age = int(message.text)
    clubs = load_clubs()

    filtered = []

    for club in clubs:
        min_age, max_age = parse_age_range(str(club["age"]))

        if min_age is not None and max_age is not None:
            if min_age <= user_age <= max_age:
                filtered.append(club)

    if not filtered:
        await message.answer("К сожалению, подходящих кружков не найдено.")
        await state.clear()
        return

    text = "<b>Подходящие кружки:</b>\n\n"

    for c in filtered:
        text += (
            f"<b>{c['name']}</b>\n"
            f"Возраст: {c['age']}\n"
            f"Педагог: {c['teacher']}\n"
            f"Адрес: {c['address']}\n"
            f"<a href='{c['link']}'>Подробнее</a>\n\n"
        )

    await message.answer(text)
    await state.clear()


# ================== ПАКЕТЫ ==================

@dp.callback_query(F.data == "packages")
async def packages(callback: CallbackQuery):
    await callback.message.answer(
        "<b>Пакетные туры</b>\n\n"
        "Хотите весело провести время?\n"
        "Выбирайте от 1 до 3 активностей.\n\n"
        "Для групп от 5 человек.\n"
        "В стоимость входит помещение для чаепития."
    )
    await callback.answer()


# ================== МАСТЕР-КЛАССЫ ==================

@dp.callback_query(F.data == "masters")
async def masters(callback: CallbackQuery):
    await callback.message.answer(
        "Раздел мастер-классов находится в разработке."
    )
    await callback.answer()


# ================== АДМИН ==================

@dp.callback_query(F.data == "admin")
async def admin_panel(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Нет доступа", show_alert=True)
        return

    await callback.message.answer("Админ панель")
    await callback.answer()


# ================== ЗАПУСК ==================

async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
