import requests
from bs4 import BeautifulSoup
from aiogram import Bot, Dispatcher, types, Router
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, \
    CallbackQuery, InlineQuery, InlineQueryResultArticle, InputTextMessageContent
from aiogram.utils.markdown import code
import asyncio
from datetime import datetime, timezone, timedelta
import hashlib
from aiogram.fsm.storage.memory import MemoryStorage

TOKEN = "7995519791:AAGfxnAh_jC0-8r6BySSafZ3KlY_OlMNBFQ"

bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
router = Router()

dp.include_router(router)

MOSCOW_TZ = timezone(timedelta(hours=3))

GROUPS = {
    18: "506", 22: "М1-21-1", 23: "М1-21-2", 24: "Н1-21", 25: "М2-22",
    26: "М2К-22", 27: "М1-22-1", 28: "М1-22-2", 29: "Н1-22", 31: "С1-22",
    32: "ИВ1-22-1", 33: "ИВ1-22-2", 34: "ИВ1К-22", 35: "ИВ2-22", 36: "ИП1-22",
    37: "ИП2К-22", 38: "МТ1-22", 39: "ИВ2-21", 40: "ИВ2К-21-1", 41: "ИВ2К-21-2",
    42: "ИВ1-21", 44: "ИП1-21", 45: "ИВ1К-21", 46: "С1-21", 47: "МТ1-21",
    60: "М2-23", 61: "С1-23", 62: "МТ1-23", 63: "М1-23-1", 64: "М1-23-2",
    65: "М1-23-3", 66: "Р2-23", 67: "ИВ1-23-1", 68: "ИВ1-23-2", 69: "ИП1-23",
    70: "ИП2-23", 125: "Н1-24", 21: "409", 20: "408"
}

user_groups = {}


def get_user_group(user_id):
    return user_groups.get(user_id, 44)


def fetch_schedule(group_id, target_date=None):
    url = f"https://e-spo.ru/org/rasp/export/site/index?pid=1&RaspBaseSearch%5Bgroup_id%5D={group_id}&RaspBaseSearch%5Bsemestr%5D=vesna&RaspBaseSearch%5Bprepod_id%5D="
    response = requests.get(url)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, 'html.parser')
    schedule = []

    schedule_cards = soup.find_all('div', class_='card h-100')
    for card in schedule_cards:
        day_header = card.find('h5', class_='card-title')
        if day_header:
            day_info = day_header.get_text(strip=True)
            day_parts = day_info.split(' - ')
            weekday, date = day_parts if len(day_parts) == 2 else ("", "")

            if target_date and target_date != date:
                continue

        table = card.find('table', class_='table table-hover table-striped gs-5')
        if table:
            rows = table.find_all('tr')
            lessons = []
            for row in rows:
                columns = row.find_all('td')
                if len(columns) >= 4:
                    lesson_number_and_time = columns[0].text.strip()
                    parts = lesson_number_and_time.split(maxsplit=1)
                    lesson_number = parts[0]
                    time = parts[1] if len(parts) > 1 else ""

                    subject_data = columns[1].get_text(" ", strip=True).replace("РТК", "").strip()
                    room = columns[2].get_text(strip=True)
                    teacher = columns[3].get_text(strip=True)

                    if subject_data:
                        lessons.append(
                            f"Урок {lesson_number} {time}\nПредмет: {subject_data}\nКабинет: {room}\nПреподаватель: {teacher}\n")

            if lessons:
                schedule.append(f"{weekday}, {date}\n" + "\n".join(lessons))

    return schedule


@router.message(Command("start"))
async def start(message: Message):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
        [KeyboardButton(text="📌 Расписание на сегодня")],
        [KeyboardButton(text="📅 Ближайшее расписание")],
        [KeyboardButton(text="🔄 Сменить группу")]
    ])
    await message.answer("Привет! Выбери нужную опцию:", reply_markup=keyboard)


@router.message()
async def button_handler(message: Message):
    user_id = message.from_user.id
    group_id = get_user_group(user_id)

    if message.text == "📌 Расписание на сегодня":
        today_date = datetime.now(MOSCOW_TZ).strftime("%d.%m.%Y")
        schedule = fetch_schedule(group_id, target_date=today_date)
    elif message.text == "📅 Ближайшее расписание":
        schedule = fetch_schedule(group_id)
    elif message.text == "🔄 Сменить группу":
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text=name, callback_data=f"group_{gid}")] for gid, name in
                             GROUPS.items()]
        )
        await message.answer("Выберите свою группу:", reply_markup=keyboard)
        return
    else:
        await message.answer("Неизвестная команда. Выберите вариант из меню.")
        return

    message_text = "\n\n".join(schedule) if schedule else "Расписание не найдено."
    await message.answer(code(message_text), parse_mode="MarkdownV2")


@router.callback_query()
async def change_group(callback: CallbackQuery):
    user_id = callback.from_user.id
    group_id = int(callback.data.split("_")[1])
    user_groups[user_id] = group_id
    await callback.message.answer(f"Группа изменена на {GROUPS[group_id]}")
    await callback.answer()


async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
