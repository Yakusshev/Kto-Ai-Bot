"""
FTL Stub Generator
==================
Парсит .ftl файл локализации и генерирует Python-файл с типизированными методами.

Использование:
    python generate_stubs.py <path_to.ftl> [output_stubs.py]

Пример:
    python generate_stubs.py strings.ftl stubs.py
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path


# ---------------------------------------------------------------------------
# Domain
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class FtlKey:
    """Один ключ локализации с его переменными-аргументами."""
    name: str
    variables: tuple[str, ...]

    def method_name(self) -> str:
        """Преобразует kebab-case → snake_case."""
        return self.name.replace("-", "_")

    def has_variables(self) -> bool:
        return bool(self.variables)


@dataclass
class FtlBundle:
    """Набор всех ключей из одного .ftl файла."""
    source_path: Path
    keys: list[FtlKey] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

_KEY_PATTERN = re.compile(r"^([a-zA-Z0-9_-]+)\s*=")
_VAR_PATTERN = re.compile(r"\{\s*\$([a-zA-Z0-9_]+)\s*\}")


def parse_ftl(path: Path) -> FtlBundle:
    """Читает .ftl файл и возвращает FtlBundle со всеми ключами."""
    bundle = FtlBundle(source_path=path)
    text = path.read_text(encoding="utf-8")

    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        key_match = _KEY_PATTERN.match(line)
        if not key_match:
            continue

        key_name = key_match.group(1)
        variables = tuple(dict.fromkeys(_VAR_PATTERN.findall(line)))  # сохраняем порядок, без дубликатов
        bundle.keys.append(FtlKey(name=key_name, variables=variables))

    return bundle


# ---------------------------------------------------------------------------
# Code Generator
# ---------------------------------------------------------------------------

_INDENT = "    "


def _render_method(key: FtlKey, indent: str = _INDENT) -> str:
    """Генерирует один метод класса для FtlKey."""
    if key.has_variables():
        kwargs = ", ".join(f"{v}: object" for v in key.variables)
        signature = f"def {key.method_name()}(self, *, {kwargs}) -> str:"
        body_return = (
            f"return self._get({key.name!r}, "
            + ", ".join(f"{v}={v}" for v in key.variables)
            + ")"
        )
    else:
        signature = f"def {key.method_name()}(self) -> str:"
        body_return = f"return self._get({key.name!r})"

    lines = [
        f"{indent}{signature}",
        f"{indent}{_INDENT}{body_return}",
        "",
    ]
    return "\n".join(lines)


def generate_stubs(bundle: FtlBundle) -> str:
    """Возвращает строку с готовым Python-кодом стабов."""
    source = bundle.source_path.name
    lines: list[str] = [
        '"""',
        f"Auto-generated stubs for {source}",
        'Do NOT edit manually — re-run generate_stubs.py to update.',
        '"""',
        "",
        "from __future__ import annotations",
        "",
        "",
        "class I18n:",
        f'{_INDENT}"""Типизированный доступ к ключам локализации."""',
        "",
        f"{_INDENT}def __init__(self, get_fn) -> None:",
        f"{_INDENT}{_INDENT}# get_fn(key, **kwargs) -> str  —  любой i18n-бэкенд",
        f"{_INDENT}{_INDENT}self._get = get_fn",
        "",
    ]

    for key in bundle.keys:
        lines.append(_render_method(key))

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Writer
# ---------------------------------------------------------------------------

def write_stubs(code: str, output_path: Path) -> None:
    output_path.write_text(code, encoding="utf-8")
    print(f"✅  Stubs written → {output_path}")


# ---------------------------------------------------------------------------
# CLI Entry Point
# ---------------------------------------------------------------------------

def main() -> None:

    ftl_path = Path("ru/strings.ftl")
    if not ftl_path.exists():
        print(f"❌  File not found: {ftl_path}")
        sys.exit(1)

    output_path = Path("strings.py")

    bundle = parse_ftl(ftl_path)
    code = generate_stubs(bundle)
    write_stubs(code, output_path=output_path)

    print(f"   Found {len(bundle.keys)} keys.")


if __name__ == "__main__":
    main()