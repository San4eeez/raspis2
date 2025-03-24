from aiogram import Router, types, Bot
from aiogram.filters import Command, CommandObject
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
)
from aiogram.utils.markdown import code
from datetime import datetime
from models import GROUPS, TEACHERS
from services import fetch_schedule
from analytics import log_request, send_analytics
import json
import asyncio

router = Router()

# Загружаем данные о группах пользователей из файла (если он существует)
try:
    with open('user_groups.json', 'r') as file:
        user_groups = json.load(file)
except FileNotFoundError:
    user_groups = {}


def save_user_groups():
    """Сохраняет данные о группах пользователей в файл."""
    with open('user_groups.json', 'w') as file:
        json.dump(user_groups, file)


def get_user_group(user_id: int) -> int:
    """Возвращает группу пользователя или группу по умолчанию, если пользователь не выбран."""
    return user_groups.get(str(user_id), 44)  # Используем строковый ключ для JSON


def split_message(text: str, max_length: int = 4096) -> list[str]:
    """Разбивает текст на части, каждая из которых не превышает max_length символов."""
    return [text[i:i + max_length] for i in range(0, len(text), max_length)]


@router.message(Command("start"))
async def start(message: Message):
    """Обработчик команды /start."""
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
        [KeyboardButton(text="📌 Расписание на сегодня")],
        [KeyboardButton(text="📅 Расписание на неделю")],
        [KeyboardButton(text="🔄 Сменить группу")],
        [KeyboardButton(text="👨‍🏫 Найти преподавателя")]
    ])
    await message.answer("Привет! Выбери нужную опцию:", reply_markup=keyboard)


@router.message(Command("analytics"))
async def analytics_command(message: types.Message, bot: Bot):
    """Обработчик команды /analytics."""
    await send_analytics(bot, message.chat.id)  # Передаем chat_id


@router.message()
async def button_handler(message: Message, command: CommandObject = None):
    """Обработчик кнопок и команд с упоминанием бота."""
    # Логируем запрос
    user_id = message.from_user.id
    username = message.from_user.username or "Без имени"
    log_request(user_id, username)

    # Если команда пришла с упоминанием бота, извлекаем текст команды
    if command and command.prefix == "@":
        command_text = command.command
    else:
        command_text = message.text

    user_id = message.from_user.id
    group_id = get_user_group(user_id)

    if command_text == "📌 Расписание на сегодня" or command_text == "сегодня":
        today_date = datetime.now().strftime("%d.%m.%Y")
        schedule = fetch_schedule(group_id, entity_type="group", target_date=today_date)
    elif command_text == "📅 Расписание на неделю" or command_text == "расписание":
        schedule = fetch_schedule(group_id, entity_type="group")
    elif command_text == "🔄 Сменить группу" or command_text == "сменить_группу":
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text=name, callback_data=f"group_{gid}")] for gid, name in
                             GROUPS.items()]
        )
        await message.answer("Выберите свою группу:", reply_markup=keyboard)
        return
    elif command_text == "👨‍🏫 Найти преподавателя" or command_text == "преподаватель":
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text=teacher["fio"], callback_data=f"teacher_{teacher['value']}")] for
                            teacher in TEACHERS]
        )
        await message.answer("Выберите преподавателя:", reply_markup=keyboard)
        return
    else:
        await message.answer("Неизвестная команда. Выберите вариант из меню.")
        return

    message_text = "\n\n".join(schedule) if schedule else "Расписание не найдено."

    # Разбиваем сообщение на части и отправляем
    message_parts = split_message(message_text)
    for part in message_parts:
        await message.answer(code(part), parse_mode="MarkdownV2")
        await asyncio.sleep(1)  # Задержка между сообщениями


@router.callback_query()
async def callback_handler(callback: CallbackQuery):
    """Обработчик callback-запросов."""
    data = callback.data
    if data.startswith("group_"):
        user_id = str(callback.from_user.id)
        group_id = int(data.split("_")[1])
        user_groups[user_id] = group_id
        save_user_groups()
        await callback.message.answer(f"Группа изменена на {GROUPS[group_id]}")
    elif data.startswith("teacher_"):
        teacher_id = data.split("_")[1]
        teacher_name = next((teacher["fio"] for teacher in TEACHERS if teacher["value"] == teacher_id), "Неизвестный преподаватель")
        today_date = datetime.now().strftime("%d.%m.%Y")
        schedule = fetch_schedule(teacher_id, entity_type="teacher", target_date=today_date)
        message_text = f"Расписание преподавателя {teacher_name}:\n\n" + "\n\n".join(
            schedule) if schedule else "Расписание не найдено."

        # Разбиваем сообщение на части и отправляем
        message_parts = split_message(message_text)
        for part in message_parts:
            await callback.message.answer(code(part), parse_mode="MarkdownV2")
            await asyncio.sleep(1)  # Задержка между сообщениями
    await callback.answer()


@router.inline_query()
async def inline_handler(query: types.InlineQuery):
    """Обработчик инлайн-запросов."""
    user_id = query.from_user.id
    group_id = get_user_group(user_id)

    # Получаем расписание
    schedule = fetch_schedule(group_id, entity_type="group")
    day_shedule = fetch_schedule(group_id, entity_type="group", target_date=datetime.now().strftime("%d.%m.%Y"))
    message_text = "\n\n".join(schedule) if schedule else "Расписание не найдено."
    day_text = "\n\n".join(day_shedule) if schedule else "Расписание не найдено."

    # Разбиваем сообщения на части
    message_parts = split_message(message_text)
    day_parts = split_message(day_text)

    # Формируем результаты с учетом частей
    results = []
    for i, part in enumerate(message_parts):
        results.append(
            InlineQueryResultArticle(
                id=f"1_{i}",  # Уникальный идентификатор результата
                title=f"📅 Расписание на неделю (часть {i + 1})",
                input_message_content=InputTextMessageContent(
                    message_text=part
                ),
                description="Нажмите, чтобы отправить расписание в чат.",
            )
        )
    for i, part in enumerate(day_parts):
        results.append(
            InlineQueryResultArticle(
                id=f"2_{i}",  # Уникальный идентификатор результата
                title=f"📅 Сегодня (часть {i + 1})",
                input_message_content=InputTextMessageContent(
                    message_text=part
                ),
                description="Нажмите, чтобы отправить расписание в чат.",
            )
        )

    # Отправляем результат
    await query.answer(results, cache_time=1, is_personal=True)