#!/bin/bash
# Подготовка облачной сессии Claude Code: зависимости и ключ сервисного аккаунта YC.
set -euo pipefail

if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

cd "$CLAUDE_PROJECT_DIR"

pip install --quiet --disable-pip-version-check -r requirements-dev.txt

# Файл ключа для YDB_AUTH_KEY_FILE создаём из секрета окружения YANDEX_AUTHORIZED_KEY.
if [ -n "${YANDEX_AUTHORIZED_KEY:-}" ]; then
  key_file="${YDB_AUTH_KEY_FILE:-credentials/ydb_authorized_key.json}"
  mkdir -p "$(dirname "$key_file")"
  (umask 077 && printf '%s' "$YANDEX_AUTHORIZED_KEY" > "$key_file")
fi

echo 'export PYTHONPATH="."' >> "$CLAUDE_ENV_FILE"
