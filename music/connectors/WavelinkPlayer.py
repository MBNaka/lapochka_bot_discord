import wavelink
from music.player.AbstractPlayer import AbstractPlayer

class WavelinkPlayer(AbstractPlayer):
    def __init__(self, player: wavelink.Player):
        self.player = player

    async def play(self, track):
        """Воспроизводит трек."""
        await self.player.play(track)

    async def pause(self):
        """Ставит воспроизведение на паузу."""
        if self.player.is_playing():
            await self.player.pause()

    async def resume(self):
        """Продолжает воспроизведение."""
        if self.player.is_paused():
            await self.player.resume()

    async def stop(self):
        """Останавливает воспроизведение."""
        await self.player.stop()

    async def skip(self):
        """Пропускает текущий трек."""
        if self.player.queue.is_empty:
            await self.player.stop()
        else:
            next_track = await self.player.queue.get_wait()  # Получаем следующий трек
            await self.player.play(next_track)

    async def set_volume(self, volume: int):
        """Устанавливает громкость."""
        await self.player.set_volume(volume)

    def get_queue(self):
        """Возвращает текущую очередь треков."""
        return list(self.player.queue)
