#!/bin/bash

# --- Скрипт для запуска бота из папки релиза ---

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
cd "$SCRIPT_DIR"

if [ ! -d "venv_release" ]; then
    echo "INFO: Virtual environment not found. Creating one..."
    python3 -m venv venv_release
    echo "INFO: Installing dependencies..."
    ./venv_release/bin/pip install -r requirements.lock
    echo "INFO: Setup complete."
fi

echo "INFO: Starting bot..."
./venv_release/bin/python main.py
