#!/usr/bin/env bash
# Проверка после выкладки по логам контейнера в Cloud Logging.
#
#   .github/scripts/verify-deploy.sh <log_group_id> <since_rfc3339> [timeout_sec] [stable_sec]
#
# Успех: после <since> в логах появилась строка старта бота
# («Бот запущен, ожидаю SIGTERM/SIGINT…», main.py), и за следующие
# <stable_sec> секунд не случилось повторного старта (то есть нет цикла
# падение → restart: always → падение).
# Провал: строки старта нет за <timeout_sec>, лаунчер Lockbox сдался
# или бот упал на проверке конфигурации.
#
# Почему логи, а не serial port: контейнеры COI пишут через драйвер fluentd
# в log group окружения, в serial-консоль их вывод не попадает.
# Нужна роль logging.reader у SA CI (infra/iam.tf).
#
# Тексты сообщений бота в лог CI не выводятся: там переписка пользователей.
# Печатаются только служебные строки лаунчера и ошибки конфигурации.
set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "Использование: $0 <log_group_id> <since_rfc3339> [timeout_sec] [stable_sec]" >&2
  exit 2
fi
group_id="$1"
since="$2"
timeout_sec="${3:-420}"
stable_sec="${4:-60}"

START_MARKER="Бот запущен"
# Строки, которые безопасно показывать: в них нет пользовательских данных
SAFE_PATTERN='^lockbox-launcher:|Некорректная конфигурация|^  - '
# Полнотекстовый поиск Cloud Logging; точное совпадение проверяется ниже grep'ом
LOG_FILTER='message: "Бот запущен" OR message: "lockbox-launcher" OR message: "Некорректная конфигурация" OR message: "переменная"'

err_file="$(mktemp)"
trap 'rm -f "$err_file"' EXIT

read_messages() {
  local raw
  # Фильтр на стороне Logging: под нагрузкой с момента выкладки может быть больше
  # записей, чем --limit, и строки старта среди них не окажется
  if ! raw="$(yc logging read --group-id "$group_id" --since "$since" \
    --filter "$LOG_FILTER" --limit 1000 --format json 2>"$err_file")"; then
    # Ошибка yc (нет роли logging.reader, неверный group id) — без содержимого логов
    echo "::warning::yc logging read: $(head -c 300 "$err_file")" >&2
    return 0
  fi
  jq -r '(. // [])[] | (.message // "")' <<<"$raw" 2>/dev/null || true
}

count_starts() {
  grep -cF "$START_MARKER" <<<"$1" || true
}

show_safe_lines() {
  echo "Служебные строки из логов (последние 30):"
  grep -E "$SAFE_PATTERN" <<<"$1" | tail -n 30 || true
  echo "Полные логи: yc logging read --group-id ${group_id} --since ${since}"
}

deadline=$(( $(date +%s) + timeout_sec ))
echo "Жду старта бота в логах (group ${group_id}, с ${since}, до ${timeout_sec} с)…"

while :; do
  messages="$(read_messages)"
  if [[ "$(count_starts "$messages")" -ge 1 ]]; then
    break
  fi
  if grep -qE '^lockbox-launcher: giving up|Некорректная конфигурация' <<<"$messages"; then
    echo "::error::Бот не стартовал: ошибка чтения Lockbox или конфигурации"
    show_safe_lines "$messages"
    exit 1
  fi
  if [[ $(date +%s) -ge $deadline ]]; then
    echo "::error::За ${timeout_sec} с бот не написал «${START_MARKER}»"
    show_safe_lines "$messages"
    exit 1
  fi
  sleep 15
done

echo "Бот стартовал. Проверяю стабильность ${stable_sec} с…"
sleep "$stable_sec"
messages="$(read_messages)"
starts="$(count_starts "$messages")"
if [[ "$starts" -gt 1 ]]; then
  echo "::error::Бот стартовал ${starts} раз после выкладки: контейнер перезапускается"
  show_safe_lines "$messages"
  exit 1
fi
echo "OK: бот работает"
