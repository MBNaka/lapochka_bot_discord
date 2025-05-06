import json
import os

import aiofiles

SETTINGS_PATH = os.path.join(os.path.dirname(__file__), "../settings.json")


async def load_settings():
    if not os.path.exists(SETTINGS_PATH):
        async with aiofiles.open(SETTINGS_PATH, "w", encoding="utf-8") as f:
            await f.write(json.dumps({"guilds": {}}, ensure_ascii=False, indent=2))
    async with aiofiles.open(SETTINGS_PATH, "r", encoding="utf-8") as f:
        content = await f.read()
        return json.loads(content)


async def save_settings(settings):
    async with aiofiles.open(SETTINGS_PATH, "w", encoding="utf-8") as f:
        await f.write(json.dumps(settings, ensure_ascii=False, indent=2))


async def get_guild_setting(guild_id, key, default=None):
    settings = await load_settings()
    return settings["guilds"].get(str(guild_id), {}).get(key, default)


async def set_guild_setting(guild_id, key, value):
    settings = await load_settings()
    guild_settings = settings["guilds"].setdefault(str(guild_id), {})
    guild_settings[key] = value
    await save_settings(settings)
