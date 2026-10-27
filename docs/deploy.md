# Выкладка: тестовые боты → прод

Бот работает на VM в Yandex Cloud (инфраструктура — `infra/README.md`). Есть два окружения:

| Окружение | VM / registry / Lockbox | Боты | Как попадает код |
|---|---|---|---|
| `test` | `kto-ai-bot-test` | тестовые (`BOT_TOKEN`, `BOT_TOKEN_ADMIN`) | автоматически на push в `sprint*` и `main` |
| `prod` | `kto-ai-bot-prod` | боевые (`BOT_TOKEN_RELEASE`, `BOT_TOKEN_ADMIN_RELEASE`) | только вручную, с подтверждением reviewer'а |

## Как это устроено

Два workflow в `.github/workflows/`:

- **CI** (`ci.yml`) — на каждый PR и push в рабочие ветки, все джобы обязательные: `pytest test`,
  `lint-imports` (контракты слоёв, `.importlinter`), `ruff` (`pyproject.toml`), тесты архитектуры
  (`test/architecture`), `mypy` (весь проект, `mypy.ini`), `docker build` без пуша и проверка,
  что зависимости в образе импортируются. Накопленные нарушения занесены в baseline
  (см. CLAUDE.md), новые блокируют PR.
- **Deploy** (`deploy.yml`):
  1. push в `sprint*` или `main` → CI → сборка образа `<image_repository>:<sha>` → push в
     Container Registry → замена тега в metadata `docker-compose` VM → проверка старта.
     Почему эти ветки: задачи спринта вливаются в `sprint<N>`. Её и гоняют на тестовых ботах,
     пока карточки в колонке «Тестирование». `main` получает спринт целиком в конце, и его
     коммит тоже проходит через test, прежде чем поехать в прод.
     Изменения только в `docs/`, `infra/`, `*.md`, `scratch/` выкладку не запускают.
     Пока репозиторная переменная `DEPLOY_TEST_ENABLED` не равна `true`, выкладка на push
     пропускается: CI проходит, а job deploy остаётся `skipped` с предупреждением.
  2. Run workflow (`workflow_dispatch`) → выбрать `environment` (`test`/`prod`) и `sha`.
     На test перед выкладкой тоже запускается CI для этого sha. Для prod job ждёт
     подтверждения в GitHub Environment `prod`.

Тег образа равен полному sha коммита. Если такой образ уже есть в registry (откат,
повторный запуск), сборка пропускается. Скрипты выкладки берутся из ветки запуска,
исходники образа — из выкладываемого коммита, поэтому откат на sha старше этого
workflow работает.

**Гейт prod: признак «прошёл test» хранится на образе.**

1. Выкладка на test заканчивается успешно (CI, выкладка, проверка старта).
2. CI ставит тег `tested-<sha>` на тот же digest в test-registry.
3. Выкладка в prod не собирает образ. Она проверяет, что `tested-<sha>` существует,
   копирует **этот digest** в prod-registry под тегом `<sha>` и сверяет digest.

Поэтому в prod уходит ровно то, что работало на тестовых ботах, и откат prod на любой
ранее проверенный sha работает. GitHub deployments для гейта не используются: их статусы
становятся `inactive` после следующей выкладки и пишутся на HEAD ветки, а не на
выложенный sha.

Если выкладываемый тег уже стоит на VM (повторный запуск, тот же sha из `main` после
`sprint*`), COI контейнер не пересоздаст. Тогда job перезапускает VM
(`yc compute instance restart`) и проверяет свежий старт: пропустить проверку нельзя.

**Проверка после выкладки** (`.github/scripts/verify-deploy.sh`) читает логи контейнера
из Cloud Logging начиная с момента выкладки. Выкладка успешна, если:

- в течение 7 минут появилась строка `Бот запущен, ожидаю SIGTERM/SIGINT…` (её пишет
  `main.py`, когда админ-бот запущен и YDB подключена);
- в следующие 60 секунд бот не стартовал повторно, то есть контейнер не перезапускается
  по кругу.

Если лаунчер не смог прочитать Lockbox (`lockbox-launcher: giving up`) или бот упал на проверке
конфигурации, job падает сразу. В лог CI попадают только служебные строки лаунчера и имена
отсутствующих переменных, но не переписка пользователей.

