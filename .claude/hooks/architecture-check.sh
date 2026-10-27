#!/bin/bash
# Stop-хук: ограждения архитектуры. Запускает lint-imports и тесты test/architecture.
# При нарушении выходит с кодом 2 и сообщением в stderr - Claude Code не даёт завершить ход
# и возвращает сообщение модели. Если зависимости не установлены - тихо выходит (не блокирует сессию).

input="$(cat 2>/dev/null || true)"

# Уже продолжаем после блокировки Stop-хука: не зацикливаемся.
if printf '%s' "$input" | grep -Eq '"stop_hook_active"[[:space:]]*:[[:space:]]*true'; then
  exit 0
fi

cd "${CLAUDE_PROJECT_DIR:-.}" 2>/dev/null || exit 0

command -v lint-imports >/dev/null 2>&1 || exit 0
command -v python >/dev/null 2>&1 || exit 0
python -c "import pytest" >/dev/null 2>&1 || exit 0

problems=""

if ! out="$(lint-imports 2>&1)"; then
  problems+=$'=== lint-imports (контракты слоёв, .importlinter) ===\n'"$(printf '%s\n' "$out" | tail -n 40)"$'\n'
fi

if ! out="$(python -m pytest test/architecture -q -p no:cacheprovider 2>&1)"; then
  problems+=$'=== test/architecture (длина файлов) ===\n'"$(printf '%s\n' "$out" | tail -n 30)"$'\n'
fi

if [ -n "$problems" ]; then
  {
    echo "Нарушены ограждения архитектуры. Исправьте код (не расширяйте baseline в .importlinter и LEGACY_LIMITS):"
    printf '%s' "$problems"
  } >&2
  exit 2
fi
exit 0
