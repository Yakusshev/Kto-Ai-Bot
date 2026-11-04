#!/bin/bash
# Stop-хук (S0, AT-90): прежде чем агент закончит ответ - контракты import-linter, тесты ограждений
# и храповик базовых линий относительно ветки спринта (scripts/baseline_ratchet.py).
# Нарушение - exit 2: агент не останавливается и получает вывод проверок, чтобы исправить код.
set -u

input="$(cat 2>/dev/null || true)"

# Уже продолжаем после блокировки Stop-хука: не зацикливаемся.
if printf '%s' "$input" | grep -Eq '"stop_hook_active"[[:space:]]*:[[:space:]]*true'; then
    exit 0
fi

top="${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel 2>/dev/null)}"
cd "$top" 2>/dev/null || exit 0

# Нечего проверять: рабочее дерево чистое и все коммиты HEAD уже есть на origin (их проверил CI).
# Без этого хук срабатывал в сессиях без правок кода - на чужих базовых линиях.
if [ -z "$(git status --porcelain 2>/dev/null)" ] \
    && [ "$(git rev-list --count HEAD --not --remotes 2>/dev/null)" = "0" ]; then
    exit 0
fi

# Инструменты из .venv (ставит session-start.sh); без .venv - из PATH. Нет инструментов - не блокируем:
# поставить - pip install -r requirements-dev.txt
if [ -x .venv/bin/lint-imports ] && [ -x .venv/bin/python ]; then
    lint_imports=.venv/bin/lint-imports
    python=.venv/bin/python
elif command -v lint-imports >/dev/null 2>&1 && command -v python >/dev/null 2>&1; then
    lint_imports=lint-imports
    python=python
else
    exit 0
fi
"$python" -c "import pytest" >/dev/null 2>&1 || exit 0

failed=0
report=""
if ! out=$("$lint_imports" --no-cache 2>&1); then
    failed=1
    report+=$'lint-imports:\n'"$(echo "$out" | sed -n '/^Broken contracts/,$p' | head -60)"$'\n\n'
fi
if ! out=$("$python" -m pytest -q test/architecture -p no:cacheprovider 2>&1); then
    failed=1
    report+=$'test/architecture:\n'"$(echo "$out" | grep -E '^(E |FAILED)' | head -40)"$'\n'
fi
if ! out=$("$python" -m scripts.baseline_ratchet 2>&1); then
    # «Рост» бывает ложным: нужной ветки спринта нет локально или она устарела, и база взята не та.
    # Докачиваем все sprint* и проверяем ещё раз - платим за сеть только при подозрении.
    timeout 30 git fetch -q origin '+refs/heads/sprint*:refs/remotes/origin/sprint*' >/dev/null 2>&1
    ratchet_ok=0
    out=$("$python" -m scripts.baseline_ratchet 2>&1) || ratchet_ok=1
else
    ratchet_ok=0
fi
if [ "$ratchet_ok" -ne 0 ]; then
    failed=1
    report+=$'baseline_ratchet:\n'"$(echo "$out" | head -40)"$'\n'
fi

if [ "$failed" -eq 1 ]; then
    {
        echo "Ограждения архитектуры нарушены - исправь код, а не базовую линию:"
        echo "$report"
    } >&2
    exit 2
fi
exit 0
