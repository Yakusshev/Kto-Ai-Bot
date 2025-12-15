# Используем легкий образ Python 3.11 (или 3.12, смотря что у тебя)
FROM python:3.11-slim

# Отключаем создание .pyc файлов и буферизацию вывода (чтобы логи виделись сразу)
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Рабочая папка внутри контейнера
WORKDIR /app

# Копируем файл зависимостей и устанавливаем их
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь остальной код проекта
COPY . .

# Команда запуска бота
CMD ["python", "main.py"]