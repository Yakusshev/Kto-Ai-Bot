"""
FTL Stub Generator
==================
Парсит ru/strings.ftl и генерирует Strings.py с классом Strings,
который оборачивает I18nContext и предоставляет типизированный доступ к ключам.

Использование:
    python generate_stubs.py
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
        # Сохраняем порядок появления переменных, без дубликатов
        variables = tuple(dict.fromkeys(_VAR_PATTERN.findall(line)))
        bundle.keys.append(FtlKey(name=key_name, variables=variables))

    return bundle


# ---------------------------------------------------------------------------
# Code Generator
# ---------------------------------------------------------------------------

_INDENT = "    "


def _render_method(key: FtlKey, indent: str = _INDENT) -> str:
    """Генерирует один метод класса Strings для FtlKey."""
    i2 = indent + _INDENT

    if key.has_variables():
        kwargs_sig = ", ".join(f"{v}: object" for v in key.variables)
        kwargs_call = ", ".join(f"{v}={v}" for v in key.variables)
        signature = f"def {key.method_name()}(self, *, {kwargs_sig}) -> str:"
        body = f"return self._i18n.get({key.name!r}, {kwargs_call})"
    else:
        signature = f"def {key.method_name()}(self) -> str:"
        body = f"return self._i18n.get({key.name!r})"

    return "\n".join([
        f"{indent}{signature}",
        f"{i2}{body}",
        "",
    ])


def generate_stubs(bundle: FtlBundle) -> str:
    """Возвращает строку с готовым Python-кодом класса Strings."""
    source = bundle.source_path.name

    header = (
        '"""\n'
        f"Auto-generated stubs for {source}\n"
        "Do NOT edit manually — re-run generate_stubs.py to update.\n"
        '"""\n'
        "\n"
        "from __future__ import annotations\n"
        "\n"
        "from aiogram_i18n import I18nContext\n"
        "\n"
        "\n"
        "class Strings:\n"
        '    """Типизированный доступ к ключам локализации через I18nContext."""\n'
        "\n"
        "    def __init__(self, i18n: I18nContext) -> None:\n"
        "        self._i18n = i18n\n"
        "\n"
    )

    methods = "\n".join(_render_method(key) for key in bundle.keys)
    return header + methods


# ---------------------------------------------------------------------------
# Writer
# ---------------------------------------------------------------------------

def write_stubs(code: str, output_path: Path) -> None:
    output_path.write_text(code, encoding="utf-8")
    print(f"✅  Stubs written → {output_path}")


# ---------------------------------------------------------------------------
# Entry Point
# ---------------------------------------------------------------------------

def main() -> None:
    ftl_path = Path("ru/strings.ftl")
    if not ftl_path.exists():
        print(f"❌  File not found: {ftl_path}")
        sys.exit(1)

    output_path = Path("Strings.py")

    bundle = parse_ftl(ftl_path)
    code = generate_stubs(bundle)
    write_stubs(code, output_path=output_path)

    print(f"   Found {len(bundle.keys)} keys.")


if __name__ == "__main__":
    main()