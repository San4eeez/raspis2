# handlers.py

from aiogram import Router, types
from aiogram.filters import Command, CommandObject
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
)
from aiogram.utils.markdown import code
from datetime import datetime
from models import GROUPS, TEACHERS
from services import fetch_schedule
import json

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


@router.message(Command("start"))
async def start(message: Message):
    """Обработчик команды /start."""
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
        [KeyboardButton(text="📌 Расписание на сегодня")],
        [KeyboardButton(text="📅 Ближайшее расписание")],
        [KeyboardButton(text="🔄 Сменить группу")],
        [KeyboardButton(text="👨‍🏫 Найти преподавателя")]
    ])
    await message.answer("Привет! Выбери нужную опцию:", reply_markup=keyboard)


@router.message()
async def button_handler(message: Message, command: CommandObject = None):
    """Обработчик кнопок и команд с упоминанием бота."""
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
    elif command_text == "📅 Ближайшее расписание" or command_text == "расписание":
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
    await message.answer(code(message_text), parse_mode="MarkdownV2")


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
        await callback.message.answer(code(message_text), parse_mode="MarkdownV2")
    await callback.answer()


@router.inline_query()
async def inline_query_handler(inline_query: InlineQuery):
    """Обработчик инлайн-запросов."""
    # Варианты команд для инлайн-режима
    commands = [
        {"title": "📌 Расписание на сегодня", "description": "Показать расписание на сегодня", "command": "сегодня"},
        {"title": "📅 Ближайшее расписание", "description": "Показать ближайшее расписание", "command": "расписание"},
        {"title": "🔄 Сменить группу", "description": "Изменить выбранную группу", "command": "сменить_группу"},
        {"title": "👨‍🏫 Найти преподавателя", "description": "Найти преподавателя", "command": "преподаватель"},
    ]

    # Создаем список результатов для инлайн-режима
    results = [
        InlineQueryResultArticle(
            id=str(index),
            title=cmd["title"],
            description=cmd["description"],
            input_message_content=InputTextMessageContent(
                message_text=f"@{inline_query.bot.username} {cmd['command']}"
            ),
        )
        for index, cmd in enumerate(commands)
    ]

    # Отправляем результаты
    await inline_query.answer(results, cache_time=1)