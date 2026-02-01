import json
import random
from pathlib import Path

# ===== НАСТРОЙКИ =====
INPUT_FOLDER = "data-set-prod-system-prompt"  # Папка с обработанными файлами
TRAIN_FILE = "data-set-prod-v3-validation/train-v3.jsonl"  # Выходной файл для обучения
VAL_FILE = "data-set-prod-v3-validation/validation-v3.jsonl"  # Выходной файл для валидации
VAL_SPLIT = 0.1  # 10% на валидацию
SEED = 42  # Для воспроизводимости


def load_all_data(input_folder):
    """
    Загружает все данные из всех JSON/JSONL файлов в папке
    """
    input_dir = Path(input_folder)

    if not input_dir.exists():
        print(f"❌ Папка {input_folder} не найдена!")
        return []

    # Получаем все JSON файлы
    json_files = list(input_dir.glob("*.json")) + list(input_dir.glob("*.jsonl"))

    if not json_files:
        print(f"❌ В папке {input_folder} не найдено JSON-файлов!")
        return []

    print(f"🔍 Найдено файлов: {len(json_files)}\n")

    all_data = []

    # Читаем каждый файл
    for json_file in json_files:
        print(f"📖 Читаю: {json_file.name}")

        try:
            with open(json_file, 'r', encoding = 'utf-8') as f:
                file_data = []
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue

                    try:
                        data = json.loads(line)
                        file_data.append(data)
                    except json.JSONDecodeError as e:
                        print(f"   ⚠️  Ошибка в строке {line_num}: {str(e)[:50]}")
                        continue

                all_data.extend(file_data)
                print(f"   ✓ Загружено примеров: {len(file_data)}")

        except Exception as e:
            print(f"   ❌ Ошибка чтения файла: {e}")
            continue

    print(f"\n{'=' * 50}")
    print(f"📊 Всего загружено примеров: {len(all_data)}")

    return all_data


def split_and_save(data, train_file, val_file, val_split, seed):
    """
    Разбивает данные на train/validation и сохраняет
    """
    if not data:
        print("❌ Нет данных для разбиения!")
        return

    # Перемешиваем
    random.seed(seed)
    random.shuffle(data)

    # Разбиваем
    val_size = int(len(data) * val_split)

    if val_size == 0:
        print(f"⚠️  Слишком мало данных для валидации ({len(data)} примеров)")
        print(f"   Минимум нужно {int(1 / val_split)} примеров для {int(val_split * 100)}% валидации")
        val_size = 1  # Хотя бы 1 пример

    val_data = data[:val_size]
    train_data = data[val_size:]

    # Сохраняем train
    with open(train_file, 'w', encoding = 'utf-8') as f:
        for item in train_data:
            f.write(json.dumps(item, ensure_ascii = False) + '\n')

    # Сохраняем validation
    with open(val_file, 'w', encoding = 'utf-8') as f:
        for item in val_data:
            f.write(json.dumps(item, ensure_ascii = False) + '\n')

    print(f"\n{'=' * 50}")
    print(f"✅ Разбиение завершено!")
    print(f"📝 Train: {len(train_data)} примеров → {train_file}")
    print(f"📝 Validation: {len(val_data)} примеров → {val_file}")
    print(f"📊 Соотношение: {(1 - val_split) * 100:.0f}% / {val_split * 100:.0f}%")


def main():
    """
    Основная функция
    """
    print("🚀 Начинаю разбиение данных на train/validation\n")

    # Загружаем все данные
    all_data = load_all_data(INPUT_FOLDER)

    if not all_data:
        return

    # Разбиваем и сохраняем
    split_and_save(all_data, TRAIN_FILE, VAL_FILE, VAL_SPLIT, SEED)

    print("\n✨ Готово! Можно использовать для обучения.")


if __name__ == "__main__":
    main()