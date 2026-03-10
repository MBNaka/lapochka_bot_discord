from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

UTC = timezone.utc


def resolve_timezone(tz_name: str | None):
    if not tz_name or tz_name.upper() == "UTC":
        return UTC
    try:
        return ZoneInfo(tz_name)
    except ZoneInfoNotFoundError:
        return UTC


def is_valid_timezone(tz_name: str) -> bool:
    if tz_name.upper() == "UTC":
        return True
    try:
        ZoneInfo(tz_name)
        return True
    except ZoneInfoNotFoundError:
        return False


def local_naive_to_utc(dt_local_naive: datetime, tz_name: str | None) -> datetime:
    tz = resolve_timezone(tz_name)
    return dt_local_naive.replace(tzinfo=tz).astimezone(UTC)


def now_in_timezone(tz_name: str | None) -> datetime:
    return datetime.now(resolve_timezone(tz_name))
