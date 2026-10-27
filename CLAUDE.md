# Kto-Ai-Bot

Telegram-бот на Python (aiogram, YDB, LLM). Код в `bot/`, тесты в `test/`, точка входа `main.py`.

## Структура и слои

```
bot/core/            общий код: config, di, entry, domain (константы, форматирование)
bot/util/            общие утилиты
bot/resource/        локали и Strings.py (генерируется, руками не править)
bot/feature/<имя>/
    entrypoint/      хендлеры aiogram, сервисы, фильтры
    data/            репозитории, datasource, YDB, внешние API
    domain/          usecase, scenario, model, интерфейсы репозиториев
    di/              сборка зависимостей (middleware, провайдеры)
```

Правила (проверяются машиной):

- `domain` ничего не знает об инфраструктуре (`aiogram`, `ydb`, `openai`, `boto3`, ...), а также о `data` и `entrypoint`.
- Зависимости слоёв внутри фичи: `entrypoint` -> `data` -> `domain` (обратных нет).
- `*.data` импортируется только из `di` и `main.py`; `entrypoint`, `domain`, `core` работают через интерфейсы из `domain`.
- `data` и `entrypoint` чужой фичи недоступны (только через `domain` или `di`).
- Файлы не длиннее 500 строк.

Новый код: фича в `bot/feature/<имя>/{entrypoint,domain,data,di}`; общее для всех фич - в `bot/core`.
Новая фича = добавить контейнер в контракт `feature-layers` и контракт `<имя>-isolated` в `.importlinter`.

## Проверки и запуск

Зависимости: `pip install -r requirements-dev.txt` (инструменты не входят в прод-образ).

| Что ловит | Команда | Конфиг |
|---|---|---|
| Нарушения слоёв | `lint-imports` | `.importlinter` |
| Длина файлов | `python -m pytest test/architecture` | `test/architecture/FileLengthTest.py` |
| Сложность, число аргументов, запрещённые API | `ruff check .` | `pyproject.toml` |
| Типы | `mypy` | `mypy.ini` |
| Юнит-тесты | `python -m pytest test` | `pytest.ini` |

Всё то же самое выполняет CI (`.github/workflows/ci.yml`, отдельные обязательные джобы), он же гейт деплоя.
Хук Stop (`.claude/hooks/architecture-check.sh`) запускает `lint-imports` и тесты архитектуры и не даёт
завершить работу при нарушении; без установленных зависимостей молча выходит.

## Baseline существующих нарушений

`ignore_imports` в `.importlinter`, `per-file-ignores` в `pyproject.toml`, секции `[mypy-...]` в `mypy.ini`,
`LEGACY_LIMITS` в тесте длины. Только сокращать: исправили нарушение - удалите запись; новые записи не добавлять.

## Стиль

- `ruff format` не запускать: по правилу yak-python-code-style каждый параметр на отдельной строке при более чем одном аргументе.
- Тексты пользователю - в `bot/resource/locales/ru/messages.ftl`, `Strings.py` перегенерировать (`bot/resource/GenerateStrings.py`).
