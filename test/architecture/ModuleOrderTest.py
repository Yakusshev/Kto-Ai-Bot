"""Порядок в модуле (AT-90): константы, затем публичные классы и функции, затем приватные (`_name`).

Выше своего места может стоять только то, что нужно при импорте модуля: декоратор, базовый класс,
значение по умолчанию, тип в аннотации (без `from __future__ import annotations`), значение константы.
Синглтон или псевдоним типа, который строится из класса выше (`timeline = Timeline()`), стоит после него.
Импорты, `if`/`try` верхнего уровня и докстринг модуля не учитываются.

Старые файлы с нарушениями — в _LEGACY_ORDER. Это храповик: исправил файл — убери его из списка.
"""
import ast
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_SOURCE_DIR = _ROOT / "bot"
_EXCLUDED = frozenset(
    {
        # Генерируется из messages.ftl
        "bot/resource/Strings.py",
    },
)
# Оператор `type X = ...` есть только в Python 3.12+; проект работает на 3.11
_TYPE_ALIAS_NODES: tuple[type, ...] = tuple(getattr(ast, name) for name in ("TypeAlias",) if hasattr(ast, name))
_CONSTANT_RANK = 0
_PUBLIC_RANK = 1
_PRIVATE_RANK = 2
_RANK_NAMES = {
    _CONSTANT_RANK: "константа",
    _PUBLIC_RANK: "публичное определение",
    _PRIVATE_RANK: "приватное определение",
}

# Старые файлы, где порядок нарушен. Только сокращать, новых строк не добавлять
_LEGACY_ORDER = frozenset(
    {
        "bot/feature/admin/entry/filter/IsRemindCommand.py",
        "bot/feature/business/data/repository/ChatHistoryRepositoryImpl.py",
        "bot/resource/GenerateStrings.py",
    },
)


@dataclass(frozen = True)
class _Statement:
    rank: int
    names: frozenset[str]
    import_time_names: frozenset[str]
    line: int


def test_when_reading_modules_expect_constants_public_private_order() -> None:
    # Arrange
    modules = _modules()

    # Act
    actual = {
        path: violations[0]
        for path, tree in modules.items()
        if path not in _LEGACY_ORDER and (violations := order_violations(tree))
    }

    # Assert
    expected: dict[str, str] = {}
    assert actual == expected, (
        "В модуле сначала константы, затем публичные классы и функции, затем приватные; "
        "выше может стоять только то, что нужно при импорте (декоратор, базовый класс, значение по умолчанию)"
    )


def test_when_legacy_module_fixed_expect_removed_from_list() -> None:
    # Arrange
    modules = _modules()

    # Act
    actual = sorted(path for path in _LEGACY_ORDER if path not in modules or not order_violations(modules[path]))

    # Assert
    expected: list[str] = []
    assert actual == expected, "Порядок в файле исправлен или файл удалён — убери его из _LEGACY_ORDER"


def test_when_private_function_above_public_expect_violation() -> None:
    # Arrange
    tree = ast.parse("def _helper():\n    pass\n\n\ndef handler():\n    _helper()\n")

    # Act
    actual = order_violations(tree)

    # Assert
    expected = ["строка 5: публичное определение handler ниже, чем приватное определение _helper (строка 1)"]
    assert actual == expected


def test_when_private_needed_at_import_expect_no_violation() -> None:
    # Arrange
    source = (
        "def _decorator(f):\n    return f\n\n\n@_decorator\ndef handler():\n    pass\n\n\n"
        "class _Base:\n    pass\n\n\nclass Public(_Base):\n    pass\n\n\n"
        "SINGLETON = Public()\n"
    )

    # Act
    actual = order_violations(ast.parse(source))

    # Assert
    expected: list[str] = []
    assert actual == expected


def test_when_constant_below_function_expect_violation() -> None:
    # Arrange
    tree = ast.parse("def handler():\n    pass\n\n\nLIMIT = 5\n")

    # Act
    actual = order_violations(tree)

    # Assert
    expected = ["строка 5: константа LIMIT ниже, чем публичное определение handler (строка 1)"]
    assert actual == expected


def order_violations(tree: ast.Module) -> list[str]:
    statements = list(_statements(tree))
    violations = []
    for index, later in enumerate(statements):
        if later.rank == _CONSTANT_RANK and _depends_on_definitions(
            statement = later,
            before = statements[:index],
        ):
            # Синглтон или псевдоним типа строится из класса выше — стоит сразу после своих зависимостей
            continue
        for earlier_index, earlier in enumerate(statements[:index]):
            if earlier.rank > later.rank and not _needed_at_import(
                statement = earlier,
                after = statements[earlier_index + 1:index + 1],
            ):
                violations.append(
                    f"строка {later.line}: {_RANK_NAMES[later.rank]} {', '.join(sorted(later.names))} "
                    f"ниже, чем {_RANK_NAMES[earlier.rank]} {', '.join(sorted(earlier.names))} (строка {earlier.line})",
                )
                break
    return violations


