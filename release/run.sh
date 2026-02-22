#!/bin/bash
# --- Скрипт для запуска бота из папки релиза ---

# Определяем директорию, где лежит сам скрипт, и переходим в нее
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
cd "$SCRIPT_DIR"

# Проверяем, было ли уже создано виртуальное окружение
if [ ! -d "venv_release" ]; then
    echo "INFO: Virtual environment not found. Creating one..."
    python3 -m venv venv_release
    echo "INFO: Installing dependencies from lock file..."
    # Устанавливаем зависимости, используя pip из нового окружения
    ./venv_release/bin/pip install -r requirements.lock
    echo "INFO: Setup complete."
fi

# Запускаем бота, используя python из нашего окружения
echo "INFO: Starting bot..."
./venv_release/bin/python main.py
