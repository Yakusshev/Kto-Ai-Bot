import datetime


def moscow_datetime(
    micros,
) -> datetime.datetime | None:
    if micros:
        return datetime.datetime.fromtimestamp(
            timestamp = micros / 1_000_000,
            tz = datetime.timezone(
                datetime.timedelta(hours = 3)
            ),
        )
    else:
        return None