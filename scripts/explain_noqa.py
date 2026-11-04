"""Дописывает к `# noqa: C901 / PLR0913 / TID251` в bot/ и main.py пояснение по-русски (AT-90).

ruff не принимает названия правил вместо кодов, но текст после кодов не мешает:
`# noqa: C901 — сложная функция`. Пометки, у которых пояснение уже есть, не трогаются.

    python -m scripts.explain_noqa
"""
import re
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_SCAN_PATHS = (
    "bot",
    "main.py",
)
_EXPLANATIONS = {
    "C901": "сложная функция",
    "PLR0913": "много аргументов",
    "TID251": "запрещённый API",
}
# Пометка, после кодов которой ничего нет до конца строки
_BARE_NOQA = re.compile(r"(?P<noqa>#\s*noqa:\s*(?P<codes>[A-Z0-9]+(?:\s*,\s*[A-Z0-9]+)*))\s*$")


def main() -> None:
    changed = 0
    for path in _python_files():
        lines = path.read_text(encoding = "utf-8").splitlines(keepends = True)
        for index, line in enumerate(lines):
            explained = _explain(line)
            if explained != line:
                lines[index] = explained
                changed += 1
        path.write_text("".join(lines), encoding = "utf-8")
    print(f"Пояснено пометок: {changed}")


def _python_files() -> list[Path]:
    files: list[Path] = []
    for name in _SCAN_PATHS:
        target = _ROOT / name
        files.extend([target] if target.is_file() else sorted(target.rglob("*.py")))
    return files


def _explain(line: str) -> str:
    body = line.rstrip("\n")
    match = _BARE_NOQA.search(body)
    if match is None:
        return line
    codes = [code.strip() for code in match.group("codes").split(",")]
    reasons = [_reason(code = code, line = body) for code in codes if code in _EXPLANATIONS]
    if not reasons:
        return line
    return f"{body[:match.end('noqa')]} — {', '.join(reasons)}" + line[len(body):]


def _reason(code: str, line: str) -> str:
    if code != "TID251":
        return _EXPLANATIONS[code]
    if "environ" in line or "getenv" in line:
        return f"{_EXPLANATIONS[code]}: env"
    return f"{_EXPLANATIONS[code]}: datetime.now"


if __name__ == "__main__":
    main()
