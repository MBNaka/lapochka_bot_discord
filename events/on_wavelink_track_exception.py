import logging
from typing import Any

import discord
import wavelink

from embeds import error_embed
from loader import bot, logger


@bot.event
async def on_wavelink_track_exception(
    payload: wavelink.TrackExceptionEventPayload,
) -> None:
    logger.info(f"on_wavelink_track_exception: {payload.exception}")
    player: wavelink.Player | None = payload.player
    track: wavelink.Playable = payload.track
    if not player:
        logging.error("Player is None")
        return
    if track:
        error = f"При воспроизведении трека **{track.title}** произошла ошибка: {payload.exception}"
    elif payload.exception:
        error = f"При воспроизведении произошла ошибка: {payload.exception}"
    else:
        error = "При воспроизведении произошла неизвестная ошибка"
    try:
        embed = await error_embed.get_embed(error)
        await player.channel.send(embed=embed)
    except Exception as e:
        logger.error(f"Failed to send track exception embed: {e}")
    logger.info(f"Player is closed: {player.guild.name}")
