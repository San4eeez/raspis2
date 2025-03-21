import json
from datetime import date
from aiogram import Bot
from aiogram.types import FSInputFile

# Путь к файлу для сохранения аналитики
ANALYTICS_FILE = "analytics.json"

# Белый список администраторов
ADMIN_IDS = [806697034]  # Ваш ID

# Загружаем аналитику из файла (если файл существует)
try:
    with open(ANALYTICS_FILE, "r", encoding="utf-8") as file:
        analytics_data = json.load(file)
except FileNotFoundError:
    analytics_data = {
        "total_users": 0,  # Общее количество пользователей
        "daily_requests": {},  # Запросы по дням
        "user_requests": {}  # Запросы по пользователям
    }


def save_analytics():
    """Сохраняет аналитику в файл."""
    with open(ANALYTICS_FILE, "w", encoding="utf-8") as file:
        json.dump(analytics_data, file, ensure_ascii=False, indent=4)


def log_request(user_id: int, username: str):
    """Логирует запрос пользователя."""
    today = str(date.today())

    # Обновляем общее количество пользователей
    if str(user_id) not in analytics_data["user_requests"]:
        analytics_data["total_users"] += 1

    # Логируем запросы по пользователям
    if str(user_id) not in analytics_data["user_requests"]:
        analytics_data["user_requests"][str(user_id)] = {
            "username": username,
            "total_requests": 0,
            "daily_requests": {}
        }

    analytics_data["user_requests"][str(user_id)]["total_requests"] += 1

    if today not in analytics_data["user_requests"][str(user_id)]["daily_requests"]:
        analytics_data["user_requests"][str(user_id)]["daily_requests"][today] = 0
    analytics_data["user_requests"][str(user_id)]["daily_requests"][today] += 1

    # Логируем запросы по дням
    if today not in analytics_data["daily_requests"]:
        analytics_data["daily_requests"][today] = 0
    analytics_data["daily_requests"][today] += 1

    # Сохраняем изменения в файл
    save_analytics()


async def send_analytics(bot: Bot, chat_id: int):
    """Отправляет аналитику администратору."""
    if chat_id not in ADMIN_IDS:
        await bot.send_message(chat_id, "У вас нет доступа к этой команде.")
        return

    # Формируем сообщение с аналитикой
    message = "📊 Аналитика использования бота:\n\n"
    message += f"👥 Общее количество пользователей: {analytics_data['total_users']}\n\n"

    # Запросы по дням
    message += "📅 Запросы по дням:\n"
    for day, count in analytics_data["daily_requests"].items():
        message += f"{day}: {count} запросов\n"

    # Запросы по пользователям
    message += "\n👤 Запросы по пользователям:\n"
    for user_id, data in analytics_data["user_requests"].items():
        message += f"Пользователь {data['username']} (ID: {user_id}):\n"
        message += f"Всего запросов: {data['total_requests']}\n"
        message += "Запросы по дням:\n"
        for day, count in data["daily_requests"].items():
            message += f"{day}: {count} запросов\n"
        message += "\n"

    # Отправляем сообщение
    await bot.send_message(chat_id, message)

    # Отправляем файл user_groups.json
    file = FSInputFile("user_groups.json")
    await bot.send_document(chat_id, file, caption="Файл user_groups.json")