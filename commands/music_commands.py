import discord
import wavelink
from discord import app_commands
from discord.ext import commands

from embeds import connect_embed, error_embed
from loader import logger
from utils.messages import MESSAGES
from utils.structured_log import log_event


class MusicCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def _ensure_same_voice_channel(
        self, interaction: discord.Interaction, player: wavelink.Player
    ) -> bool:
        if not interaction.user.voice or not interaction.user.voice.channel:
            await interaction.response.send_message(MESSAGES["not_in_voice"], ephemeral=True)
            return False

        if player and player.channel and interaction.user.voice.channel.id != player.channel.id:
            await interaction.response.send_message(MESSAGES["different_voice_channel"], ephemeral=True)
            return False

        return True

    @staticmethod
    def _format_queue_text(queue, limit: int = 20) -> str:
        queue_items = list(queue)
        visible = queue_items[:limit]
        queue_text = "\n".join(f"{i + 1}. {track.title}" for i, track in enumerate(visible))
        if len(queue_items) > limit:
            queue_text += f"\n... и ещё {len(queue_items) - limit} трек(ов)"
        return queue_text

    @app_commands.command(name="play", description="Включить музыку")
    @app_commands.rename(query="ссылка_или_название_трек")
    @app_commands.describe(query="Введите URL или название трека")
    async def play(self, interaction: discord.Interaction, query: str):
        await interaction.response.defer()
        logger.debug(f"{interaction.user.name} use /play. Query: {query}")

        if not interaction.user.voice:
            log_event(
                logger,
                "info",
                "User is not in voice channel",
                guild_id=interaction.guild.id,
                user_id=interaction.user.id,
            )
            return await interaction.followup.send(MESSAGES["not_in_voice"], ephemeral=True)

        player = interaction.guild.voice_client
        if not isinstance(player, wavelink.Player):
            logger.info(f"Creating a new player for {interaction.guild.name}")
            try:
                player = await interaction.user.voice.channel.connect(cls=wavelink.Player)
                player.autoplay = wavelink.AutoPlayMode.partial
                player.inactive_timeout = 60
            except Exception as e:
                log_event(
                    logger,
                    "error",
                    "Error connecting to voice channel",
                    guild_id=interaction.guild.id,
                    user_id=interaction.user.id,
                    error=e,
                )
                return await interaction.followup.send(
                    MESSAGES["connect_error"], ephemeral=True
                )

        try:
            tracks = await wavelink.Playable.search(query)
        except Exception as e:
            log_event(
                logger,
                "error",
                "Error searching for track",
                guild_id=interaction.guild.id,
                user_id=interaction.user.id,
                query=query,
                error=e,
            )
            return await interaction.followup.send(
                embed=await error_embed.get_embed(
                    "Скорее всего твоя ссылка не поддерживается. Попробуй ввести другую или найди музыку текстом"
                ),
                ephemeral=True,
            )

        if not tracks:
            logger.warning(f"{interaction.user.name} can't find track")
            return await interaction.followup.send(
                MESSAGES["track_not_found"], ephemeral=True
            )

        if isinstance(tracks, wavelink.Playlist):
            for track in tracks.tracks:
                await player.queue.put_wait(track)
            logger.info(
                f"Playlist added to queue: {tracks.name} ({len(tracks.tracks)} tracks)"
            )
            first_track = tracks.tracks[0]
            embed = await connect_embed.get_embed(
                tracks.name,
                tracks.author,
                tracks.name,
                first_track.source,
            )
            playlist_info = (
                f"Добавлен плейлист: **{tracks.name}** ({len(tracks.tracks)} треков)"
            )
        else:
            await player.queue.put_wait(tracks[0])
            logger.info(
                f"Track added to queue: {tracks[0].title}. Queue size: {len(player.queue)}"
            )
            first_track = tracks[0]
            embed = await connect_embed.get_embed(
                first_track.title,
                first_track.author,
                first_track.album.name,
                first_track.source,
            )
            playlist_info = f"Добавлен трек: **{tracks[0].title}**"

        if not player.playing:
            await player.play(player.queue.get(), volume=30)
            logger.debug(f"{interaction.user.name} started playing {first_track.title}")

        embed.description = playlist_info
        await interaction.followup.send(embed=embed, ephemeral=True)
        log_event(
            logger,
            "info",
            "Track queued",
            guild_id=interaction.guild.id,
            user_id=interaction.user.id,
            track=first_track.title,
        )

    @app_commands.command(name="skip", description="Пропустить трек")
    async def skip(self, interaction: discord.Interaction):
        logger.debug(f"{interaction.user.name} use /skip")
        player: wavelink.Player = interaction.guild.voice_client
        if not await self._ensure_same_voice_channel(interaction, player):
            logger.info(f"{interaction.user.name} is not allowed to control player")
            return

        if not player or not player.playing:
            logger.info(f"{interaction.user.name}. Player is not playing")
            return await interaction.response.send_message(
                MESSAGES["skip_nothing"], ephemeral=True
            )

        current_track = player.current
        await player.stop()

        if current_track:
            await interaction.response.send_message(
                f"Пропущен трек: {current_track.title}", ephemeral=True
            )
            logger.info(f"{interaction.user.name} success skip {current_track.title}")
        else:
            await interaction.response.send_message(
                MESSAGES["skip_nothing"], ephemeral=True
            )

    @app_commands.command(name="stop", description="Остановить плеер")
    async def stop(self, interaction: discord.Interaction):
        logger.debug(f"{interaction.user.name} use /stop")
        player: wavelink.Player = interaction.guild.voice_client
        if player and not await self._ensure_same_voice_channel(interaction, player):
            logger.info(f"{interaction.user.name} is not allowed to control player")
            return

        if not player:
            logger.info(f"{interaction.user.name}. Player is not playing")
            return await interaction.response.send_message(
                MESSAGES["player_not_playing"], ephemeral=True
            )

        last_message_id = getattr(player, "last_track_message", None)
        if last_message_id:
            try:
                last_message = await player.channel.fetch_message(last_message_id)
                await last_message.delete()
                logger.info("Deleted last track message")
            except Exception as e:
                logger.warning(f"Could not delete last track message: {e}")

        player.queue.reset()
        await player.stop()
        await interaction.response.send_message(MESSAGES["stopped"], ephemeral=True)
        logger.info(f"{interaction.user.name} success stop")

    @app_commands.command(name="pause", description="Поставить плеер в режим паузы")
    async def pause(self, interaction: discord.Interaction):
        logger.debug(f"{interaction.user.name} use /pause")
        player: wavelink.Player = interaction.guild.voice_client
        if player and not await self._ensure_same_voice_channel(interaction, player):
            logger.info(f"{interaction.user.name} is not allowed to control player")
            return

        if not player:
            logger.info(f"{interaction.user.name}. Player is not playing")
            return await interaction.response.send_message(
                MESSAGES["player_not_playing"], ephemeral=True
            )
        await player.pause(True)
        await interaction.response.send_message(MESSAGES["paused"], ephemeral=True)
        logger.info(f"{interaction.user.name} success pause")

    @app_commands.command(name="resume", description="Поставить плеер в режим воспроизведения")
    async def resume(self, interaction: discord.Interaction):
        logger.debug(f"{interaction.user.name} use /resume")
        player: wavelink.Player = interaction.guild.voice_client
        if player and not await self._ensure_same_voice_channel(interaction, player):
            logger.info(f"{interaction.user.name} is not allowed to control player")
            return

        if not player:
            logger.info(f"{interaction.user.name}. Player is not playing")
            return await interaction.response.send_message(
                MESSAGES["player_not_playing"], ephemeral=True
            )
        await player.pause(False)
        await interaction.response.send_message(MESSAGES["resumed"], ephemeral=True)
        logger.info(f"{interaction.user.name} success resume")

    @app_commands.command(
        name="volume", description="Установить уровень громкости 25, 50, 75 или 100"
    )
    @app_commands.rename(value="громкость")
    @app_commands.describe(value="Громкость может быть 25, 50, 75 или 100")
    async def volume(self, interaction: discord.Interaction, value: int):
        logger.debug(f"{interaction.user.name} use /volume {value}")
        if value not in [25, 50, 75, 100]:
            logger.warning(f"{interaction.user.name} invalid value {value}")
            return await interaction.response.send_message(
                MESSAGES["volume_invalid"], ephemeral=True
            )
        player: wavelink.Player = interaction.guild.voice_client
        if player and not await self._ensure_same_voice_channel(interaction, player):
            logger.info(f"{interaction.user.name} is not allowed to control player")
            return

        if not player:
            logger.info(f"{interaction.user.name}. Player is not playing")
            return await interaction.response.send_message(
                MESSAGES["player_not_playing"], ephemeral=True
            )
        await interaction.response.send_message(
            MESSAGES["volume_set"].format(value=value), ephemeral=True
        )
        await player.set_volume(value)
        logger.info(f"{interaction.user.name} success volume")

    @app_commands.command(name="queue", description="Показать список треков в очереди")
    async def queue(self, interaction: discord.Interaction):
        await interaction.response.defer()
        logger.debug(f"{interaction.user.name} use /queue")
        player: wavelink.Player = interaction.guild.voice_client
        if not player or not player.queue:
            logger.info(f"{interaction.user.name}. Player is not playing")
            return await interaction.followup.send(
                MESSAGES["queue_empty"], ephemeral=True
            )
        queue_text = self._format_queue_text(player.queue)
        await interaction.followup.send(
            f"🔹 **Очередь:**\n{queue_text}", ephemeral=True
        )
        logger.info(f"{interaction.user.name} success queue. Queue: {queue_text}")

async def setup(bot):
    await bot.add_cog(MusicCommands(bot))
