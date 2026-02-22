#!/bin/bash

# --- Профессиональный сборочный скрипт v2 ---

# 1. Создаем или очищаем папку релиза
echo "INFO: Creating release directory..."
rm -rf release
mkdir release

# 2. Создаем точный lock-файл с помощью pip-tools
echo "INFO: Compiling dependencies into requirements.lock..."
# Активируем виртуальное окружение, чтобы использовать его библиотеки
source .venv/bin/activate
# Используем pip-compile для создания полного и точного lock-файла из requirements.txt
pip-compile requirements.txt -o requirements.lock --strip-extras

# 3. Копируем все необходимые файлы
echo "INFO: Copying project files..."
cp -R bot release/
cp main.py release/
cp requirements.lock release/
cp .env release/
# Копируем ключ, только если он существует
if [ -f "serviceAccountKey.json" ]; then
    cp serviceAccountKey.json release/
fi

# 4. Удаляем временный lock-файл из корневой папки
rm requirements.lock

# 5. Настраиваем .env для релиза (устанавливаем DEBUG_MODE=False)
echo "INFO: Configuring .env for production..."
RELEASE_ENV_FILE="release/.env"
if grep -q "^DEBUG_MODE=" "$RELEASE_ENV_FILE"; then
    # Если строка есть, заменяем ее
    sed -i '' 's/^DEBUG_MODE=.*/DEBUG_MODE=False/' "$RELEASE_ENV_FILE"
else
    # Если строки нет, добавляем ее в конец
    echo -e "\n# Production settings\nDEBUG_MODE=False" >> "$RELEASE_ENV_FILE"
fi
echo "INFO: DEBUG_MODE set to False in release/.env"

# 6. Создаем скрипт запуска внутри папки релиза
echo "INFO: Creating run script in release/run.sh..."
cat << 'EOF' > release/run.sh
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
EOF

# 7. Делаем созданный run.sh исполняемым
chmod +x release/run.sh

echo "SUCCESS: Build complete!"
echo "To run the bot, execute from project root: ./release/run.sh"