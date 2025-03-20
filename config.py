# config.py

from dotenv import load_dotenv
import os

# Загружаем переменные из .env
load_dotenv()

# Токен вашего бота
TOKEN = os.getenv("TOKEN")  # Получаем значение переменной TOKEN из .env

# Часовой пояс (например, для Москвы)
MOSCOW_TZ = "Europe/Moscow"