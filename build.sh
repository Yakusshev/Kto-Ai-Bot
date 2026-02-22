#!/bin/bash

# --- Финальный сборочный скрипт ---

# 1. Создаем или очищаем папку релиза
echo "INFO: Creating release directory..."
rm -rf release
mkdir release

# 2. Создаем точный lock-файл с помощью pip-tools
echo "INFO: Compiling dependencies into requirements.lock..."
source .venv/bin/activate
pip-compile requirements.txt -o requirements.lock --strip-extras

# 3. Копируем все необходимые файлы
echo "INFO: Copying project files..."
cp -R bot release/
cp main.py release/
cp requirements.lock release/
cp .env release/

# --- НОВЫЙ БЛОК: Копируем папку с ключами ---
if [ -d "credentials" ]; then
    echo "INFO: Copying credentials directory..."
    cp -R credentials release/
else
    echo "WARNING: 'credentials' directory not found. If you use services requiring keys, the build may not work."
fi
# --- КОНЕЦ НОВОГО БЛОКА ---

# 4. Удаляем временный lock-файл
rm requirements.lock

# 5. Настраиваем .env для релиза (устанавливаем DEBUG_MODE=False)
echo "INFO: Configuring .env for production..."
RELEASE_ENV_FILE="release/.env"
if grep -q "^DEBUG_MODE=" "$RELEASE_ENV_FILE"; then
    sed -i '' 's/^DEBUG_MODE=.*/DEBUG_MODE=False/' "$RELEASE_ENV_FILE"
else
    echo -e "\n# Production settings\nDEBUG_MODE=False" >> "$RELEASE_ENV_FILE"
fi
echo "INFO: DEBUG_MODE set to False in release/.env"

# 6. Создаем скрипт запуска
echo "INFO: Creating run script in release/run.sh..."
cat << 'EOF' > release/run.sh
#!/bin/bash
# --- Скрипт для запуска бота из папки релиза ---

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
cd "$SCRIPT_DIR"

if [ ! -d "venv_release" ]; then
    echo "INFO: Virtual environment not found. Creating one..."
    python3 -m venv venv_release
    echo "INFO: Installing dependencies from lock file..."
    ./venv_release/bin/pip install -r requirements.lock
    echo "INFO: Setup complete."
fi

echo "INFO: Starting bot..."
./venv_release/bin/python main.py
EOF

# 7. Делаем run.sh исполняемым
chmod +x release/run.sh

echo "SUCCESS: Build complete!"
echo "To run the bot, execute from project root: ./release/run.sh"