import os

def anyaSystemInstruction():
    # Определяем путь к файлу относительно текущего файла
    # __file__ -> /path/to/your/project/bot/domain/DefaultSystemInstuction.py
    # os.path.dirname(__file__) -> /path/to/your/project/bot/domain
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Строим путь к файлу с инструкцией
    # ../resource/string/default_system_instruction.txt
    file_path = os.path.join(current_dir, '..', 'resource', 'string', 'default_system_instruction.txt')

    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read().strip()
