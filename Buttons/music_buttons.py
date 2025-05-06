import discord
import wavelink
from discord import PartialEmoji
from discord.ui import Button, View

from loader import logger
from utils.messages import MESSAGES


class PlayerControls(View):
    def __init__(self, bot):
        super().__init__(timeout=None)  # Кнопки остаются активными
        self.bot = bot

    @discord.ui.button(
        emoji=PartialEmoji(name=":play_pause_button:", id=1335960491784278047),
        style=discord.ButtonStyle.secondary,
        custom_id="play_pause",
    )
    async def play_pause(self, interaction: discord.Interaction, button: Button):
        """Переключение паузы"""
        player: wavelink.Player = interaction.guild.voice_client
        logger.debug(f"Called button_pause_play. user: {interaction.user.display_name}")

        if player and player.playing:
            await player.pause(not player.paused)
            status = (
                "⏸ Музыка поставлена на паузу"
                if player.paused
                else "▶️ Воспроизведение продолжено"
            )
            await interaction.response.send_message(status, ephemeral=True)
            logger.info(f"{interaction.user.display_name} paused: {status}")

    @discord.ui.button(
        emoji=PartialEmoji(name=":stop_button:", id=1335959100265070635),
        style=discord.ButtonStyle.secondary,
        custom_id="stop",
    )
    async def stop(self, interaction: discord.Interaction, button: Button):
        """Остановка воспроизведения"""
        logger.debug(f"Called button_stop. user: {interaction.user.display_name}")
        player: wavelink.Player = interaction.guild.voice_client
        if not player:
            return await interaction.response.send_message(
                MESSAGES["player_not_playing"], ephemeral=True
            )
        player.queue.reset()
        await player.stop(force=True)
        await interaction.response.send_message(MESSAGES["stopped"], ephemeral=True)
        logger.info(f"{interaction.user.display_name}: player stopped")

    @discord.ui.button(
        emoji=PartialEmoji(name=":skip_button", id=1335960627860078612),
        style=discord.ButtonStyle.secondary,
        custom_id="skip",
    )
    async def skip(self, interaction: discord.Interaction, button: Button):
        """Пропуск трека"""
        logger.debug(f"Called button_skip. user: {interaction.user.display_name}")
        if not interaction.user.voice:
            logger.info(f"{interaction.user.display_name} is not in a voice channel")
            return await interaction.response.send_message(
                MESSAGES["not_in_voice"], ephemeral=True
            )

        player: wavelink.Player = interaction.guild.voice_client

        if not player or not player.playing:
            logger.info(f"{interaction.user.display_name} player is not playing")
            return await interaction.response.send_message(
                MESSAGES["skip_nothing"], ephemeral=True
            )

        current_track = player.current
        await player.stop()

        if current_track:
            await interaction.response.send_message(
                f"Пропущен трек: {current_track.title}", ephemeral=True
            )
            logger.info(
                f"{interaction.user.display_name} skipped track: {current_track.title}"
            )
        else:
            await interaction.response.send_message(
                MESSAGES["skip_nothing"], ephemeral=True
            )

    @discord.ui.button(
        emoji=PartialEmoji(name=":queue_button", id=1335960580502192199),
        style=discord.ButtonStyle.secondary,
        custom_id="queue",
    )
    async def queue(self, interaction: discord.Interaction, button: Button):
        """Вывод очереди"""
        logger.debug(f"Called button_queue. user: {interaction.user.display_name}")

        player: wavelink.Player = interaction.guild.voice_client

        if not player or not player.queue:
            logger.info(f"{interaction.user.display_name} player queue is empty")
            return await interaction.response.send_message(
                MESSAGES["queue_empty"], ephemeral=True
            )

        queue_text = "\n".join(
            f"{i + 1}. {track.title}" for i, track in enumerate(player.queue)
        )
        await interaction.response.send_message(
            f"🔹 **Очередь:**\n{queue_text}", ephemeral=True
        )
        logger.info(f"{interaction.user.display_name} player queue: {queue_text}")
