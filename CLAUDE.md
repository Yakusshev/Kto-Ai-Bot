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
    di/              провайдеры dishka (<Фича>Provider.py)
```

Правила (проверяются машиной):

- `domain` ничего не знает об инфраструктуре (`aiogram`, `ydb`, `openai`, `boto3`, ...), а также о `data` и `entrypoint`.
- Зависимости слоёв внутри фичи: `entrypoint` -> `data` -> `domain` (обратных нет).
- `*.data` импортируется только из `di` и `main.py`; `entrypoint`, `domain`, `core` работают через интерфейсы из `domain`.
- `data` и `entrypoint` чужой фичи недоступны (только через `domain` или `di`).
- Файлы не длиннее 500 строк.

Новый код: фича в `bot/feature/<имя>/{entrypoint,domain,data,di}`; общее для всех фич - в `bot/core`.
Новая фича = добавить контейнер в контракт `feature-layers` и контракт `<имя>-isolated` в `.importlinter`.

## DI: где добавить зависимость

DI на dishka, контейнер не привязан к aiogram: `bot/core/di/container.py` (`create_container`) - единственное место сборки.

- Новый класс (репозиторий, use case, сервис): добавить в `provide_all(...)` провайдера своей фичи, `bot/feature/<фича>/di/<Фича>Provider.py`. Зависимости берутся из типов `__init__`.
- Scope: APP - YDB, репозитории, клиенты, состояние приложения; REQUEST - всё, что зависит от Strings/апдейта. Не клади в REQUEST финализаторы: фоновые задачи живут дольше апдейта.
- Общее для всех фич (YDB driver/pool, Strings) - `bot/core/di/CoreProvider.py`. Провайдеры фич друг друга не импортируют: нужный тип чужой фичи просто указывается в `__init__`.
- Хендлер получает зависимость как `x: FromDishka[Тип]` (auto_inject включён в `main.py` для обоих диспетчеров). Вне aiogram: `create_container(StandaloneI18nProvider())`, затем `async with container() as request: await request.get(ChatService)`.
- Тесты: подменять внешние границы провайдером с `provide(override = True)`, образец - `test/core/di/ContainerTest.py`.

## Ответ бота: отложенные шаги

Ответ состоит из шагов «прочитать -> печатает -> сгенерировать и отправить» (`business/domain/usecase/*StepUseCase`, диспетчер `HandleChatStepUseCase`).
Шаги ставятся в `DelayedTaskQueue` (порт в domain; адаптеры `business/data/queue`: `InMemory` и `Sqs`, выбор - `DELAYED_QUEUE_BACKEND`, по умолчанию memory).
Каждый шаг сверяет талон `StepTicket` (S1) и тихо завершается, если он устарел; `asyncio.Task.cancel` для отмены не используется. Паузы - `HumanDelays` (DEBUG_MODE_TYPING = 0).
Вход: `ProcessChatEventUseCase` (хендлеры, `ReminderService`). Приёмник сообщений SQS (S2/S6) должен вызвать `HandleChatStepUseCase.invoke(ChatStepPayload.from_json(body))`.

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
