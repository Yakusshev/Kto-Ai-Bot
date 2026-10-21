from datetime import datetime

import pytest

from bot.core.domain.format.ReadableDateTime import format_readable_datetime


@pytest.mark.parametrize(
    argnames = (
        "value",
        "expected",
    ),
    argvalues = [
        (datetime(2025, 1, 6, 14, 30), "2025-01-06 Понедельник 14:30"),
        (datetime(2025, 1, 8, 9, 5), "2025-01-08 Среда 09:05"),
        (datetime(2025, 1, 12, 23, 59), "2025-01-12 Воскресенье 23:59"),
    ],
)
def test_format_readable_datetime_uses_russian_weekday(
    value: datetime,
    expected: str,
) -> None:
    assert format_readable_datetime(value = value) == expected
