import os

# 1. Загружаем переменные окружения в самом начале
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN_DEBUG = os.getenv("BOT_TOKEN")
TELEGRAM_BOT_TOKEN_RELEASE = os.getenv("BOT_TOKEN_RELEASE")
TELEGRAM_BOT_TOKEN_ADMIN = os.getenv("BOT_TOKEN_ADMIN")
TELEGRAM_BOT_TOKEN_ADMIN_RELEASE = os.getenv("BOT_TOKEN_ADMIN_RELEASE")

YANDEX_FOLDER_ID = os.getenv("YANDEX_FOLDER_ID")
YANDEX_API_KEY = os.getenv("YANDEX_API_KEY")
YDB_ENDPOINT = os.getenv("YDB_ENDPOINT")
YDB_PATH = os.getenv("YDB_PATH")
YDB_AUTH_KEY_FILE = os.getenv("YDB_AUTH_KEY_FILE")
DEBUG_MODE_TYPING = os.getenv("DEBUG_MODE_TYPING") == "True"
DEBUG_MODE_START_POLLING = os.getenv("DEBUG_MODE_START_POLLING") == "True"
DEBUG_MODE_LOGGING = os.getenv("DEBUG_MODE_LOGGING") == "True"
DEBUG_MODE_TOKEN = os.getenv("DEBUG_MODE_TOKEN") == "True"
DEBUG_MODE_DATABASE = os.getenv("DEBUG_MODE_DATABASE") == "True"

NEXT_MESSAGE_SEPARATOR = os.getenv("NEXT_MESSAGE_SEPARATOR") == "True"
NEXT_MESSAGE_SEPARATOR_REGEX = os.getenv("NEXT_MESSAGE_SEPARATOR_REGEX") == "True"

ADMIN_ID_LIST = list(map(int, os.getenv("ADMIN_ID_LIST", "").split(",")))
OWN_CHANNEL_ID = int(os.getenv("OWN_CHANNEL_ID"))
OWN_CHAT_ID = int(os.getenv("OWN_CHAT_ID"))
