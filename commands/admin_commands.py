import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import Modal, TextInput

from database import database
from database.database import is_admin
from loader import logger
from utils.messages import ADMIN_MESSAGES, MESSAGES
from utils.settings import get_guild_setting, set_guild_setting
from utils.decorators import admin_only

class AdminCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @admin_only()
    @app_commands.command(
        name="add_admin", description="Добавить пользователя в список админов"
    )
    @app_commands.describe(user="Пользователь, которого нужно добавить в админы")
    async def add_admin(self, interaction: discord.Interaction, user: discord.Member):
        guild_id = str(interaction.guild.id)
        if database.is_admin(guild_id, str(user.id)):
            await interaction.response.send_message(
                ADMIN_MESSAGES["already_admin"], ephemeral=True
            )
            return
        database.add_admin(guild_id, str(user.id))
        logger.info(
            f"User {interaction.user} added {user} as admin in guild {guild_id}."
        )
        await interaction.response.send_message(
            ADMIN_MESSAGES["added_admin"].format(mention=user.mention), ephemeral=True
        )

    @admin_only()
    @app_commands.command(
        name="remove_admin", description="Удалить пользователя из списка админов"
    )
    @app_commands.describe(user="Пользователь, которого нужно удалить из админов")
    async def remove_admin(
        self, interaction: discord.Interaction, user: discord.Member
    ):
        guild_id = str(interaction.guild.id)
        database.remove_admin(guild_id, str(user.id))
        logger.info(
            f"User {interaction.user} removed {user} from admin list in guild {guild_id}."
        )
        await interaction.response.send_message(
            ADMIN_MESSAGES["removed_admin"].format(mention=user.mention), ephemeral=True
        )

    @admin_only()
    @app_commands.command(
        name="edit_greeting", description="Редактировать поздравление пользователя"
    )
    @app_commands.describe(user="Пользователь, чьё поздравление нужно изменить")
    async def edit_greeting(
        self, interaction: discord.Interaction, user: discord.Member
    ):
        guild_id = str(interaction.guild.id)
        greeting = database.get_greeting(guild_id, str(user.id))
        if not greeting:
            logger.error(
                f"User {interaction.user} tried to edit greeting for {user}, but no greeting found in guild {guild_id}."
            )
            await interaction.response.send_message(
                ADMIN_MESSAGES["no_greeting"], ephemeral=True
            )
            return

        logger.debug(
            f"User {interaction.user} is editing greeting for {user} in guild {guild_id}."
        )

        class EditGreetingModal(discord.ui.Modal, title="Редактирование поздравления"):
            embed_title = discord.ui.TextInput(
                label="Заголовок", default=greeting.get("title", "")
            )
            url = discord.ui.TextInput(
                label="URL", default=greeting.get("url", ""), required=False
            )
            description = discord.ui.TextInput(
                label="Описание",
                default=greeting.get("description", ""),
                style=discord.TextStyle.paragraph,
            )
            image_url = discord.ui.TextInput(
                label="URL изображения",
                default=greeting.get("image_url", ""),
                required=False,
            )
            footer = discord.ui.TextInput(
                label="Footer", default=greeting.get("footer", ""), required=False
            )

            async def on_submit(self, interaction: discord.Interaction):
                updated_greeting = {
                    "title": str(self.embed_title),
                    "url": str(self.url) if self.url else None,
                    "description": str(self.description),
                    "image_url": str(self.image_url) if self.image_url else None,
                    "footer": str(self.footer) if self.footer else None,
                }
                database.set_greeting(guild_id, str(user.id), updated_greeting)
                logger.info(
                    f"User {interaction.user} updated greeting for {user} in guild {guild_id}."
                )
                await interaction.response.send_message(
                    ADMIN_MESSAGES["greeting_updated"], ephemeral=True
                )

        await interaction.response.send_modal(EditGreetingModal())

    @admin_only()
    @app_commands.command(
        name="list_admins", description="Просмотреть список администраторов"
    )
    async def list_admins(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild.id)
        with database.get_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT user_id FROM admins WHERE guild_id = ?", (guild_id,))
            rows = c.fetchall()

        if not rows:
            logger.info(f"Admin list is empty for guild {guild_id}.")
            await interaction.response.send_message(
                ADMIN_MESSAGES["admin_list_empty"], ephemeral=True
            )
            return

        admin_mentions = [f"<@{row[0]}>" for row in rows]
        admin_list = "\n".join(admin_mentions)
        logger.debug(
            f"User {interaction.user} requested admin list: {admin_list} in guild {guild_id}"
        )
        await interaction.response.send_message(
            ADMIN_MESSAGES["admin_list"].format(admin_list=admin_list), ephemeral=True
        )

    @admin_only()
    @app_commands.command(
        name="welcome_settings", description="Настройка приветственных сообщений"
    )
    @app_commands.describe(
        action="Действие: enable/disable - включить/выключить приветствия, edit - изменить текст, channel - установить канал",
        channel="Канал для приветственных сообщений (только при action=channel)",
    )
    @app_commands.choices(
        action=[
            app_commands.Choice(name="Включить приветствия", value="enable"),
            app_commands.Choice(name="Выключить приветствия", value="disable"),
            app_commands.Choice(name="Изменить текст", value="edit"),
            app_commands.Choice(name="Установить канал", value="channel"),
        ]
    )
    async def welcome_settings(
        self, interaction: discord.Interaction, action: str, channel: discord.TextChannel = None
    ):
        async def isChannelEmpty(guild_id: int):
            if await get_guild_setting(guild_id, "WELCOME_CHANNEL_ID") is None:
                return True
            return False
        match action:
            case "enable":
                channel_id = await get_guild_setting(interaction.guild_id, "WELCOME_CHANNEL_ID")
                if await isChannelEmpty(interaction.guild_id) is True:
                    await interaction.response.send_message(
                        ADMIN_MESSAGES["no_channel"], ephemeral=True
                    )
                    return
                await set_guild_setting(interaction.guild_id, "WELCOME_ENABLED", True)
                await interaction.response.send_message(
                    ADMIN_MESSAGES["enabled"], ephemeral=True
                )
            case "disable":
                await set_guild_setting(interaction.guild_id, "WELCOME_ENABLED", False)
                await interaction.response.send_message(
                    ADMIN_MESSAGES["disabled"], ephemeral=True
                )
            case "edit":
                current_message = await get_guild_setting(
                    interaction.guild_id,
                    "WELCOME_MESSAGE",
                    ADMIN_MESSAGES["default_welcome_message"] if "default_welcome_message" in ADMIN_MESSAGES else "Привет, {member}! Добро пожаловать на сервер {guild}!",
                )
                class WelcomeMessageModal(Modal, title="Редактирование приветствия"):
                    message = TextInput(
                        label="Текст приветствия",
                        style=discord.TextStyle.paragraph,
                        placeholder=ADMIN_MESSAGES["welcome_placeholder"] if "welcome_placeholder" in ADMIN_MESSAGES else "Введите текст приветствия. Используйте {member} и {guild}",
                        required=True,
                        max_length=2000,
                        default=current_message
                    )
                    async def on_submit(self, interaction: discord.Interaction):
                        await set_guild_setting(
                            interaction.guild_id, "WELCOME_MESSAGE", self.message.value
                        )
                        await interaction.response.send_message(
                            ADMIN_MESSAGES["message_updated"], ephemeral=True
                        )
                await interaction.response.send_modal(WelcomeMessageModal())
            case "channel":
                if not channel:
                    await interaction.response.send_message(
                        ADMIN_MESSAGES["no_channel"], ephemeral=True
                    )
                    return
                await set_guild_setting(
                    interaction.guild_id, "WELCOME_CHANNEL_ID", channel.id
                )
                await interaction.response.send_message(
                    ADMIN_MESSAGES["channel_set"].format(channel.mention),
                    ephemeral=True,
                )

    class WelcomeSelect(discord.ui.Select):
        def __init__(self):
            options = [
                discord.SelectOption(label="О сервере", value="about", description="Информация о сервере"),
                discord.SelectOption(label="Как получить роль", value="roles", description="Инструкция по ролям"),
                discord.SelectOption(label="Связаться с модератором", value="contact", description="Как связаться с модератором"),
            ]
            super().__init__(placeholder="Выберите интересующий пункт...", min_values=1, max_values=1, options=options)

        async def callback(self, interaction: discord.Interaction):
            responses = {
                "about": "Это сервер для общения и веселья! Здесь ты найдёшь новых друзей и интересные активности.",
                "roles": "Чтобы получить роль, перейди в канал #roles и выбери подходящую роль с помощью реакций или кнопок.",
                "contact": "Связаться с модератором можно через личные сообщения или в канале #support.",
            }
            await interaction.response.send_message(responses[self.values[0]], ephemeral=True)

    class WelcomeView(discord.ui.View):
        def __init__(self, faq_url, roles_url, rules_url):
            super().__init__(timeout=None)
            self.add_item(AdminCommands.WelcomeSelect())
            self.add_item(discord.ui.Button(label="FAQ", url=faq_url, style=discord.ButtonStyle.link))
            self.add_item(discord.ui.Button(label="Роли", url=roles_url, style=discord.ButtonStyle.link))
            self.add_item(discord.ui.Button(label="Правила", url=rules_url, style=discord.ButtonStyle.link))

    @admin_only()
    @app_commands.command(name="send_welcome_embed", description="Отправить приветственное embed-сообщение с меню и кнопками (однократно)")
    @app_commands.describe(
        channel="Канал для приветственного сообщения"
    )
    async def send_welcome_embed(self, interaction: discord.Interaction, channel: discord.TextChannel):
        guild_id = str(interaction.guild.id)
        message_id = await get_guild_setting(guild_id, "WELCOME_EMBED_MESSAGE_ID")
        if message_id:
            await interaction.response.send_message(ADMIN_MESSAGES["already_sent"], ephemeral=True)
            return
        # Настроить ссылки на FAQ, роли, правила (заменить на реальные URL или получить из настроек)
        faq_url = f"https://discord.com/channels/{guild_id}/1216022567744311316"
        roles_url = f"https://discord.com/channels/{guild_id}/1198002842502434996"
        rules_url = f"https://discord.com/channels/{guild_id}/981320862047285278"
        from embeds.settings_embed import get_welcome_embed
        embed = await get_welcome_embed()
        view = AdminCommands.WelcomeView(faq_url, roles_url, rules_url)
        sent_message = await channel.send(embed=embed, view=view)
        await set_guild_setting(guild_id, "WELCOME_EMBED_MESSAGE_ID", sent_message.id)
        await interaction.response.send_message(ADMIN_MESSAGES["welcome_sent"].format(channel.mention), ephemeral=True)

async def setup(bot):
    await bot.add_cog(AdminCommands(bot))
