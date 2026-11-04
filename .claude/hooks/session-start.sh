#!/bin/bash
# SessionStart (AT-90): в облачной среде Claude Code ставит зависимости и инструменты проверок в .venv
# (Python 3.11, как в Dockerfile и CI - baseline mypy зависит от версии) и подтягивает ветку спринта для
# храповика базовых линий. Заодно создаёт файл ключа сервисного аккаунта YC. Локально ничего не делает.
set -uo pipefail

if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

cd "$CLAUDE_PROJECT_DIR" || exit 0

notes=()
if [ ! -x .venv/bin/python ]; then
  uv venv -q --python 3.11 .venv >&2 || notes+=("не удалось создать .venv")
fi
# uv pip install идемпотентен: при уже установленных пакетах - доли секунды
uv pip install -q --python .venv/bin/python -r requirements-dev.txt >&2 \
  || notes+=("не удалось поставить зависимости из requirements-dev.txt")

# Облако клонирует одну ветку: без ветки спринта храповик (scripts/baseline_ratchet.py) берёт устаревшую
# за базу и видит «рост» базовых линий, которого нет. Качаем только ветку по умолчанию в GitHub
# (обычно текущий спринт); остальные sprint* хук Stop докачает сам, если сравнение с ней не сойдётся.
default_branch=$(timeout 10 git ls-remote --symref origin HEAD 2>/dev/null | sed -n 's|^ref: refs/heads/\(.*\)[[:space:]]HEAD$|\1|p')
if [ -n "$default_branch" ]; then
  timeout 30 git fetch -q origin "+refs/heads/$default_branch:refs/remotes/origin/$default_branch" >&2 \
    || notes+=("не удалось скачать ветку $default_branch - храповик базовых линий может сравнивать не с той веткой")
fi

# Файл ключа для YDB_AUTH_KEY_FILE создаём из секрета окружения YANDEX_AUTHORIZED_KEY.
if [ -n "${YANDEX_AUTHORIZED_KEY:-}" ]; then
  key_file="${YDB_AUTH_KEY_FILE:-credentials/ydb_authorized_key.json}"
  mkdir -p "$(dirname "$key_file")"
  (umask 077 && printf '%s' "$YANDEX_AUTHORIZED_KEY" > "$key_file")
fi

if [ -n "${CLAUDE_ENV_FILE:-}" ]; then
  {
    echo 'export PYTHONPATH="."'
    echo "export VIRTUAL_ENV=\"$CLAUDE_PROJECT_DIR/.venv\""
    echo "export PATH=\"$CLAUDE_PROJECT_DIR/.venv/bin:\$PATH\""
  } >> "$CLAUDE_ENV_FILE"
fi

if [ "${#notes[@]}" -gt 0 ]; then
  printf '{"systemMessage": "session-start: %s"}\n' "$(IFS=';'; echo "${notes[*]}" | sed 's/;/; /g')"
fi
exit 0
