"""Храповик базовой линии import-linter (AT-90): исключений в ignore_imports не становится больше.

lint-imports сам падает, если исключение больше не нужно, - так строка удаляется вместе с исправлением.
Этот тест закрывает обратную дыру: новое нарушение нельзя «узаконить», дописав строку в ignore_imports.
"""
import configparser
from pathlib import Path

_CONFIG = Path(__file__).resolve().parents[2] / ".importlinter"
_CONTRACT_PREFIX = "importlinter:contract:"

# Только уменьшать - вместе с удалением строк из .importlinter
_BASELINE = {
    "domain-pure": 0,
    "feature-layers": 9,
    "domain-layers": 1,
    "domain-util-pure": 1,
    "data-no-scenario": 0,
    "presenter-no-client": 0,
    "feature-entry-public": 1,
    "data-only-from-di": 9,
}


def test_when_reading_importlinter_expect_ignored_imports_match_baseline() -> None:
    # Arrange
    expected = _BASELINE

    # Act
    actual = _ignored_imports_count()

    # Assert
    assert actual == expected, (
        "Число исключений в .importlinter изменилось: убрал нарушение - уменьши _BASELINE; "
        "новые нарушения исправляй в коде, а не в ignore_imports"
    )


def _ignored_imports_count() -> dict[str, int]:
    parser = configparser.ConfigParser()
    parser.read(_CONFIG, encoding = "utf-8")
    return {
        section.removeprefix(_CONTRACT_PREFIX): len(
            [line for line in parser[section].get("ignore_imports", "").splitlines() if line.strip()],
        )
        for section in parser.sections()
        if section.startswith(_CONTRACT_PREFIX)
    }
