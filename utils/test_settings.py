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
