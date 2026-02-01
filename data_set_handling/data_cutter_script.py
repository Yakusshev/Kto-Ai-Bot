import json
import argparse
import sys
import os

INPUT_FILE = "data-set-scratch/ksusha.json"
OUTPUT_FILE = "data-set-prod/ksusha.jsonl"

def create_training_pairs(messages):
    """
    Генератор, который возвращает пары (история, ответ) для каждого сообщения ассистента.
    """
    for i, msg in enumerate(messages):
        # Нас интересуют только ответы ассистента
        if msg.get('role') == 'assistant':
            response_text = msg.get('text', '')

            # История — это все сообщения ДО текущего
            request_list = messages[:i]

            # Если истории нет (ассистент начал первым), пропускаем или обрабатываем по желанию.
            # Обычно для обучения нужен контекст от user, поэтому пропускаем пустые.
            if not request_list:
                continue

            yield {
                "request": request_list,
                "response": response_text
            }


def load_and_normalize_json(filepath):
    """
    Загружает JSON и приводит его к единому формату (список сообщений).
    """
    with open(filepath, 'r', encoding = 'utf-8') as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"Ошибка: Файл '{filepath}' не является валидным JSON.\nДетали: {e}")
            sys.exit(1)

    # Вариант 1: Формат из твоего примера (request + response)
    if isinstance(data, dict) and 'request' in data and 'response' in data:
        # Объединяем в одну линию времени
        full_messages = data['request'] + [{"role": "assistant", "text": data['response']}]
        return full_messages

    # Вариант 2: Просто список сообщений (стандартный формат диалогов)
    elif isinstance(data, list):
        return data

    # Вариант 3: Если это словарь, но только с ключом request (незаконченный диалог)
    elif isinstance(data, dict) and 'request' in data:
        return data['request']

    else:
        print("Ошибка: Непонятная структура JSON. Ожидался список сообщений или объект с ключами 'request'/'response'.")
        sys.exit(1)


def main():
    # Настройка аргументов командной строки
    parser = argparse.ArgumentParser(description = "Нарезка истории чата JSON в датасет для обучения (JSONL).")

    if not os.path.exists(INPUT_FILE):
        print(f"Ошибка: Файл '{INPUT_FILE}' не найден.")
        sys.exit(1)

    # Определение имени выходного файла
    if OUTPUT_FILE:
        output_file = OUTPUT_FILE
    else:
        # Если выходной файл не указан, меняем расширение входного на .jsonl
        base, _ = os.path.splitext(INPUT_FILE)
        output_file = f"{base}.jsonl"

    # 1. Загрузка и нормализация
    messages = load_and_normalize_json(INPUT_FILE)

    # 2. Обработка и запись
    count = 0
    try:
        with open(output_file, 'w', encoding = 'utf-8') as f_out:
            for pair in create_training_pairs(messages):
                # Записываем одну строку JSONL
                json_line = json.dumps(pair, ensure_ascii = False)
                f_out.write(json_line + '\n')
                count += 1

        print(f"Готово! Обработано пар: {count}.")
        print(f"Результат сохранен в: {output_file}")

    except IOError as e:
        print(f"Ошибка при записи файла: {e}")


if __name__ == "__main__":
    main()