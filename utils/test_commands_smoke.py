from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from commands.music_commands import MusicCommands
from commands.setup_commands import Setup
import commands.setup_commands as setup_commands_module


@pytest.mark.asyncio
async def test_queue_uses_followup_after_defer():
    cog = MusicCommands(bot=SimpleNamespace())
    track = SimpleNamespace(title="Track A")
    player = SimpleNamespace(queue=[track])

    interaction = SimpleNamespace(
        user=SimpleNamespace(name="tester"),
        guild=SimpleNamespace(voice_client=player),
        response=SimpleNamespace(defer=AsyncMock()),
        followup=SimpleNamespace(send=AsyncMock()),
    )

    await MusicCommands.queue.callback(cog, interaction)

    interaction.response.defer.assert_awaited_once()
    interaction.followup.send.assert_awaited_once()
    kwargs = interaction.followup.send.await_args.kwargs
    assert kwargs.get("ephemeral") is True
    assert "Track A" in interaction.followup.send.await_args.args[0]


@pytest.mark.asyncio
async def test_setup_status_sends_embed(monkeypatch):
    async def fake_load_settings():
        return {
            "guilds": {
                "42": {
                    "WELCOME_ENABLED": True,
                    "WELCOME_CHANNEL_ID": 111,
                    "RULES_CHANNEL_ID": 222,
                    "BIRTHDAY_CHANNEL_ID": 333,
                    "BIRTHDAY_ROLE_ID": 444,
                    "ROLE_REPORT_CHANNEL_ID": 555,
                    "WELCOME_EMBED": {"TEXT": "hello"},
                }
            }
        }

    monkeypatch.setattr(setup_commands_module, "load_settings", fake_load_settings)

    cog = Setup(bot=SimpleNamespace())
    interaction = SimpleNamespace(
        guild=SimpleNamespace(id=42),
        response=SimpleNamespace(send_message=AsyncMock()),
    )

    await Setup.setup_status.callback(cog, interaction)

    interaction.response.send_message.assert_awaited_once()
    kwargs = interaction.response.send_message.await_args.kwargs
    assert kwargs.get("ephemeral") is True
    embed = kwargs.get("embed")
    assert embed is not None
    assert "WELCOME_CHANNEL_ID: OK" in embed.description
