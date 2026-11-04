"""Храповик базовых линий относительно ветки спринта (AT-90).

Тесты test/architecture сверяют базовые линии с числами в самих тестах — а их агент может поднять.
Этот скрипт сравнивает рабочее дерево с merge-base ветки спринта: базовая линия не выше, чем там.

- `# noqa` на C901 / PLR0913 / TID251 в bot/ и main.py и записи `per-file-ignores` в pyproject.toml — не больше по каждому коду;
- исключения `ignore_imports` в .importlinter — не больше по каждому контракту;
- секции `[mypy-…]` в mypy.ini — не больше, у оставшихся не больше отключённых кодов;
- потолки и списки-исключения `_LEGACY_*` в test/architecture — не больше записей,
  сумма не выше, потолок каждого файла не выше.

Если guard-файла или контракта у базы ещё нет, его базовая линия вводится этим изменением — сравнивать не с чем.

    .venv/bin/python -m scripts.baseline_ratchet                      # база — ближайшая ветка sprint*
    .venv/bin/python -m scripts.baseline_ratchet --base origin/sprint6
"""
import argparse
import ast
import configparser
import re
import subprocess
import sys
import tomllib
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

_ROOT = Path(__file__).resolve().parents[1]
_GUARDED_CODES = frozenset(
    {
        "C901",
        "PLR0913",
        "TID251",
    },
)
_NOQA = re.compile(r"#\s*noqa:\s*(?P<codes>[A-Z0-9]+(?:\s*,\s*[A-Z0-9]+)*)")
_CONTRACT_PREFIX = "importlinter:contract:"
_MYPY_SECTION_PREFIX = "mypy-"
_ARCHITECTURE_TESTS = "test/architecture"
# Словари и множества в тестах ограждений, которые можно только сокращать
_LEGACY_NAME = re.compile(r"^_LEGACY_[A-Z_]+$")


@dataclass(frozen = True)
class Snapshot:
    noqa: dict[str, int]
    ignore_imports: dict[str, int] | None
    mypy_sections: dict[str, frozenset[str]] | None
    legacy: dict[str, dict[str, int] | None]


def main() -> None:
    parser = argparse.ArgumentParser(description = __doc__.splitlines()[0])
    parser.add_argument(
        "--base",
        help = "ветка или коммит, с merge-base которого сравнивать; по умолчанию — ближайшая sprint*",
    )
    args = parser.parse_args()
    base_ref = args.base or _nearest_sprint_ref()
    if base_ref is None:
        print("baseline_ratchet: ветка спринта не найдена — проверка пропущена")
        return
    merge_base = _git("merge-base", "HEAD", base_ref).strip()
    violations = compare(
        base = _snapshot(reader = _RevisionReader(revision = merge_base)),
        current = _snapshot(reader = _WorktreeReader()),
    )
    if violations:
        print(f"Базовая линия выросла относительно {base_ref} ({merge_base[:8]}):")
        for violation in violations:
            print(f"- {violation}")
        print("Новые нарушения исправляй в коде; noqa, ignore_imports, секции mypy.ini и потолки не поднимать.")
        sys.exit(1)
    print(f"baseline_ratchet: базовые линии не выше, чем в {base_ref} ({merge_base[:8]})")


def compare(
    base: Snapshot,
    current: Snapshot,
) -> list[str]:
    violations = [
        f"noqa {code}: {count} пометок, в базе {base.noqa.get(code, 0)}"
        for code, count in sorted(current.noqa.items())
        if count > base.noqa.get(code, 0)
    ]
    if base.ignore_imports is not None and current.ignore_imports is not None:
        # Контракт, которого в базе ещё нет, вводится этим изменением вместе со своей базовой линией
        violations += [
            f".importlinter {contract}: {count} исключений, в базе {base.ignore_imports[contract]}"
            for contract, count in sorted(current.ignore_imports.items())
            if contract in base.ignore_imports and count > base.ignore_imports[contract]
        ]
    if base.mypy_sections is not None and current.mypy_sections is not None:
        violations += _compare_mypy(
            base = base.mypy_sections,
            current = current.mypy_sections,
        )
    for name, ceilings in sorted(current.legacy.items()):
        base_ceilings = base.legacy.get(name)
        if base_ceilings is not None and ceilings is not None:
            violations += _compare_ceilings(
                name = name,
                base = base_ceilings,
                current = ceilings,
            )
    return violations


def _compare_mypy(
    base: dict[str, frozenset[str]],
    current: dict[str, frozenset[str]],
) -> list[str]:
    violations = []
    if len(current) > len(base):
        violations.append(f"mypy.ini: {len(current)} секций-исключений, в базе {len(base)}")
    for section, codes in sorted(current.items()):
        added = codes - base.get(section, codes)
        if added:
            violations.append(f"mypy.ini [{section}]: новые отключённые коды {sorted(added)}")
    return violations


def _compare_ceilings(
    name: str,
    base: dict[str, int],
    current: dict[str, int],
) -> list[str]:
    violations = []
    if len(current) > len(base):
        violations.append(f"{name}: {len(current)} записей, в базе {len(base)}")
    if sum(current.values()) > sum(base.values()):
        violations.append(f"{name}: сумма потолков {sum(current.values())}, в базе {sum(base.values())}")
    violations += [
        f"{name}[{path}]: потолок {ceiling}, в базе {base[path]}"
        for path, ceiling in sorted(current.items())
        if path in base and ceiling > base[path]
    ]
    return violations


