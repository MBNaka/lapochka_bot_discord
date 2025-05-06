from typing import Any

import wavelink

from Buttons.music_buttons import PlayerControls
from embeds import track_embed
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

    try:
        embed, file = await track_embed.get_embed(track, original)

        # Получаем последнее сообщение из атрибута player
        last_message_id = getattr(player, "last_track_message", None)
        last_message = None

        if last_message_id:
            try:
                # Пытаемся получить предыдущее сообщение
                last_message = await player.channel.fetch_message(last_message_id)
            except Exception as e:
                logger.warning(f"Could not fetch last track message: {e}")

        if last_message:
            # Если нашли предыдущее сообщение - редактируем его
            try:
                await last_message.edit(
                    embed=embed, attachments=[file], view=PlayerControls(bot)
                )
                logger.info(f"Updated existing message for track: {track.title}")
            except Exception as e:
                logger.error(f"Failed to edit message: {e}")
                last_message = None  # Если не удалось отредактировать, отправим новое

        if not last_message:
            # Если не нашли предыдущее сообщение или не удалось отредактировать - отправляем новое
            new_message = await player.channel.send(
                embed=embed, file=file, view=PlayerControls(bot)
            )
            # Сохраняем ID нового сообщения в player
            setattr(player, "last_track_message", new_message.id)
            logger.info(f"Sent new message for track: {track.title}")

    except Exception as e:
        logger.error(f"Failed to handle track start: {e}")
