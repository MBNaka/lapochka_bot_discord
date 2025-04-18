from loader import bot, logger
import wavelink
import discord
import typing

from discord import app_commands
from embeds import connect_embed, error_embed
# Команда для воспроизведения музыки
@bot.tree.command(name="play", description="Включить музыку")
@app_commands.rename(query="ссылка_или_название_трек")
@app_commands.describe(query="Введите URL или название трека")
async def play(interaction: discord.Interaction, query: str):
    await interaction.response.defer()
    logger.debug(f"{interaction.user.name} use /play. Query: {query}")

    if not interaction.user.voice:
        logger.info(f"{interaction.user.name} is not in a voice channel")
        return await interaction.followup.send(
            "Пожалуйста, подключись к каналу, прежде чем звать меня 😽", ephemeral=True
        )

    # Получаем плеер, но сначала проверяем, существует ли он
    player = interaction.guild.voice_client
    if not isinstance(player, wavelink.Player):
        logger.info(f"Creating a new player for {interaction.guild.name}")
        try:
            player = await interaction.user.voice.channel.connect(cls=wavelink.Player)

            player.autoplay = wavelink.AutoPlayMode.partial
            player.inactive_timeout = 60
        except Exception as e:
            logger.error(f"Error connecting to voice channel: {e}")
            return await interaction.followup.send(
                "Не удалось подключиться к голосовому каналу 😿", ephemeral=True
            )

    # Ищем треки (может быть одиночный трек или плейлист)
    try:
        tracks = await wavelink.Playable.search(query)
    except Exception as e:
        logger.error(f"Error searching for track: {e}")
        return await interaction.followup.send(
            embed=await error_embed.get_embed("Скорее всего твоя ссылка не поддерживается. Попробуй ввести другую или найди музыку текстом"),
            ephemeral=True
        )

    if not tracks:
        logger.warning(f"{interaction.user.name} can't find track")
        return await interaction.followup.send(
            "Я попытался поискать твой трек, но так ничего и не нашёл 😿", ephemeral=True
        )

    # Проверяем, является ли запрос плейлистом
    if isinstance(tracks, wavelink.Playlist):  # Если это плейлист
        for track in tracks.tracks:
            await player.queue.put_wait(track)
        logger.info(f"Playlist added to queue: {tracks.name} ({len(tracks.tracks)} tracks)")
        first_track = tracks.tracks[0]  # Берем первый трек для отображения
        playlist_info = f"Добавлен плейлист: **{tracks.name}** ({len(tracks.tracks)} треков)"
    else:  # Если это одиночный трек
        await player.queue.put_wait(tracks[0])
        logger.info(f"Track added to queue: {tracks[0].title}. Queue size: {len(player.queue)}")
        first_track = tracks[0]
        playlist_info = f"Добавлен трек: **{tracks[0].title}**"

    # Если плеер не играет, начинаем воспроизведение
    if not player.playing:
        await player.play(player.queue.get(), volume=30)
        logger.debug(f"{interaction.user.name} started playing {first_track.title}")

    # Отправляем embed
    embed = await connect_embed.get_embed(
        first_track.title, first_track.author, first_track.album.name, first_track.source
    )
    embed.description = playlist_info  # Добавляем инфу о плейлисте/треке
    await interaction.followup.send(embed=embed, ephemeral=True)
    logger.info(f"{interaction.user.name} success added {first_track.title}")


# Команда для пропуска трека
@bot.tree.command(name="skip", description="Пропустить трек")
async def skip(interaction: discord.Interaction):
    logger.debug(f"{interaction.user.name} use /skip")
    # Проверяем, что пользователь в голосовом канале
    if not interaction.user.voice:
        logger.info(f"{interaction.user.name} is not in a voice channel")
        return await interaction.response.send_message("Пожалуйста, подключись к каналу, прежде чем использовать команду 😽", ephemeral=True)


    player: wavelink.Player = interaction.guild.voice_client

    if not player:
        logger.info(f"{interaction.user.name}. Player is not playing")
        return await interaction.response.send_message("Я не могу пропустить трек, потому что пропускать нечего 😿. Попробуй включить меня", ephemeral=True)

    result = await player.skip(force=True)

    if not result:
        logger.info(f"{interaction.user.name}. Player is not playing. Result {result}")
        return await interaction.response.send_message("😿 не могу пропустить трек, потому что пропускать нечего 😿. Попробуй включить меня", ephemeral=True)

    await interaction.response.send_message(f"Пропущен трек: {result.title}", ephemeral=True)
    logger.info(f"{interaction.user.name} success skip {result.title}")

