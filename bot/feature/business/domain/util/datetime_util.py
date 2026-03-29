import datetime
import zoneinfo


def moscow_datetime(
    micros,
) -> datetime.datetime | None:
    if micros:
        return datetime.datetime.fromtimestamp(
            timestamp = micros / 1_000_000,
            tz = zoneinfo.ZoneInfo("Europe/Moscow"),
        )
    else:
        return None
