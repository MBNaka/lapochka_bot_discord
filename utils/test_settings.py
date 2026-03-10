import json

import pytest

from database import database
from utils import settings


@pytest.mark.asyncio
async def test_get_main_setting_returns_default_for_missing_key(tmp_path, monkeypatch):
    settings_file = tmp_path / "settings.json"
    settings_file.write_text(json.dumps({"guilds": {}}, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setattr(settings, "SETTINGS_PATH", str(settings_file))

    value = await settings.get_main_setting("UNKNOWN_KEY", default="fallback")
    assert value == "fallback"


@pytest.mark.asyncio
async def test_database_run_in_thread_executes_function():
    result = await database.run_in_thread(lambda a, b: a + b, 2, 3)
    assert result == 5


def test_database_scheduled_message_meta_fields(tmp_path, monkeypatch):
    db_file = tmp_path / "test.db"
    monkeypatch.setattr(database, "DB_PATH", str(db_file))

    database.init_db()
    msg_id = database.add_scheduled_message(
        "1", "never", "2026-03-10 10:00:00", "123", "hello", enabled=1
    )

    rows = database.get_scheduled_messages_with_meta("1")
    assert len(rows) == 1
    row = rows[0]
    assert row[0] == msg_id
    assert row[6] is None
    assert row[7] == 0
    assert row[8] is None

    database.record_scheduled_message_failure("1", msg_id, "boom")
    rows = database.get_scheduled_messages_with_meta("1")
    assert rows[0][6] == "boom"
    assert rows[0][7] == 1
    assert rows[0][8] is not None

    database.record_scheduled_message_success("1", msg_id)
    rows = database.get_scheduled_messages_with_meta("1")
    assert rows[0][6] is None
    assert rows[0][7] == 2


def test_database_foreign_keys_are_enabled(tmp_path, monkeypatch):
    db_file = tmp_path / "fk.db"
    monkeypatch.setattr(database, "DB_PATH", str(db_file))
    conn = database.get_connection()
    try:
        value = conn.execute("PRAGMA foreign_keys").fetchone()[0]
        assert value == 1
    finally:
        conn.close()