Serial port не подходит: вывод контейнеров COI идёт через драйвер fluentd в log group,
в serial-консоль он не попадает.

## Однократная настройка

### 1. Инфраструктура и секреты бота

По `infra/README.md` для каждого окружения: `make -C infra apply ENV=<env>`, затем заполнить
Lockbox (`make -C infra secrets ...`).

С D3 SA CI получает две роли:

- `logging.reader` **только на log group своего окружения**, поэтому ключ test-CI
  не читает боевую переписку, даже если окружения в одном каталоге;
- для prod — `container-registry.images.puller` на test-registry, чтобы копировать
  проверенный образ. Для этого в `infra/envs/prod.tfvars` задайте
  `promote_from_registry_id = "<infra/apply.sh test output -raw registry_id>"`.

Обе роли выдаются через `yc ... add-access-binding` из `terraform_data`: в провайдере нет
таких IAM-ресурсов. Если инфраструктура уже создана, выполните
`make -C infra apply ENV=test` и `make -C infra apply ENV=prod` ещё раз.

### 2. Ключ CI

Для каждого окружения выпустите отдельный ключ (Terraform его не создаёт):

```bash
yc iam key create --service-account-name kto-ai-bot-test-ci --output ci-key-test.json
yc iam key create --service-account-name kto-ai-bot-prod-ci --output ci-key-prod.json
```

### 3. GitHub Environments

Settings → Environments → создать `test` и `prod`.

| Где | Имя | Тип | Откуда значение |
|---|---|---|---|
| `test`, `prod` | `YC_SA_KEY` | secret | содержимое `ci-key-<env>.json` целиком |
| `test`, `prod` | `YC_IMAGE_REPOSITORY` | variable | `infra/apply.sh <env> output -raw image_repository` |
| `test`, `prod` | `YC_INSTANCE_ID` | variable | `infra/apply.sh <env> output -raw instance_id` |
| `test`, `prod` | `YC_LOG_GROUP_ID` | variable | `infra/apply.sh <env> output -raw log_group_id` |
| `prod` | `YC_TEST_IMAGE_REPOSITORY` | variable | `infra/apply.sh test output -raw image_repository` |
| репозиторий | `DEPLOY_TEST_ENABLED` | variable | `true`, когда `test` настроен (до этого push не выкладывает) |

Значения задаются в **environment**, а не в репозитории. Имена в обоих окружениях
одинаковые, а job видит только значения своего окружения: ключ prod недоступен
выкладке на test.

То же через `gh` (замените `test` на `prod` для второго окружения):

```bash
ENV=test
gh secret set YC_SA_KEY --env "$ENV" < "ci-key-$ENV.json"
gh variable set YC_IMAGE_REPOSITORY --env "$ENV" --body "$(infra/apply.sh $ENV output -raw image_repository)"
gh variable set YC_INSTANCE_ID      --env "$ENV" --body "$(infra/apply.sh $ENV output -raw instance_id)"
gh variable set YC_LOG_GROUP_ID     --env "$ENV" --body "$(infra/apply.sh $ENV output -raw log_group_id)"
rm "ci-key-$ENV.json"

# только для prod и для репозитория
gh variable set YC_TEST_IMAGE_REPOSITORY --env prod --body "$(infra/apply.sh test output -raw image_repository)"
gh variable set DEPLOY_TEST_ENABLED --body true
```

Настройки окружения **prod** (Settings → Environments → prod):

- **Required reviewers**: вы (и кто ещё может разрешать выкладку в прод);
- **Prevent self-review**: включите, если reviewer'ов больше одного;
- **Deployment branches and tags**: Selected branches → только `main`.

Почему только `main`: гейт — это код `deploy.yml` той ветки, с которой запущен workflow.
Под маску `sprint*` попадает любая новая ветка, и в ней гейт можно убрать. `main` защищён
правилами ветки.

Окружение `test` оставьте без reviewer'ов, ветки — `main` и `sprint*`.

Рекомендуется: в правилах защиты веток `main` и `sprint*` сделать обязательными проверки
`pytest`, `lint-imports`, `ruff`, `тесты архитектуры`, `mypy`, `docker build` из workflow CI.

