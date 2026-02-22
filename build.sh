#!/bin/bash

# --- Профессиональный сборочный скрипт ---

# 1. Создаем или очищаем папку релиза
echo "INFO: Creating release directory..."
rm -rf release
mkdir release

# 2. Создаем точный lock-файл зависимостей
echo "INFO: Freezing dependencies..."
source .venv/bin/activate
pip freeze > requirements.lock

# 3. Копируем все необходимые файлы
echo "INFO: Copying project files..."
cp -R bot release/
cp main.py release/
cp requirements.lock release/
cp .env release/
cp serviceAccountKey.json release/

# 4. Удаляем временный lock-файл
rm requirements.lock

# 5. --- НОВЫЙ ШАГ: Настраиваем .env для релиза ---
echo "INFO: Configuring .env for production..."
# Путь к .env файлу в папке релиза
RELEASE_ENV_FILE="release/.env"

# Проверяем, существует ли уже строка DEBUG_MODE
if grep -q "^DEBUG_MODE=" "$RELEASE_ENV_FILE"; then
    # Если да, заменяем ее значение на False
    sed -i '' 's/^DEBUG_MODE=.*/DEBUG_MODE=False/' "$RELEASE_ENV_FILE"
else
    # Если нет, добавляем строку в конец файла
    echo -e "\n# Production settings\nDEBUG_MODE=False" >> "$RELEASE_ENV_FILE"
fi
echo "INFO: DEBUG_MODE set to False in release/.env"


# 6. Создаем скрипт запуска внутри папки release
echo "INFO: Creating run script in release/run.sh..."
cat << 'EOF' > release/run.sh
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
EOF

# 7. Делаем созданный run.sh исполняемым
chmod +x release/run.sh

echo "SUCCESS: Build complete!"
echo "To run the bot, execute: ./release/run.sh"