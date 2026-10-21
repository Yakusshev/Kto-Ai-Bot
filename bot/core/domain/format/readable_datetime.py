from datetime import datetime

# Названия дней недели заданы в коде, а не берутся из системной локали:
# в образе python:3.11-slim локали ru_RU нет, а setlocale глобален для процесса.
# Порядок соответствует datetime.weekday(): 0 — понедельник
WEEKDAY_NAMES = (
    "Понедельник",
    "Вторник",
    "Среда",
    "Четверг",
    "Пятница",
    "Суббота",
    "Воскресенье",
)

DATE_FORMAT = "%Y-%m-%d"
TIME_FORMAT = "%H:%M"


def format_readable_datetime(value: datetime) -> str:
    """Форматирует дату как «2025-01-06 Понедельник 14:30» без системной локали."""
    date_part = value.strftime(DATE_FORMAT)
    weekday = WEEKDAY_NAMES[value.weekday()]
    time_part = value.strftime(TIME_FORMAT)

    return f"{date_part} {weekday} {time_part}"
