import discord
import wavelink
from discord.ext import commands
from loader import EXTENSIONS, LAVALINK_HOST, LAVALINK_PASSWORD, init_aiohttp_session, logger
from utils.settings import load_settings, save_settings, get_guild_setting
from utils.messages import get_welcome_embed
from embeds import guild_join, queue_empty_embed, track_embed
import embeds.disconnect_embed

class Events(commands.Cog):
    """Cog для всех Discord событий: on_ready, on_guild_join, on_member_join, события Wavelink и др."""
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        """Инициализация бота, подключение к Lavalink, синхронизация команд."""
        discord.utils.setup_logging(level=logger.level)
        for extention in EXTENSIONS:
            try:
                await self.bot.load_extension(extention)
                logger.info(f"Extension {extention} loaded successfully.")
            except Exception as e:
                logger.error(f"Failed to load extension {extention}: {e}")
        await init_aiohttp_session()
        logger.info("Logged in: %s | %s", self.bot.user, self.bot.user.id)
        selected_node = {"host": LAVALINK_HOST, "password": LAVALINK_PASSWORD}
        node = wavelink.Node(
            uri=selected_node["host"],
            password=selected_node["password"],
        )
        await wavelink.Pool.connect(nodes=[node], client=self.bot)
        logger.info("Lavalink node connected!")
        await self.bot.tree.sync()
        logger.info("Slash commands synced!")
        logger.info(f"Bot is ready. Logged in as {self.bot.user}")
        # Запуск задач для поздравлений и снятия роли именинника
        birthday_cog = self.bot.get_cog("BirthdayTask")
        if birthday_cog and not hasattr(birthday_cog, "_tasks_started"):
            birthday_cog._tasks_started = True
            self.bot.loop.create_task(birthday_cog.birthday_check_loop())
            self.bot.loop.create_task(birthday_cog.birthday_role_cleanup_loop())

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        """Обработка события присоединения к новому серверу."""
        logger.info(f"Joined guild: {guild.name} (ID: {guild.id})")
        from database import database
        database.register_guild(str(guild.id))
        if database.is_admin(str(guild.id), str(guild.owner_id)) is False:
            database.add_admin(str(guild.id), str(guild.owner_id))
            logger.info(f"Add new admin in guild: {guild.name} (ID:{guild.id}): {guild.owner} (ID:{guild.owner_id})")
        else:
            logger.info(f"Owner guild: {guild.name} (ID:{guild.id}) is already admin")
        settings = await load_settings()
        new_guild_settings = {
            "GUILD_JOIN": "Привет, я твой Lapochka! Круто, что я оказался на сервере {username}. Теперь тебе нужно настроить меня, введи команду /setup, чтобы я смог помочь тебе ознакомиться с моими функциями",
            "BIRTHDAY_CHANNEL_ID": None,
            "GREETINGS_CHANNEL_ID": None,
            "BIRTHDAY_ROLE_ID": None,
            "RULES_CHANNEL_ID": None,
            "WELCOME_ENABLED": True,
            "WELCOME_CHANNEL_ID": None,
            "WELCOME_MESSAGE": "Привет, {member}! Добро пожаловать на сервер {guild}!\nНадеемся, тебе у нас понравится!",
            "WELCOME_EMBED": {
                "TEXT": ":flag_ru: Alatulya, <@{username}>! Рады приветствовать тебя на нашем сервере!\nПожалуйста, ознакомься с правилами сообщества: <#{channel}>\n\n:anusauk: Alatulya, <@456790730715955200>! We're glad to have you on the our server!\nPlease, familiarize yourself with the server rules: <#{channel}>",
                "THUMBNAIL_URL": "https://media.discordapp.net/attachments/1267898983666417786/1353734947936010351/ezgif-6fe6ac1197de50.gif?ex=6827496a&is=6825f7ea&hm=82a3758ed333686afa0c4acc1596cbe58d5a872cf0a096c7a7f46b972a0f2e87&=&width=80&height=80",
                "IMAGE_URL": "https://media.discordapp.net/attachments/1267898983666417786/1353735781184962631/ezgif-671abe36596d58.gif?ex=68274a31&is=6825f8b1&hm=4ed87f074f370f8be002edc7f78c28e3b7094cbfa3252f502d75776c8d037a8f&=&width=400&height=216"
            }
        }
        settings["guilds"][str(guild.id)] = new_guild_settings
        await save_settings(settings)
        channel = guild.system_channel
        if channel is not None:
            await channel.send(embed=await guild_join.get_embed(guild))

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """Обработка события входа нового участника на сервер."""
        logger.info(f"Member {member.name} joined guild {member.guild.name}")
        welcome_enabled = await get_guild_setting(member.guild.id, "WELCOME_ENABLED", False)
        if not welcome_enabled:
            logger.info(f"Welcome messages are disabled for guild {member.guild.name}")
            return
        channel_id = await get_guild_setting(member.guild.id, "WELCOME_CHANNEL_ID")
        if not channel_id:
            logger.warning(f"Welcome channel not set for guild {member.guild.name}")
            return
        channel = member.guild.get_channel(channel_id)
        if not channel:
            logger.error(f"Welcome channel {channel_id} not found in guild {member.guild.name}")
            return
        RULES_CHANNEL_ID = await get_guild_setting(member.guild.id, "RULES_CHANNEL_ID", None)
        embed = await get_welcome_embed(member.guild.id, member.id, RULES_CHANNEL_ID)
        if embed is None:
            welcome_message = await get_guild_setting(
                member.guild.id,
                "WELCOME_MESSAGE",
                "Привет, {member}! Добро пожаловать на сервер {guild}!",
            )
            formatted_message = welcome_message.format(
                member=member.mention, guild=member.guild.name
            )
            try:
                await channel.send(formatted_message)
                logger.info(f"Sent welcome message for {member.name} in {member.guild.name}")
            except Exception as e:
                logger.error(f"Failed to send welcome message: {e}")
        else:
            try:
                await channel.send(embed=embed)
                logger.info(f"Sent welcome embed for {member.name} in {member.guild.name}")
            except Exception as e:
                logger.error(f"Failed to send welcome embed: {e}")

    @commands.Cog.listener()
    async def on_wavelink_inactive_player(self, player: wavelink.Player):
        """Обработка события бездействующего плеера Wavelink."""
        logger.info(f"Player is inactive: {player.guild.name}")
        try:
            embed = await embeds.disconnect_embed.get_embed()
            await player.channel.send(embed=embed)
        except Exception as e:
            logger.error(f"Failed to send disconnect embed: {e}")
        try:
            await player.disconnect()
        except Exception as e:
            logger.error(f"Failed to disconnect player: {e}")

    @commands.Cog.listener()
    async def on_wavelink_track_end(self, payload: wavelink.TrackEndEventPayload):
        """Обработка события окончания трека Wavelink."""
        logger.info(
            f"Track ended: {payload.track.title}. Guild: {payload.player.guild.name}"
        )
        player = payload.player
        if not player:
            logger.error("Player is None.")
            return
        if player.queue.is_empty:
            logger.info(f"Queue is empty for {player.guild.name}. Disconnecting...")
            try:
                last_message_id = getattr(player, "last_track_message", None)
                if last_message_id:
                    try:
                        last_message = await player.channel.fetch_message(last_message_id)
                        await last_message.delete()
                        logger.info("Deleted last track message")
                    except Exception as e:
                        logger.warning(f"Could not delete last track message: {e}")
                await player.channel.send(embed=await queue_empty_embed.get_embed())
                logger.info("Player disconnected after queue end.")
            except Exception as e:
                logger.error(f"Error during empty queue handling: {e}")
            return

    @commands.Cog.listener()
    async def on_wavelink_track_start(self, payload: wavelink.TrackStartEventPayload):
        """Обработка события начала трека Wavelink."""
        logger.info("on_wavelink_track_start")
        player = payload.player
        if not player:
            logger.error("Player is None")
            return
        original = payload.original
        track = payload.track
        try:
            embed, file = await track_embed.get_embed(track, original)
            last_message_id = getattr(player, "last_track_message", None)
            last_message = None
            if last_message_id:
                try:
                    last_message = await player.channel.fetch_message(last_message_id)
                except Exception as e:
                    logger.warning(f"Could not fetch last track message: {e}")
            from Buttons.music_buttons import PlayerControls
            if last_message:
                try:
                    await last_message.edit(
                        embed=embed, attachments=[file], view=PlayerControls(self.bot)
                    )
                    logger.info(f"Updated existing message for track: {track.title}")
                except Exception as e:
                    logger.warning(f"Could not edit last track message: {e}")
            else:
                try:
                    msg = await player.channel.send(
                        embed=embed, file=file, view=PlayerControls(self.bot)
                    )
                    player.last_track_message = msg.id
                    logger.info(f"Sent new message for track: {track.title}")
                except Exception as e:
                    logger.error(f"Failed to send new track message: {e}")
        except Exception as e:
            logger.error(f"Failed to send track embed: {e}")

    @commands.Cog.listener()
    async def on_wavelink_track_exception(self, payload: wavelink.TrackExceptionEventPayload):
        """Обработка ошибки при воспроизведении трека Wavelink."""
        from embeds import error_embed
        logger.info(f"on_wavelink_track_exception: {payload.exception}")
        player = payload.player
        track = payload.track
        if not player:
            logger.error("Player is None")
            return
        if track:
            error = f"При воспроизведении трека **{track.title}** произошла ошибка: {payload.exception}"
        elif payload.exception:
            error = f"При воспроизведении произошла ошибка: {payload.exception}"
        else:
            error = "При воспроизведении произошла неизвестная ошибка"
        try:
            embed = await error_embed.get_embed(error)
            await player.channel.send(embed=embed)
        except Exception as e:
            logger.error(f"Failed to send track exception embed: {e}")
        logger.info(f"Player is closed: {player.guild.name}")

async def setup(bot):
    """Регистрация Cog событий."""
    await bot.add_cog(Events(bot))
