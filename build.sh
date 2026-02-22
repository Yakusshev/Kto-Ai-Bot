#!/bin/bash

# --- Сборочный скрипт для Telegram-бота ---

# 1. Создаем или очищаем папку релиза
echo "INFO: Creating release directory..."
rm -rf release
mkdir release

# 2. Создаем точный lock-файл зависимостей
echo "INFO: Freezing dependencies into requirements.lock..."
# Активируем виртуальное окружение, чтобы получить правильные зависимости
source .venv/bin/activate
pip freeze > requirements.lock

# 3. Копируем все необходимые файлы в папку релиза
echo "INFO: Copying project files..."
# Копируем весь код приложения
cp -R bot release/
# Копируем основной скрипт
cp main.py release/
# Копируем lock-файл
cp requirements.lock release/
# Копируем файлы конфигурации
cp .env release/
cp serviceAccountKey.json release/

# 4. Удаляем временный lock-файл из основной папки проекта
rm requirements.lock

echo "SUCCESS: Build complete! Your release is in the 'release' folder."
echo "To run it, navigate to 'release' folder and follow the launch instructions."