@bot.tree.command(name='stop', description='Остановить плеер')
async def stop(interaction: discord.Interaction):
    logger.debug(f"{interaction.user.name} use /stop")
    player: wavelink.Player = interaction.guild.voice_client
    if not player:
        logger.info(f"{interaction.user.name}. Player is not playing")
        return await interaction.response.send_message("Я не могу остановить плеер, потому что он не играет 😿. Попробуй включить меня", ephemeral=True)
    player.queue.reset()
    await player.stop()
    await interaction.response.send_message("Остановил плеер", ephemeral=True)
    logger.info(f"{interaction.user.name} success stop")

@bot.tree.command(name='pause', description='Поставить плеер в режим паузы')
async def pause(interaction: discord.Interaction):
    logger.debug(f"{interaction.user.name} use /pause")
    player: wavelink.Player = interaction.guild.voice_client
    if not player:
        logger.info(f"{interaction.user.name}. Player is not playing")
        return await interaction.response.send_message("Я не могу поставить плеер в режим паузы, потому что он не играет 😿. Попробуй включить меня", ephemeral=True)
    await player.pause(True)
    await interaction.response.send_message("Поставил на паузу", ephemeral=True)
    logger.info(f"{interaction.user.name} success pause")

@bot.tree.command(name='resume', description='Поставить плеер в режим воспроизведения')
async def resume(interaction: discord.Interaction):
    logger.debug(f"{interaction.user.name} use /resume")
    player: wavelink.Player = interaction.guild.voice_client
    if not player:
        logger.info(f"{interaction.user.name}. Player is not playing")
        return await interaction.response.send_message("Я не могу поставить плеер в режим воспроизведения, потому что он не играет 😿. Попробуй включить меня", ephemeral=True)
    await player.pause(False)
    await interaction.response.send_message("Возобновил трек", ephemeral=True)
    logger.info(f"{interaction.user.name} success resume")

@bot.tree.command(name='volume', description='Установить уровень громкости 25, 50, 75 или 100')
@app_commands.rename(value="громкость")
@app_commands.describe(value="Громкость может быть 25, 50, 75 или 100")
async def volume(interaction: discord.Interaction, value: int):
    logger.debug(f"{interaction.user.name} use /volume {value}")
    if value not in [25, 50, 75, 100]:
        logger.warning(f"{interaction.user.name} invalid value {value}")
        return await interaction.response.send_message("Уровень громкости должен быть 25, 50, 75 или 100", ephemeral=True)
    if value == 25:
        result = 25
    elif value == 50:
        result = 50
    elif value == 75:
        result = 75
    elif value == 100:
        result = 100
    player: wavelink.Player = interaction.guild.voice_client
    if not player:
        logger.info(f"{interaction.user.name}. Player is not playing")
        return await interaction.response.send_message("Я не могу установить уровень громкости, потому что музыка не играет 😿. Попробуй включить меня", ephemeral=True)
    await interaction.response.send_message(f"Установил уровень громкости на {result}%", ephemeral=True)
    await player.set_volume(value)
    logger.info(f"{interaction.user.name} success volume")

@bot.tree.command(name='queue', description='Показать список треков в очереди')
async def queue(interaction: discord.Interaction):
    await interaction.response.defer()
    """Показать очередь"""
    logger.debug(f"{interaction.user.name} use /queue")
    player: wavelink.Player = interaction.guild.voice_client

    if not player or not player.queue:
        logger.info(f"{interaction.user.name}. Player is not playing")
        return await interaction.response.send_message("📭 Очередь пуста.", ephemeral=True)

    queue_text = "\n".join(f"{i + 1}. {track.title}" for i, track in enumerate(player.queue))
    await interaction.response.send_message(f"🔹 **Очередь:**\n{queue_text}", ephemeral=True)
    logger.info(f"{interaction.user.name} success queue. Queue: {queue_text}")