### Почему ключ, а не Workload Identity Federation

Yandex Cloud поддерживает федерацию с OIDC GitHub Actions: тогда долгоживущий ключ не нужен.
Но для неё понадобятся федерация и federated credentials (в Terraform или руками) и обмен
токена в workflow. JSON-ключ уже заложен в `infra/README.md`, поэтому сейчас используется он.
Переход на федерацию касается только `.github/actions/setup-yc`, остальной workflow
не меняется.

## Первая выкладка на тестовых ботов

1. Lockbox `kto-ai-bot-test` должен содержать **тестовые** токены:
   `DEBUG_MODE_TOKEN=True`, `BOT_TOKEN`, `BOT_TOKEN_ADMIN` (шаблон —
   `infra/secrets.env.example`).
2. Остановите локальный запуск бота с этими же токенами. Два процесса с long polling
   на одном токене мешают друг другу: Telegram отвечает `409 Conflict`.
3. Запустите выкладку одним из способов:
   - влейте PR в `sprint<N>` (или сделайте push в эту ветку). Для этого нужна
     переменная `DEPLOY_TEST_ENABLED=true`;
   - Actions → **Deploy** → Run workflow → branch `sprint<N>`, environment `test`,
     sha пустой.
4. Дождитесь зелёного job. В summary будут образ, предыдущий тег и команда отката.
   Пока на VM стоит тег `latest` из Terraform, «предыдущий тег» будет `latest`.
5. Логи:
   ```bash
   yc logging read --group-name kto-ai-bot-test --since 15m --follow
   ```
6. Пройдите чек-лист регресса ниже.

## Чек-лист регресса на тестовых ботах

> **Заглушка.** Основной список — карточки из колонки **«Тестирование»** в Trello:
> прогнать каждую на тестовых ботах и только потом переносить в «Готово».
> Ниже ключевые сценарии из кода, которые проверяются при каждой выкладке.

Подготовка: тестовый Telegram-аккаунт с Business, тестовый бот подключён как
чат-бот бизнес-аккаунта. Ваш id указан в `ADMIN_ID_LIST`.

**Запуск и инфраструктура**

- [ ] Deploy зелёный, в логах есть `Бот запущен`, нет повторных стартов.
- [ ] Отключение и подключение бота в настройках Business → в логах
      `connected business account` / `DISABLED business account`.

**Бизнес-бот (ответы от имени владельца)**

- [ ] Текст от собеседника → бот «читает» сообщение, показывает typing и отвечает.
      Длинный ответ приходит несколькими сообщениями (разделитель `NEXT_MESSAGE_SEPARATOR`).
- [ ] Несколько сообщений подряд → один ответ на всю пачку, а не на каждое.
- [ ] Владелец успел ответить вручную, пока бот «думал» → ответ бота отменяется,
      ручное сообщение сохраняется в историю.
- [ ] Стикер, фото (одно и несколько), голосовое, кружок → бот реагирует без ошибок
      в логах.
- [ ] Пересланное сообщение (от пользователя, из канала, со скрытым автором) → ответ
      учитывает, откуда оно.
- [ ] История сохраняется в YDB: после рестарта бот помнит контекст диалога.

**Админ-бот (только для `ADMIN_ID_LIST`)**

- [ ] `/stop` → бизнес-бот перестаёт отвечать; `/play` → снова отвечает.
- [ ] `/users` → список пользователей; `/update_users` → таблица обновляется из истории.
- [ ] `/remind` → список чатов для напоминания; `/remind_<chat_id>` → напоминание
      уходит в этот чат. `/remind_all` в тесте используйте осторожно: напоминание
      уйдёт во все чаты тестовой базы.
- [ ] Команды от не-админа игнорируются.

**Остановка**

- [ ] Выкладка нового sha во время генерации ответа → ответ дописывается (graceful
      shutdown, до 60 с), потом бот стартует на новом образе.

## Выкладка в прод

