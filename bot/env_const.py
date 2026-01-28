import os

# 1. Загружаем переменные окружения в самом начале
from dotenv import load_dotenv

load_dotenv()

YANDEX_FOLDER_ID = os.getenv("YANDEX_FOLDER_ID")
YANDEX_API_KEY = os.getenv("YANDEX_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("BOT_TOKEN")