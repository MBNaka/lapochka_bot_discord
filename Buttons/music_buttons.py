import discord
from discord.ui import View, Button
from discord import PartialEmoji
import wavelink
from loader import logger

class PlayerControls(View):
    def __init__(self, bot):
        super().__init__(timeout=None)  # Кнопки остаются активными
        self.bot = bot

    @discord.ui.button(emoji=PartialEmoji(name=":play_pause_button:", id=1335960491784278047), style=discord.ButtonStyle.secondary, custom_id="play_pause")
    async def play_pause(self, interaction: discord.Interaction, button: Button):
        """Переключение паузы"""
        player: wavelink.Player = interaction.guild.voice_client
        logger.debug(f"Called button_pause_play. user: {interaction.user.display_name}")

        if player and player.playing:
            await player.pause(not player.paused)
            status = "⏸ Музыка поставлена на паузу" if player.paused else "▶️ Воспроизведение продолжено"
            await interaction.response.send_message(status, ephemeral=True)
            logger.info(f"{interaction.user.display_name} paused: {status}")

    @discord.ui.button(emoji=PartialEmoji(name=":stop_button:", id=1335959100265070635), style=discord.ButtonStyle.secondary, custom_id="stop")
    async def stop(self, interaction: discord.Interaction, button: Button):
        """Остановка воспроизведения"""
        logger.debug(f"Called button_stop. user: {interaction.user.display_name}")
        player: wavelink.Player = interaction.guild.voice_client
        if not player:
            return await interaction.response.send_message(
                "Я не могу остановить плеер, потому что он не играет 😿. Попробуй включить меня", ephemeral=True)
        player.queue.reset()
        await player.stop(force=True)
        await interaction.response.send_message("Остановил плеер", ephemeral=True)
        logger.info(f"{interaction.user.display_name}: player stopped")

    @discord.ui.button(emoji=PartialEmoji(name=":skip_button", id=1335960627860078612), style=discord.ButtonStyle.secondary, custom_id="skip")
    async def skip(self, interaction: discord.Interaction, button: Button):
        """Пропуск трека"""
        logger.debug(f"Called button_skip. user: {interaction.user.display_name}")
        # Проверяем, что пользователь в голосовом канале
        if not interaction.user.voice:
            logger.info(f"{interaction.user.display_name} is not in a voice channel")
            return await interaction.response.send_message(
                "Пожалуйста, подключись к каналу, прежде чем использовать команду 😽", ephemeral=True)

        player: wavelink.Player = interaction.guild.voice_client

        if not player:
            logger.info(f"{interaction.user.display_name} player is not playing")
            return await interaction.response.send_message(
                "Я не могу пропустить трек, потому что пропускать нечего 😿. Попробуй включить меня", ephemeral=True)

        result = await player.skip(force=True)

        if not result:
            logger.info(f"{interaction.user.display_name} player is not playing")
            return await interaction.response.send_message(
                "😿 не могу пропустить трек, потому что пропускать нечего 😿. Попробуй включить меня", ephemeral=True)

        await interaction.response.send_message(f"Пропущен трек: {result.title}", ephemeral=True)
        logger.info(f"{interaction.user.display_name} skipped track: {result.title}")

    @discord.ui.button(emoji=PartialEmoji(name=":queue_button", id=1335960580502192199), style=discord.ButtonStyle.secondary, custom_id="queue")
    async def queue(self, interaction: discord.Interaction, button: Button):
        """Вывод очереди"""
        logger.debug(f"Called button_queue. user: {interaction.user.display_name}")

        player: wavelink.Player = interaction.guild.voice_client

        if not player or not player.queue:
            logger.info(f"{interaction.user.display_name} player queue is empty")
            return await interaction.response.send_message("📭 Очередь пуста.", ephemeral=True)

        queue_text = "\n".join(f"{i + 1}. {track.title}" for i, track in enumerate(player.queue))
        await interaction.response.send_message(f"🔹 **Очередь:**\n{queue_text}", ephemeral=True)
        logger.info(f"{interaction.user.display_name} player queue: {queue_text}")