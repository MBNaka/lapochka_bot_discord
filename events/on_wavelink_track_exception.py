import discord
import logging
import wavelink

from embeds import error_embed
from loader import bot, logger

@bot.event
async def on_wavelink_track_exception(payload: wavelink.TrackExceptionEventPayload) -> None:
    logger.info(f"on_wavelink_track_exception: {payload.exception}")
    player: wavelink.Player | None = payload.player
    track: wavelink.Playable = payload.track
    if not player:
        logging.error("Player is None")
        return await player.channel.send(embed=error_embed.get_embed("Плеер не доступен. Запустите заново"))

    if track:
        error = f"При воспроизведении трека **{track.title}** произошла ошибка: {payload.exception}"
    elif payload.exception:
        error = f"При воспроизведении произошла ошибка: {payload.exception}"
    else:
        error = "При воспроизведении произошла неизвестная ошибка"

    await player.channel.send(embed=error_embed.get_embed(error))
    await player
    logger.info(f"Player is closed: {player.guild.name}")