def _snapshot(reader: "_Reader") -> Snapshot:
    return Snapshot(
        noqa = _noqa_counts(reader = reader),
        ignore_imports = _ignore_imports(text = reader(".importlinter")),
        mypy_sections = _mypy_sections(text = reader("mypy.ini")),
        legacy = _legacy_lists(reader = reader),
    )


def _noqa_counts(reader: "_Reader") -> dict[str, int]:
    """Исключения на ограждающие правила ruff: `# noqa` в коде и записи per-file-ignores в pyproject.toml."""
    counts: Counter[str] = Counter()
    for path in [*reader.list_python("bot"), "main.py"]:
        text = reader(path) or ""
        for match in _NOQA.finditer(text):
            codes = {code.strip() for code in match.group("codes").split(",")}
            counts.update(codes & _GUARDED_CODES)
    pyproject = reader("pyproject.toml")
    if pyproject is not None:
        ignores = tomllib.loads(pyproject).get("tool", {}).get("ruff", {}).get("lint", {}).get("per-file-ignores", {})
        for codes in ignores.values():
            counts.update(set(codes) & _GUARDED_CODES)
    return dict(counts)


def _ignore_imports(text: str | None) -> dict[str, int] | None:
    if text is None:
        return None
    parser = configparser.ConfigParser()
    parser.read_string(text)
    return {
        section.removeprefix(_CONTRACT_PREFIX): len(
            [line for line in parser[section].get("ignore_imports", "").splitlines() if line.strip()],
        )
        for section in parser.sections()
        if section.startswith(_CONTRACT_PREFIX)
    }


def _mypy_sections(text: str | None) -> dict[str, frozenset[str]] | None:
    if text is None:
        return None
    parser = configparser.ConfigParser()
    parser.read_string(text)
    return {
        section.removeprefix(_MYPY_SECTION_PREFIX): frozenset(
            code.strip()
            for code in parser[section].get("disable_error_code", "").split(",")
            if code.strip()
        )
        for section in parser.sections()
        if section.startswith(_MYPY_SECTION_PREFIX)
    }


def _legacy_lists(reader: "_Reader") -> dict[str, dict[str, int] | None]:
    """`_LEGACY_*` из тестов ограждений: словарь «путь → потолок» или множество путей (потолок 1)."""
    result: dict[str, dict[str, int] | None] = {}
    for path in reader.list_python(_ARCHITECTURE_TESTS):
        text = reader(path)
        if text is None:
            continue
        for node in ast.parse(text).body:
            assignment = _assignment(node)
            if assignment is not None and _LEGACY_NAME.match(assignment[0]):
                result[f"{Path(path).name}:{assignment[0]}"] = _as_ceilings(assignment[1])
    return result


def _assignment(node: ast.stmt) -> tuple[str, ast.expr] | None:
    if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
        return node.targets[0].id, node.value
    if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.value is not None:
        return node.target.id, node.value
    return None


def _as_ceilings(value: ast.expr) -> dict[str, int] | None:
    # frozenset({...}) / set(...) — разбираем аргумент; frozenset() без аргументов — пусто
    if isinstance(value, ast.Call):
        if not value.args:
            return {}
        value = value.args[0]
    try:
        literal = ast.literal_eval(value)
    except ValueError:
        return None
    if isinstance(literal, dict):
        return {str(key): int(ceiling) for key, ceiling in literal.items()}
    if isinstance(literal, (set, frozenset, list, tuple)):
        return {str(item): 1 for item in literal}
    return None


class _Reader(Protocol):
    def __call__(self, path: str) -> str | None: ...

    def list_python(self, directory: str) -> list[str]: ...


class _WorktreeReader:
    def __call__(self, path: str) -> str | None:
        file = _ROOT / path
        return file.read_text(encoding = "utf-8") if file.is_file() else None

    def list_python(self, directory: str) -> list[str]:
        return sorted(path.relative_to(_ROOT).as_posix() for path in (_ROOT / directory).rglob("*.py"))


class _RevisionReader:
    def __init__(self, revision: str):
        self._revision = revision

    def __call__(self, path: str) -> str | None:
        result = subprocess.run(
            ["git", "show", f"{self._revision}:{path}"],
            cwd = _ROOT,
            capture_output = True,
            text = True,
            check = False,
        )
        return result.stdout if result.returncode == 0 else None

    def list_python(self, directory: str) -> list[str]:
        output = _git("ls-tree", "-r", "--name-only", self._revision, "--", directory)
        return [line for line in output.splitlines() if line.endswith(".py")]


def _nearest_sprint_ref() -> str | None:
    """Ветка sprint*, ближайшая к HEAD по истории: от неё ответвилась текущая работа."""
    refs = _git("for-each-ref", "--format=%(refname:short)", "refs/remotes/origin/sprint*", "refs/heads/sprint*")
    best: tuple[int, str] | None = None
    for ref in refs.split():
        merge_base = subprocess.run(
            ["git", "merge-base", "HEAD", ref],
            cwd = _ROOT,
            capture_output = True,
            text = True,
            check = False,
        ).stdout.strip()
        if not merge_base:
            continue
        distance = int(_git("rev-list", "--count", f"{merge_base}..HEAD").strip())
        if best is None or distance < best[0]:
            best = (distance, ref)
    return best[1] if best else None


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args],
        cwd = _ROOT,
        capture_output = True,
        text = True,
        check = True,
    ).stdout


if __name__ == "__main__":
    main()
