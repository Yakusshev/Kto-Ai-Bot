#!/usr/bin/env bash
# Заливает переменные окружения бота в Lockbox-секрет kto-ai-bot-<env>
# новой версией. Ключи из файла добавляются/перезаписываются, остальные
# ключи предыдущей версии сохраняются (так работает AddVersion в Lockbox).
#
#   infra/push-secrets.sh <test|prod> <файл .env> [ydb_authorized_key.json]
#
# Значения не печатаются и не сохраняются на диск: payload идёт в yc через stdin.
# Бот перечитывает секрет при старте контейнера — после заливки перезапустите
# VM (команда в README.md).
set -euo pipefail

ENV_NAME="${1:-}"
ENV_FILE="${2:-}"
YDB_KEY_FILE="${3:-}"

case "$ENV_NAME" in
  test|prod) ;;
  *)
    echo "Использование: $0 <test|prod> <файл .env> [ydb_authorized_key.json]" >&2
    exit 2
    ;;
esac
if [[ ! -f "$ENV_FILE" ]]; then
  echo "Нет файла $ENV_FILE (шаблон: infra/secrets.env.example)" >&2
  exit 2
fi
if [[ -n "$YDB_KEY_FILE" && ! -f "$YDB_KEY_FILE" ]]; then
  echo "Нет файла ключа YDB $YDB_KEY_FILE" >&2
  exit 2
fi

SECRET_NAME="kto-ai-bot-${ENV_NAME}"

python3 -I - "$ENV_FILE" "$YDB_KEY_FILE" <<'PY' | yc lockbox secret add-version --name "$SECRET_NAME" --payload - >/dev/null
import json
import sys

env_file, ydb_key_file = sys.argv[1], sys.argv[2]
entries = {}
with open(env_file, encoding = "utf-8") as source:
    for number, raw in enumerate(source, start = 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export "):].lstrip()
        key, separator, value = line.partition("=")
        key = key.strip()
        if not separator or not key:
            sys.exit("{0}:{1}: ожидается KEY=VALUE".format(env_file, number))
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        # Пустые значения пропускаем: для бота пустое == не задано
        if value:
            entries[key] = value

if ydb_key_file:
    with open(ydb_key_file, encoding = "utf-8") as key_source:
        entries["YDB_AUTHORIZED_KEY_JSON"] = key_source.read()

if not entries:
    sys.exit("{0}: нет ни одной переменной".format(env_file))

json.dump([{"key": key, "text_value": value} for key, value in entries.items()], sys.stdout)
print("Ключи для Lockbox: " + ", ".join(sorted(entries)), file = sys.stderr)
PY

echo "Новая версия секрета ${SECRET_NAME} создана." >&2
