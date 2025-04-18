import wavelink

from embeds import track_embed
from Buttons.music_buttons import PlayerControls
from loader import bot, logger

@bot.event
async def on_wavelink_track_start(payload: wavelink.TrackStartEventPayload) -> None:
    logger.info("on_wavelink_track_start")
    player: wavelink.Player | None = payload.player
    if not player:
        logger.error("Player is None")
        return

    original: wavelink.Playable | None = payload.original
    track: wavelink.Playable = payload.track

    embed, file = await track_embed.get_embed(track, original)

    await player.channel.send(embed=embed, file=file, view=PlayerControls(bot))
    logger.info(f"Track started: {track.title}")