1. **Боевые токены** — один раз, перед первой выкладкой в прод. Заполните Lockbox
   `kto-ai-bot-prod`:
   ```
   DEBUG_MODE_TOKEN=False
   BOT_TOKEN_RELEASE=...
   BOT_TOKEN_ADMIN_RELEASE=...
   ```
   плюс остальные переменные (боевая YDB, ключи LLM и т. д.):
   ```bash
   cp infra/secrets.env.example infra/secrets.prod.env   # в .gitignore
   make -C infra secrets ENV=prod FILE=secrets.prod.env
   ```
   При `DEBUG_MODE_TOKEN=False` бот требует только `*_RELEASE`-токены
   (`bot/core/domain/const/env_const.py`). Тестовые токены в prod не нужны.
   Остановите старый боевой процесс, если он где-то ещё запущен на этих токенах
   (иначе `409 Conflict`).
2. Убедитесь, что нужный sha прошёл test (зелёный Deploy в test) и чек-лист регресса.
3. Actions → **Deploy** → Run workflow:
   - branch: `main`, environment: `prod`;
   - sha: коммит, проверенный на test (полный или короткий sha, можно имя ветки).
4. Reviewer подтверждает выкладку (Review deployments → Approve).
5. Job проверяет, что в test-registry есть `tested-<sha>`, и копирует этот digest
   в prod-registry. Затем выкладывает его и ждёт старта бота.
6. Проверьте в боевых ботах 2–3 ключевых сценария: ответ на текст, `/users` в админ-боте.

## Откат

**Код (образ).** Предыдущий тег показан в summary каждой выкладки. Откат — это
выкладка предыдущего sha:

- Actions → **Deploy** → Run workflow → environment `test`/`prod`, sha = предыдущий тег.
  Образ уже в registry, поэтому сборки нет, откат занимает около минуты плюс время старта.
  Для prod нужно подтверждение reviewer'а. Работает для любого sha с `tested-<sha>`.
  На test можно указать и тег образа, которого нет в git: например `latest`, если
  неудачной была самая первая выкладка.
- Без GitHub (нужны `yc`, `jq` и права на VM):
  ```bash
  ENV=prod
  .github/scripts/deploy-vm.sh \
    "$(infra/apply.sh $ENV output -raw instance_id)" \
    "$(infra/apply.sh $ENV output -raw image_repository)" \
    <предыдущий_sha>
  ```
  Тот же скрипт откатывает на `latest`, если неудачной была самая первая выкладка.

Список тегов в registry:
```bash
yc container image list --repository-name "$(infra/apply.sh prod output -raw registry_id)/kto-ai-bot"
```

**Секреты (Lockbox).** Новая версия секрета применяется при рестарте контейнера. Чтобы
вернуть старые значения, залейте их через `push-secrets.sh` (или в консоли Lockbox сделайте
предыдущую версию текущей) и выполните `yc compute instance restart kto-ai-bot-<env>`.

## Если выкладка упала

| Где упало | Что смотреть |
|---|---|
| «Проверить настройки окружения» | не заданы variables в GitHub Environment |
| «Образ для prod», `Нет …:tested-<sha>` | sha не проходил test: сначала выложите его на test |
| «Образ для prod», `denied` | нет pull из test-registry: `promote_from_registry_id` в `prod.tfvars` + `make apply ENV=prod` |
| setup-yc | пустой или неверный `YC_SA_KEY`, ключ удалён (ротация) |
| push образа | нет роли `container-registry.images.pusher` у SA CI, неверный `YC_IMAGE_REPOSITORY` |
| «Выложить на VM» | нет `compute.editor` на VM или `iam.serviceAccounts.user` на SA VM, неверный `YC_INSTANCE_ID` |
| «Дождаться старта бота», warning `yc logging read` | нет `logging.reader` на log group (не выполнен `make apply` после D3), неверный `YC_LOG_GROUP_ID` |
| «Дождаться старта бота», `Некорректная конфигурация` | в Lockbox не хватает переменных, имена в логе job |
| «Дождаться старта бота», `lockbox-launcher: giving up` | у SA VM нет доступа к Lockbox или секрет пуст |
| «Дождаться старта бота», таймаут | смотреть полные логи: `yc logging read --group-name kto-ai-bot-<env> --since 30m` |

Если упала проверка, VM уже работает на новом теге. Откатите её (раздел выше) или
выложите исправление.
