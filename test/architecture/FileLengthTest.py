"""
Ограждение архитектуры: длина файлов.

Новые файлы - не длиннее MAX_LINES строк. У уже существующих больших файлов
потолок равен их текущему размеру (LEGACY_LIMITS): файл можно сокращать,
но нельзя растить. Когда файл разрезан до MAX_LINES и меньше, его запись
нужно удалить (тест напомнит). Только сокращать.
"""
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]

MAX_LINES = 500

# Проверяемый код: пакет bot и точка входа.
SCAN_PATHS = ("bot", "main.py")

# Сгенерированные файлы, их длину не контролируем.
GENERATED = frozenset(
    {
        "bot/resource/Strings.py",
    }
)

# Существующие файлы длиннее MAX_LINES: путь от корня -> потолок (текущий размер).
# На момент заведения таких файлов нет (самый длинный - около 400 строк).
LEGACY_LIMITS: dict[str, int] = {}


def _line_count(path: Path) -> int:
    with path.open("r", encoding="utf-8") as file:
        return sum(1 for _ in file)


def _python_files() -> list[Path]:
    files: list[Path] = []
    for name in SCAN_PATHS:
        target = ROOT / name
        if target.is_file():
            files.append(target)
        else:
            files.extend(p for p in target.rglob("*.py") if "__pycache__" not in p.parts)
    return sorted(files)


def _relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def test_python_files_not_too_long():
    violations = []
    for path in _python_files():
        rel = _relative(path)
        if rel in GENERATED:
            continue
        limit = LEGACY_LIMITS.get(rel, MAX_LINES)
        lines = _line_count(path)
        if lines > limit:
            violations.append(f"{rel}: {lines} строк при потолке {limit}")
    assert not violations, (
        f"Файлы длиннее допустимого (новые - до {MAX_LINES} строк, "
        "существующие не должны расти). Разрежьте файл на модули:\n  "
        + "\n  ".join(violations)
    )


@pytest.mark.parametrize("rel", sorted(LEGACY_LIMITS))
def test_legacy_limits_are_actual(rel):
    path = ROOT / rel
    assert path.is_file(), f"{rel} удалён или переименован: уберите запись из LEGACY_LIMITS"
    assert _line_count(path) > MAX_LINES, (
        f"{rel} уже не длиннее {MAX_LINES} строк: уберите запись из LEGACY_LIMITS"
    )


def test_generated_files_exist():
    missing = [rel for rel in sorted(GENERATED) if not (ROOT / rel).is_file()]
    assert not missing, f"Сгенерированные файлы не найдены, обновите GENERATED: {missing}"
