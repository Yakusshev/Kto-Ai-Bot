import os

# 1. Загружаем переменные окружения в самом начале
from dotenv import load_dotenv

from bot.core.config.EnvReader import EnvReader

load_dotenv()

_reader = EnvReader(environ = os.environ)

DEBUG_MODE_TYPING = _reader.flag("DEBUG_MODE_TYPING")
DEBUG_MODE_START_POLLING = _reader.flag("DEBUG_MODE_START_POLLING")
DEBUG_MODE_LOGGING = _reader.flag("DEBUG_MODE_LOGGING")
DEBUG_MODE_TOKEN = _reader.flag("DEBUG_MODE_TOKEN")
DEBUG_MODE_DATABASE = _reader.flag("DEBUG_MODE_DATABASE")

# Обязательны только токены того режима, в котором запускается бот
if DEBUG_MODE_TOKEN:
    TELEGRAM_BOT_TOKEN_DEBUG = _reader.require_str("BOT_TOKEN")
    TELEGRAM_BOT_TOKEN_ADMIN = _reader.require_str("BOT_TOKEN_ADMIN")
    TELEGRAM_BOT_TOKEN_RELEASE = _reader.optional_str("BOT_TOKEN_RELEASE") or ""
    TELEGRAM_BOT_TOKEN_ADMIN_RELEASE = _reader.optional_str("BOT_TOKEN_ADMIN_RELEASE") or ""
else:
    TELEGRAM_BOT_TOKEN_DEBUG = _reader.optional_str("BOT_TOKEN") or ""
    TELEGRAM_BOT_TOKEN_ADMIN = _reader.optional_str("BOT_TOKEN_ADMIN") or ""
    TELEGRAM_BOT_TOKEN_RELEASE = _reader.require_str("BOT_TOKEN_RELEASE")
    TELEGRAM_BOT_TOKEN_ADMIN_RELEASE = _reader.require_str("BOT_TOKEN_ADMIN_RELEASE")

YANDEX_FOLDER_ID = _reader.optional_str("YANDEX_FOLDER_ID")
YANDEX_API_KEY = _reader.optional_str("YANDEX_API_KEY")
YDB_ENDPOINT = _reader.require_str("YDB_ENDPOINT")
YDB_PATH = _reader.require_str("YDB_PATH")
YDB_AUTH_KEY_FILE = _reader.optional_str("YDB_AUTH_KEY_FILE")

# Очередь отложенных шагов ответа: memory - в процессе (polling), sqs - Yandex Message Queue.
# Для memory SQS_* не нужны. Дефолт сменится на sqs, когда появится приёмник очереди (S2/S6/S8).
DELAYED_QUEUE_BACKEND = _reader.optional_choice(
    "DELAYED_QUEUE_BACKEND",
    allowed = ("memory", "sqs"),
    default = "memory",
)
SQS_ENDPOINT = _reader.optional_str("SQS_ENDPOINT") or "https://message-queue.api.cloud.yandex.net"
SQS_REGION = _reader.optional_str("SQS_REGION") or "ru-central1"
if DELAYED_QUEUE_BACKEND == "sqs":
    SQS_ACCESS_KEY_ID = _reader.require_str("SQS_ACCESS_KEY_ID")
    SQS_SECRET_ACCESS_KEY = _reader.require_str("SQS_SECRET_ACCESS_KEY")
    SQS_QUEUE_URL = _reader.require_str("SQS_QUEUE_URL")
else:
    SQS_ACCESS_KEY_ID = _reader.optional_str("SQS_ACCESS_KEY_ID") or ""
    SQS_SECRET_ACCESS_KEY = _reader.optional_str("SQS_SECRET_ACCESS_KEY") or ""
    SQS_QUEUE_URL = _reader.optional_str("SQS_QUEUE_URL") or ""

NEXT_MESSAGE_SEPARATOR = _reader.require_str("NEXT_MESSAGE_SEPARATOR")
NEXT_MESSAGE_SEPARATOR_REGEX = _reader.optional_str("NEXT_MESSAGE_SEPARATOR_REGEX")

ADMIN_ID_LIST = _reader.require_int_list("ADMIN_ID_LIST")
OWN_CHANNEL_ID = _reader.require_int("OWN_CHANNEL_ID")
OWN_CHAT_ID = _reader.require_int("OWN_CHAT_ID")

# Падаем сразу при импорте с перечнем всех проблем, а не на первом int(None)
_reader.validate()
