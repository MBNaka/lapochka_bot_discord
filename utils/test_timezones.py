from datetime import datetime

from utils.timezones import UTC, is_valid_timezone, local_naive_to_utc, resolve_timezone


def test_resolve_timezone_fallback_to_utc():
    tz = resolve_timezone("Invalid/Timezone")
    assert tz == UTC


def test_is_valid_timezone():
    assert is_valid_timezone("UTC") is True
    assert is_valid_timezone("Invalid/Timezone") is False


def test_local_naive_to_utc_conversion_keeps_timezone_info():
    local_dt = datetime(2026, 1, 15, 12, 0, 0)
    utc_dt = local_naive_to_utc(local_dt, "UTC")
    assert utc_dt.tzinfo is not None
    assert utc_dt.hour == 12


def test_utc_is_always_valid_timezone():
    assert is_valid_timezone("UTC") is True
