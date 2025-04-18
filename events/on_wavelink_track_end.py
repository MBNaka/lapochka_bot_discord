import wavelink
from embeds import queue_empty_embed
from loader import bot, logger


@bot.event
async def on_wavelink_track_end(payload: wavelink.TrackEndEventPayload) -> None:
    logger.info(f"Track ended: {payload.track.title}. Guild: {payload.player.guild.name}")

    player: wavelink.Player | None = payload.player
    if not player:
        logger.error("Player is None.")
        return

    # Если очередь пуста, отправляем сообщение
    if player.queue.is_empty:
        logger.info(f"Queue is empty for {player.guild.name}. Waiting...")
        await player.channel.send(embed=await queue_empty_embed.get_embed())
        return

    # Если плеер не играет, воспроизводим следующий трек из очереди
    if not player.playing:
        logger.info(f"Player is not playing. Attempting to play next track in {player.guild.name}.")

        # Получаем следующий трек из очереди
        next_track = await player.queue.get_wait()  # Используем get_wait() для ожидания следующего трека
        if next_track:
            logger.info(f"Next track found in queue: {next_track.title}")
            try:
                # Останавливаем плеер и воспроизводим следующий трек
                await player.stop(force=True)  # Принудительная остановка текущего трека
                await player.play(next_track, volume=30)
                logger.info(f"Started playing {next_track.title}.")
            except Exception as e:
                logger.error(f"Error while trying to play the next track: {e}")
        else:
            logger.warning("No track found in the queue after the previous track ended.")
            return