def _modules() -> dict[str, ast.Module]:
    modules = {}
    for path in sorted(_SOURCE_DIR.rglob("*.py")):
        relative = path.relative_to(_ROOT).as_posix()
        if relative not in _EXCLUDED:
            modules[relative] = ast.parse(path.read_text(encoding = "utf-8"))
    return modules


def _depends_on_definitions(
    statement: _Statement,
    before: list[_Statement],
) -> bool:
    return any(
        statement.import_time_names & earlier.names
        for earlier in before
        if earlier.rank != _CONSTANT_RANK
    )


def _needed_at_import(
    statement: _Statement,
    after: list[_Statement],
) -> bool:
    """Определение выше своего места оправдано, если его читает при импорте что-то между ним и проверяемым."""
    return any(statement.names & later.import_time_names for later in after)


def _statements(tree: ast.Module) -> Iterator[_Statement]:
    lazy_annotations = any(
        isinstance(node, ast.ImportFrom)
        and node.module == "__future__"
        and any(alias.name == "annotations" for alias in node.names)
        for node in tree.body
    )
    for node in tree.body:
        names = _defined_names(node)
        if not names or _is_skipped(node):
            continue
        yield _Statement(
            rank = _rank(
                node = node,
                names = names,
            ),
            names = frozenset(names),
            import_time_names = frozenset(
                _import_time_names(
                    node = node,
                    lazy_annotations = lazy_annotations,
                ),
            ),
            line = node.lineno,
        )


def _is_skipped(node: ast.stmt) -> bool:
    return isinstance(node, (ast.Import, ast.ImportFrom, ast.If, ast.Try, ast.Expr))


def _defined_names(node: ast.stmt) -> set[str]:
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        return {node.name}
    if isinstance(node, ast.Assign):
        return {name.id for target in node.targets for name in ast.walk(target) if isinstance(name, ast.Name)}
    if isinstance(node, (ast.AnnAssign, ast.AugAssign)) and isinstance(node.target, ast.Name):
        return {node.target.id}
    if isinstance(node, _TYPE_ALIAS_NODES):
        alias_name = getattr(node, "name", None)
        if isinstance(alias_name, ast.Name):
            return {alias_name.id}
    return set()


def _rank(
    node: ast.stmt,
    names: set[str],
) -> int:
    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        return _CONSTANT_RANK
    if all(name.startswith("_") and not name.startswith("__") for name in names):
        return _PRIVATE_RANK
    return _PUBLIC_RANK


def _import_time_names(
    node: ast.AST,
    lazy_annotations: bool,
) -> Iterator[str]:
    """Имена, которые читаются при выполнении node во время импорта модуля (тела функций - нет)."""
    if isinstance(node, ast.Name):
        yield node.id
    else:
        for child in _import_time_children(
            node = node,
            lazy_annotations = lazy_annotations,
        ):
            yield from _import_time_names(
                node = child,
                lazy_annotations = lazy_annotations,
            )


def _import_time_children(
    node: ast.AST,
    lazy_annotations: bool,
) -> list[ast.AST]:
    """Части node, которые выполняются при импорте: у определений - только декораторы, базы, значения по умолчанию."""
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return _function_import_time_children(
            node = node,
            lazy_annotations = lazy_annotations,
        )
    if isinstance(node, ast.ClassDef):
        return [*node.decorator_list, *node.bases, *(keyword.value for keyword in node.keywords), *node.body]
    if isinstance(node, ast.Lambda):
        return [*node.args.defaults, *(default for default in node.args.kw_defaults if default is not None)]
    if isinstance(node, ast.AnnAssign):
        annotation = [] if lazy_annotations else [node.annotation]
        return [*annotation, *([node.value] if node.value is not None else [])]
    return list(ast.iter_child_nodes(node))


def _function_import_time_children(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    lazy_annotations: bool,
) -> list[ast.AST]:
    children: list[ast.AST] = [*node.decorator_list, *node.args.defaults]
    children += [default for default in node.args.kw_defaults if default is not None]
    if not lazy_annotations:
        children += [arg.annotation for arg in _all_args(node.args) if arg.annotation is not None]
        if node.returns is not None:
            children.append(node.returns)
    return children


def _all_args(args: ast.arguments) -> list[ast.arg]:
    extra = [arg for arg in (args.vararg, args.kwarg) if arg is not None]
    return [*args.posonlyargs, *args.args, *args.kwonlyargs, *extra]
