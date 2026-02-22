import os
from multiprocessing.util import DEBUG

# 1. Загружаем переменные окружения в самом начале
from dotenv import load_dotenv

load_dotenv()

YANDEX_FOLDER_ID = os.getenv("YANDEX_FOLDER_ID")
YANDEX_API_KEY = os.getenv("YANDEX_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("BOT_TOKEN")
YDB_ENDPOINT = os.getenv("YDB_ENDPOINT")
YDB_PATH = os.getenv("YDB_PATH")
YDB_AUTH_KEY_FILE = os.getenv("YDB_AUTH_KEY_FILE")
DEBUG_MODE = os.getenv("DEBUG_MODE") == "True"