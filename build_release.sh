#!/bin/bash

# --- Профессиональный сборочный скрипт v3 ---

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
if [ -d "credentials" ]; then
    echo "INFO: Copying credentials directory..."
    cp -R credentials release/
else
    echo "WARNING: 'credentials' directory not found."
fi

# 4. Удаляем временный lock-файл
rm requirements.lock

# 5. --- ОБНОВЛЕННЫЙ ШАГ: Настраиваем .env для релиза ---
echo "INFO: Setting all DEBUG_MODE flags to False in release/.env..."
RELEASE_ENV_FILE="release/.env"

# Используем sed для поиска и замены ВСЕХ строк, начинающихся с "DEBUG_MODE"
# `g` в конце `s/.../.../g` означает "глобальная замена" на случай нескольких совпадений в одной строке (хотя здесь это маловероятно)
sed -i '' 's/^DEBUG_MODE.*/DEBUG_MODE=False/' "$RELEASE_ENV_FILE"

# Этот код заменит строки вида:
# DEBUG_MODE=True -> DEBUG_MODE=False
# DEBUG_MODE_DATABASE=True -> DEBUG_MODE=False
# DEBUG_MODE_API=some_value -> DEBUG_MODE=False
#
# Если вам нужно сохранять имена полей, а менять только значение, команда будет сложнее:
# sed -i '' 's/^\(DEBUG_MODE[^=]*=\).*/\1False/' "$RELEASE_ENV_FILE"
# Давайте пока остановимся на простом варианте, который вы описали.
# Если нужно будет усложнить, дайте знать.

echo "INFO: All DEBUG flags processed."


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