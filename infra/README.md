# Инфраструктура Kto-Ai-Bot в Yandex Cloud

Terraform-описание окружений `test` и `prod`: Container Registry, сервисные аккаунты,
Lockbox, Cloud Logging, сеть и постоянно работающая VM на Container Optimized Image (COI).
Все ресурсы называются `kto-ai-bot-<env>`.

Почему VM, а не serverless: бот работает через long polling и хранит FSM-состояние в памяти,
поэтому нужен один долгоживущий процесс (вариант A).

## Что создаётся

| Ресурс | Имя | Зачем |
|---|---|---|
| Container Registry | `kto-ai-bot-<env>` | образ бота `cr.yandex/<registry_id>/kto-ai-bot:<tag>` |
| Lockbox-секрет | `kto-ai-bot-<env>` | все переменные окружения бота; **значения в репозиторий и state не попадают** |
| Log group | `kto-ai-bot-<env>` | логи контейнера бота, хранятся 7 дней |
| VPC-сеть, подсеть, security group | `kto-ai-bot-<env>` | только исходящий трафик (+ SSH, если задан ключ) |
| VM (COI, не прерываемая) | `kto-ai-bot-<env>` | standard-v3, 2 vCPU 20%, 1 ГБ RAM, HDD |
| SA VM | `kto-ai-bot-<env>-vm` | см. роли ниже |
| SA CI | `kto-ai-bot-<env>-ci` | см. роли ниже, ключ выпускается вручную |

Роли (минимальные):

- **SA VM**: `container-registry.images.puller` на registry, `lockbox.payloadViewer` на секрет,
  `logging.writer` на каталог (у провайдера нет IAM на уровне log group), `ydb.editor` только
  на базу из `ydb_database_id`. Если переменная пуста, роль не выдаётся.
- **SA CI**: `container-registry.images.pusher` на registry, `compute.editor` только на эту VM,
  `iam.serviceAccounts.user` на SA VM (без него нельзя менять VM с привязанным SA).

## Как устроен запуск на VM

COI читает из metadata ключ `docker-compose` и сам поднимает контейнеры, а при изменении
metadata пересоздаёт их. Compose рендерит Terraform (`templates/docker-compose.yaml.tftpl`):

- **bot** — образ бота, `restart: always`, `network_mode: host`, `stop_grace_period: 60s`
  (переменная `stop_grace_period`). Лаунчер делает `exec`, поэтому python бота остаётся PID 1,
  сам получает SIGTERM и успевает дописать ответы LLM. SIGKILL придёт только через 60 с.
  До `exec` лаунчер завершается по SIGTERM сразу, даже если ещё ждёт Lockbox.
- **fluentbit** — `cr.yandex/yc/fluent-bit-plugin-yandex`, принимает логи по forward-протоколу
  на `127.0.0.1:24224` и пишет их в log group от имени SA VM.

### Доставка секретов из Lockbox

У COI нет встроенной интеграции с Lockbox, поэтому entrypoint контейнера бота подменяется
на маленький лаунчер `templates/lockbox_launcher.py` (только stdlib, передаётся через
`python -c`, то есть целиком лежит в metadata):

1. берёт IAM-токен SA VM из metadata-сервиса (`169.254.169.254`);
2. читает payload секрета `LOCKBOX_SECRET_ID` через Lockbox API;
3. кладёт записи в окружение и делает `exec python main.py`;
4. запись `YDB_AUTHORIZED_KEY_JSON` (если есть) сохраняет в `/tmp/ydb_authorized_key.json`
   внутри контейнера и выставляет `YDB_AUTH_KEY_FILE` на этот путь.

Почему так, а не user-data-скрипт на хосте, который пишет env-файл:

- секреты не лежат на диске хоста, их видно только процессу бота;
- нет гонки между cloud-init и стартом compose: всё в одной metadata, которую COI
  применяет атомарно;
- секрет перечитывается при каждом старте контейнера, поэтому новая версия секрета
  применяется простым перезапуском, без пересоздания VM;
- при ошибке (нет прав, сеть) лаунчер делает до 30 попыток, потом контейнер падает и docker
  его перезапускает.

Образ бота (после D1.2) содержит только `bot/`, `main.py`, `requirements.txt`: ни `.env`,
ни `credentials/` в него не попадают. Для YDB есть два варианта:

