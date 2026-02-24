import os
from multiprocessing.util import DEBUG

# 1. Загружаем переменные окружения в самом начале
from dotenv import load_dotenv

load_dotenv()

YANDEX_FOLDER_ID = os.getenv("YANDEX_FOLDER_ID")
YANDEX_API_KEY = os.getenv("YANDEX_API_KEY")
TELEGRAM_BOT_TOKEN_DEBUG = os.getenv("BOT_TOKEN")
TELEGRAM_BOT_TOKEN_RELEASE = os.getenv("BOT_TOKEN_RELEASE")
YDB_ENDPOINT = os.getenv("YDB_ENDPOINT")
YDB_PATH = os.getenv("YDB_PATH")
YDB_AUTH_KEY_FILE = os.getenv("YDB_AUTH_KEY_FILE")
DEBUG_MODE = os.getenv("DEBUG_MODE") == "True"
DEBUG_MODE_TOKEN = os.getenv("DEBUG_MODE_TOKEN") == "True"
DEBUG_MODE_DATABASE = os.getenv("DEBUG_MODE_DATABASE") == "True"