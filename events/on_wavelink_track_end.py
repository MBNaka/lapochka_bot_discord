from typing import Any

import wavelink

from embeds import queue_empty_embed
from loader import bot, logger


@bot.event
async def on_wavelink_track_end(payload: wavelink.TrackEndEventPayload) -> None:
    logger.info(
        f"Track ended: {payload.track.title}. Guild: {payload.player.guild.name}"
    )
    player: wavelink.Player | None = payload.player

    if not player:
        logger.error("Player is None.")
        return

    # Если очередь пуста
    if player.queue.is_empty:
        logger.info(f"Queue is empty for {player.guild.name}. Disconnecting...")
        try:
            # Получаем и удаляем последнее сообщение с треком
            last_message_id = getattr(player, "last_track_message", None)
            if last_message_id:
                try:
                    last_message = await player.channel.fetch_message(last_message_id)
                    await last_message.delete()
                    logger.info("Deleted last track message")
                except Exception as e:
                    logger.warning(f"Could not delete last track message: {e}")

            # Отправляем сообщение о пустой очереди и отключаемся
            await player.channel.send(embed=await queue_empty_embed.get_embed())
            await player.disconnect()
            logger.info("Player disconnected after queue end.")
        except Exception as e:
            logger.error(f"Error during empty queue handling: {e}")
        return

    # Проверяем, не запущен ли уже следующий трек
    if not player.playing and not player.paused:
        logger.info(f"Starting next track in {player.guild.name}")
        try:
            next_track = await player.queue.get_wait()
            if next_track:
                await player.play(next_track, volume=30)
                logger.info(f"Started playing next track: {next_track.title}")
            else:
                logger.warning("No track found in queue despite queue not being empty")
        except Exception as e:
            logger.error(f"Error while getting next track from queue: {e}")
