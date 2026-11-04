"""Храповик базовой линии ruff (AT-90): исключений на ограждающие правила не становится больше.

Исключение - это `# noqa: <код>` в коде или запись в `[tool.ruff.lint.per-file-ignores]` (pyproject.toml).
RUF100 сам падает на ненужной пометке `noqa`, - так она удаляется вместе с исправлением.
Этот тест закрывает обратную дыру: новое нарушение нельзя «узаконить», дописав пометку или запись.
Каждая пометка `noqa` несёт пояснение по-русски: `# noqa: C901 - сложная функция`;
дописать его ко всем - `python -m scripts.explain_noqa`.
"""
import re
import tomllib
from collections import Counter
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_SCAN_PATHS = (
    "bot",
    "main.py",
)
_NOQA = re.compile(r"#\s*noqa:\s*(?P<codes>[A-Z0-9]+(?:\s*,\s*[A-Z0-9]+)*)(?P<rest>.*)$", re.MULTILINE)
# После кодов - тире и пояснение: `- сложная функция` (длинное или короткое тире)
_EXPLANATION = re.compile(r"^\s+[—-]\s+\S")
_GUARDED_CODES = frozenset(
    {
        "C901",
        "PLR0913",
        "TID251",
    },
)

# Только уменьшать - вместе с исправлением нарушений
_BASELINE = {
    "PLR0913": 2,
    "TID251": 2,
}


def test_when_counting_ruff_exceptions_expect_guarded_codes_match_baseline() -> None:
    # Arrange
    expected = _BASELINE

    # Act
    actual = _exception_counts()

    # Assert
    assert actual == expected, (
        "Число исключений ruff изменилось: убрал нарушение - уменьши _BASELINE; "
        "новые нарушения исправляй в коде, а не пометкой noqa или записью в per-file-ignores"
    )


def test_when_reading_noqa_expect_every_guarded_one_explained() -> None:
    # Arrange
    expected: list[str] = []

    # Act
    actual = _unexplained_noqa()

    # Assert
    assert actual == expected, (
        "Пометке noqa нужно пояснение после кода: `# noqa: C901 - сложная функция` "
        "(python -m scripts.explain_noqa); а лучше - исправить нарушение"
    )


def _python_files() -> list[Path]:
    files: list[Path] = []
    for name in _SCAN_PATHS:
        target = _ROOT / name
        if target.is_file():
            files.append(target)
        else:
            files.extend(path for path in target.rglob("*.py") if "__pycache__" not in path.parts)
    return sorted(files)


def _exception_counts() -> dict[str, int]:
    counts: Counter[str] = Counter()
    for path in _python_files():
        for match in _NOQA.finditer(path.read_text(encoding = "utf-8")):
            codes = {code.strip() for code in match.group("codes").split(",")}
            counts.update(codes & _GUARDED_CODES)
    pyproject = tomllib.loads((_ROOT / "pyproject.toml").read_text(encoding = "utf-8"))
    ignores = pyproject["tool"]["ruff"]["lint"].get("per-file-ignores", {})
    for codes in ignores.values():
        counts.update(set(codes) & _GUARDED_CODES)
    return dict(counts)


def _unexplained_noqa() -> list[str]:
    unexplained = []
    for path in _python_files():
        text = path.read_text(encoding = "utf-8")
        for match in _NOQA.finditer(text):
            codes = {code.strip() for code in match.group("codes").split(",")}
            if codes & _GUARDED_CODES and not _EXPLANATION.match(match.group("rest")):
                line_number = text.count("\n", 0, match.start()) + 1
                unexplained.append(f"{path.relative_to(_ROOT).as_posix()}:{line_number}")
    return unexplained