- **без ключа (рекомендуется)**: укажите `ydb_database_id` базы этого окружения
  в `envs/<env>.tfvars`. SA VM получит `ydb.editor` только на эту базу: test-VM не получит
  доступ к prod-YDB, даже если оба окружения в одном каталоге. Файла ключа нет, и
  `CreateYdbDriver` переходит на `MetadataUrlCredentials`;
- **с ключом (обязательно, если `ydb_database_id` пуст)**: залейте `credentials/ydb_authorized_key.json` третьим аргументом
  `push-secrets.sh`, он попадёт в запись `YDB_AUTHORIZED_KEY_JSON` и будет смонтирован файлом,
  как описано выше.

Предусловие: в образе есть `python` (сейчас `python:3.11-slim`). Если поменяется CMD образа,
поменяйте и `bot_command` в tfvars.

### Логи

Docker-драйвер `fluentd` (`fluentd-async`, поэтому бот стартует, даже если fluent-bit ещё
не поднялся) → fluent-bit → Cloud Logging (`resource_type=kto-ai-bot`,
`resource_id=kto-ai-bot-<env>`). Уровень у всех записей `INFO`, сам уровень бота виден
в тексте сообщения. Смотреть логи так:

```bash
yc logging read --group-name kto-ai-bot-test --since 1h --follow
```

## Предпосылки

