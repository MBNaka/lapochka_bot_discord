import abc


class AbstractPlayer(abc.ABC):
    @abc.abstractmethod
    async def play(self, track):
        """Воспроизводит трек."""
        pass

    @abc.abstractmethod
    async def pause(self):
        """Ставит воспроизведение на паузу."""
        pass

    @abc.abstractmethod
    async def resume(self):
        """Продолжает воспроизведение."""
        pass

    @abc.abstractmethod
    async def stop(self):
        """Останавливает воспроизведение."""
        pass

    @abc.abstractmethod
    async def skip(self):
        """Пропускает текущий трек."""
        pass

    @abc.abstractmethod
    async def set_volume(self, volume: int):
        """Устанавливает громкость."""
        pass

    @abc.abstractmethod
    def get_queue(self):
        """Возвращает текущую очередь треков."""
        pass
