"""Импорт своих модулей только для типов (AT-90): `if TYPE_CHECKING:` + тип в кавычках маскирует цикл импортов.

Цикл исправляется в коде: общий кусок выносится в модуль ниже, зависимость разворачивается через порт.
Под TYPE_CHECKING можно импортировать только сторонние библиотеки, тяжёлые при загрузке.
Старые файлы - в _LEGACY_TYPE_CHECKING. Это храповик: исправил файл - убери его из списка.
"""
import ast
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_SOURCE_DIR = _ROOT / "bot"
_OWN_PACKAGE = "bot"

# Только сокращать. На момент введения проверки таких файлов нет
_LEGACY_TYPE_CHECKING: frozenset[str] = frozenset()


def test_when_importing_for_type_checking_expect_no_own_modules() -> None:
    # Arrange
    expected = _LEGACY_TYPE_CHECKING

    # Act
    actual = frozenset(
        path.relative_to(_ROOT).as_posix()
        for path in sorted(_SOURCE_DIR.rglob("*.py"))
        if _imports_own_module_for_type_checking(tree = ast.parse(path.read_text(encoding = "utf-8")))
    )

    # Assert
    assert actual == expected, (
        "Импорт модуля bot под `if TYPE_CHECKING:` прячет цикл импортов - разорви цикл в коде; "
        "исправил старый файл - убери его из _LEGACY_TYPE_CHECKING"
    )


def _imports_own_module_for_type_checking(tree: ast.Module) -> bool:
    return any(
        _is_own_import(node = node)
        for block in ast.walk(tree)
        if isinstance(block, ast.If) and _is_type_checking(test = block.test)
        for statement in block.body
        for node in ast.walk(statement)
    )


def _is_type_checking(test: ast.expr) -> bool:
    if isinstance(test, ast.Name):
        return test.id == "TYPE_CHECKING"
    return isinstance(test, ast.Attribute) and test.attr == "TYPE_CHECKING"


def _is_own_import(node: ast.AST) -> bool:
    if isinstance(node, ast.ImportFrom):
        return node.level > 0 or (node.module or "").split(".")[0] == _OWN_PACKAGE
    if isinstance(node, ast.Import):
        return any(alias.name.split(".")[0] == _OWN_PACKAGE for alias in node.names)
    return False