- [yc CLI](https://yandex.cloud/ru/docs/cli/quickstart): `yc init`, профиль с облаком и каталогом.
  Права в каталоге: `admin` (нужны создание SA и выдача ролей), либо `editor` вместе
  с `resource-manager.admin`.
- Terraform ≥ 1.5. Если `registry.terraform.io` недоступен, используйте зеркало Яндекса:
  ```hcl
  # ~/.terraformrc
  provider_installation {
    network_mirror {
      url     = "https://terraform-mirror.yandexcloud.net/"
      include = ["registry.terraform.io/*/*"]
    }
    direct {
      exclude = ["registry.terraform.io/*/*"]
    }
  }
  ```
- `python3` локально (только для `push-secrets.sh`), `make` (по желанию).

### State

State локальный, отдельный файл на окружение: `infra/state/<env>.tfstate` (в `.gitignore`).
Почему не бакет Object Storage:

- в state нет секретов: значения Lockbox и ключи SA Terraform не создаёт;
- нет проблемы курицы и яйца: для бакета нужны свои ресурсы и статический ключ, которые
  сами живут вне Terraform;
- инфраструктуру применяет один человек, CI (D3) Terraform не запускает, а работает через `yc`
  с outputs.

Чем платим: state живёт на одной машине. Если он потерялся, ресурсы можно удалить по имени
`kto-ai-bot-<env>` и создать заново (см. «Пересоздание») или вернуть через `terraform import`.
Если инфраструктуру начнут применять несколько человек, перенесите state в бакет: замените
`backend "local" {}` на `backend "s3" { ... }` и выполните `terraform init -migrate-state`.

## Шаги: первое развёртывание окружения

```bash
# 1. Инфраструктура (одна команда; по умолчанию каталог берётся из профиля yc)
make -C infra apply ENV=test          # или: infra/apply.sh test
#    Посмотреть план без изменений: make -C infra plan ENV=test

# 2. Секреты: шаблон в infra/secrets.env.example
cp infra/secrets.env.example infra/secrets.test.env   # в .gitignore
#    ... заполнить ...
make -C infra secrets ENV=test FILE=secrets.test.env
#    с ключом YDB (обязательно, если ydb_database_id в envs/test.tfvars пуст):
make -C infra secrets ENV=test FILE=secrets.test.env YDB_KEY=../credentials/ydb_authorized_key.json

# 3. Образ. До D3 — вручную:
yc container registry configure-docker
REPO=$(infra/apply.sh test output -raw image_repository)
docker build -t "$REPO:latest" . && docker push "$REPO:latest"

# 4. Перезапуск, чтобы контейнер взял секрет и образ
yc compute instance restart kto-ai-bot-test
```

`ENV=prod` делается так же. Для `prod` включён `deletion_protection` на Lockbox-секрете.
Каталог или облако окружения можно зафиксировать в `envs/<env>.tfvars` (`folder_id`,
`cloud_id`). Без этого они берутся из активного профиля `yc`.

### Обновить секреты

`push-secrets.sh` создаёт новую версию секрета. Ключи из файла добавляются или
перезаписываются, остальные ключи остаются как в прошлой версии. Пустые значения
пропускаются. Значения никуда не выводятся. После заливки:

```bash
yc compute instance restart kto-ai-bot-<env>
```

Удалить ключ из секрета скрипт не умеет. Это делается в консоли Lockbox: создайте новую
версию без этого ключа.

### Пересоздание

```bash
make -C infra destroy ENV=test && make -C infra apply ENV=test
```

После пересоздания у Lockbox-секрета новый ID и пустое содержимое, а registry пустой.
Повторите шаги 2–4. Для prod сначала снимите `deletion_protection = false`
в `envs/prod.tfvars` и выполните `apply`. Во время пересоздания бот недоступен.
FSM-состояние в памяти теряется, как и при любом рестарте.

## Контракт для CI (задача D3)

Outputs (`infra/apply.sh <env> output -json`):

| Output | Пример использования |
|---|---|
| `registry_id`, `image_repository` | `docker push <image_repository>:<sha>` |
| `instance_id`, `instance_name` | `yc compute instance update ...` / `restart` |
| `lockbox_secret_id`, `lockbox_secret_name` | проверка, что секрет заполнен |
| `log_group_id` | ссылки на логи |
| `ci_service_account_id` | для выпуска ключа CI |

**Кто чем владеет.** Тег образа в metadata `docker-compose` принадлежит CI. Terraform пишет
compose только при создании VM, с тегом из `image_tag` (по умолчанию `latest`).
После этого он его не трогает: `ignore_changes = [metadata["docker-compose"]]`. Поэтому
`make apply` не откатывает тег, который выложил CI.

**Выкладка образа (CI):** собрать и запушить `<image_repository>:<sha>`, затем заменить тег
в compose, который сейчас лежит на VM. COI сам пересоздаст контейнер: старый получит SIGTERM
и до 60 с на graceful shutdown.

```bash
yc compute instance get --id "$INSTANCE_ID" --full --format json \
  | jq -r '.metadata["docker-compose"]' > compose.yaml
sed -i -E "s#(${IMAGE_REPOSITORY}):[^\"[:space:]]+#\1:${SHA}#" compose.yaml
yc compute instance update --id "$INSTANCE_ID" --metadata-from-file docker-compose=compose.yaml
```

Откат делается той же командой с предыдущим `<sha>`. Неизменяемый тег, а не `:latest`,
нужен, чтобы точно знать, что запущено, и чтобы COI видел изменение metadata.

**Изменение шаблона compose** (`templates/*`, `bot_environment`, `stop_grace_period`,
версия fluent-bit) делает человек, CI тут не участвует:

```bash
make -C infra apply ENV=test     # обновит output docker_compose, VM не тронет
make -C infra compose ENV=test   # выложит новый compose с текущим тегом образа с VM
                                 # (ARGS=<tag> — задать тег явно)
```

**Обновление COI.** Образ ОС зафиксирован при создании VM (`ignore_changes` на `image_id`),
поэтому новые релизы COI не пересоздают VM при каждом `apply`. Чтобы обновить COI осознанно
(VM пересоздаётся, бот недолго недоступен, публичный IP меняется):

```bash
infra/apply.sh test apply -replace=yandex_compute_instance.bot
make -C infra compose ENV=test ARGS=<sha>   # новая VM стартует с image_tag: вернуть тег из CI
```

### Ключ для CI

Terraform ключ не создаёт, чтобы он не попал в state. Выпускается один раз на окружение:

```bash
yc iam key create --service-account-name kto-ai-bot-test-ci --output ci-key.json
# содержимое ci-key.json → секрет GitHub Actions (например YC_SA_KEY_TEST), потом удалить файл
rm ci-key.json
```

Ротация: создать новый ключ, обновить секрет в GitHub, удалить старый
(`yc iam key list --service-account-name ...`, `yc iam key delete <id>`).

## Проверка конфигурации без облака

```bash
make -C infra check   # terraform fmt -check + terraform validate
```
