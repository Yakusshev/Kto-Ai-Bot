# Запустите этот скрипт
import beartype
import site
import os

def main():
    print("Путь к beartype:", beartype.__file__)
    print("\nПути site-packages:")
    for path in site.getsitepackages():
        print(path)
        # Ищем кэш beartype
        beartype_cache = os.path.join(path, "beartype", "__pycache__")
        if os.path.exists(beartype_cache):
            print(f"  Найден кэш: {beartype_cache}")

# важно, чтобы в многострочном тексте не было строк, начинающихся с "[" - это ломает
# ftl
if __name__ == "__main__":
    main()
