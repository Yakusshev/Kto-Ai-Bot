import json
import argparse
import sys
import os
import re  # Добавили для работы с регулярками

INPUT_FILE = "data-set-scratch/ksusha.json"
OUTPUT_FILE = "data-set-prod/ksusha.jsonl"


def clean_timestamp(text):
    """
    Удаляет метку времени формата [Time: ...] из начала строки.
    Использует безопасный regex, чтобы не задеть другие данные в квадратных скобках.
    """
    if not isinstance(text, str):
        return text
    # Ищем [Time: ...], затем любые символы до закрывающей скобки, затем возможный пробел
    return re.sub(r'\[Time: [^\]]+\]\s*', '', text)


def merge_consecutive_messages(messages):
    """
    Объединяет последовательные сообщения от одного и того же автора.
    Тексты склеиваются через \n.
    """
    if not messages:
        return []

    merged = []
    # Берем первое сообщение
    current_msg = messages[0].copy()

    # Сразу чистим первое сообщение, если это ассистент
    if current_msg.get('role') == 'assistant':
        current_msg['text'] = clean_timestamp(current_msg.get('text', ''))

    for i in range(1, len(messages)):
        next_msg = messages[i].copy()

        # Если это ассистент, чистим текст от времени ПЕРЕД склейкой
        if next_msg.get('role') == 'assistant':
            next_msg['text'] = clean_timestamp(next_msg.get('text', ''))

        # Если роль совпадает — склеиваем
        if next_msg.get('role') == current_msg.get('role'):
            current_msg['text'] += "\n" + next_msg.get('text', '')
        else:
            # Роль сменилась — сохраняем накопленное и начинаем новое
            merged.append(current_msg)
            current_msg = next_msg

    merged.append(current_msg)
    return merged


def create_training_pairs(messages):
    """
    Генератор пар (история -> ответ).
    """
    for i, msg in enumerate(messages):
        if msg.get('role') == 'assistant':
            response_text = msg.get('text', '')

            # История — все сообщения ДО текущего ответа
            request_list = messages[:i]

            if not request_list:
                continue

            yield {
                "request": request_list,
                "response": response_text
            }


def load_and_normalize_json(filepath):
    """
    Загружает JSON и приводит к плоскому списку сообщений.
    """
    with open(filepath, 'r', encoding = 'utf-8') as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"Ошибка: Файл '{filepath}' не является валидным JSON.\nДетали: {e}")
            sys.exit(1)

    if isinstance(data, dict) and 'request' in data and 'response' in data:
        full_messages = data['request'] + [{"role": "assistant", "text": data['response']}]
        return full_messages
    elif isinstance(data, list):
        return data
    elif isinstance(data, dict) and 'request' in data:
        return data['request']
    else:
        print("Ошибка: Непонятная структура JSON.")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description = "Подготовка датасета: склейка сообщений и удаление времени у ассистента.")
    args, unknown = parser.parse_known_args()

    if not os.path.exists(INPUT_FILE):
        print(f"Ошибка: Файл '{INPUT_FILE}' не найден.")
        sys.exit(1)

    if OUTPUT_FILE:
        output_file = OUTPUT_FILE
    else:
        base, _ = os.path.splitext(INPUT_FILE)
        output_file = f"{base}.jsonl"

    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 1. Загрузка
    raw_messages = load_and_normalize_json(INPUT_FILE)

    # 2. Склейка + Очистка времени (встроена в функцию merge)
    messages = merge_consecutive_messages(raw_messages)

    # 3. Запись
    count = 0
    try:
        with open(output_file, 'w', encoding = 'utf-8') as f_out:
            for pair in create_training_pairs(messages):
                json_line = json.dumps(pair, ensure_ascii = False)
                f_out.write(json_line + '\n')
                count += 1

        print(f"Готово! Обработано пар: {count}.")
        print(f"Результат сохранен в: {output_file}")

    except IOError as e:
        print(f"Ошибка при записи файла: {e}")


if __name__ == "__main__":
    main()