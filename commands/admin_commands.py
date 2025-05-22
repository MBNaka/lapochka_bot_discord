import discord
from discord import app_commands
from discord.ext import commands

from database import database
from loader import logger
from utils.messages import ADMIN_MESSAGES


class AdminCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="add_admin", description="Добавить пользователя в список админов"
    )
    @app_commands.describe(user="Пользователь, которого нужно добавить в админы")
    async def add_admin(self, interaction: discord.Interaction, user: discord.Member):
        guild_id = str(interaction.guild.id)
        if not database.is_admin(guild_id, str(interaction.user.id)):
            logger.warning(
                f"User {interaction.user} attempted to add admin without permissions."
            )
            await interaction.response.send_message(
                ADMIN_MESSAGES["no_permission"], ephemeral=True
            )
            return
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

    @app_commands.command(
        name="remove_admin", description="Удалить пользователя из списка админов"
    )
    @app_commands.describe(user="Пользователь, которого нужно удалить из админов")
    async def remove_admin(
        self, interaction: discord.Interaction, user: discord.Member
    ):
        guild_id = str(interaction.guild.id)
        if not database.is_admin(guild_id, str(interaction.user.id)):
            logger.warning(
                f"User {interaction.user} attempted to remove admin without permissions."
            )
            await interaction.response.send_message(
                ADMIN_MESSAGES["no_permission"], ephemeral=True
            )
            return
        database.remove_admin(guild_id, str(user.id))
        logger.info(
            f"User {interaction.user} removed {user} from admin list in guild {guild_id}."
        )
        await interaction.response.send_message(
            ADMIN_MESSAGES["removed_admin"].format(mention=user.mention), ephemeral=True
        )

    @app_commands.command(
        name="edit_greeting", description="Редактировать поздравление пользователя"
    )
    @app_commands.describe(user="Пользователь, чьё поздравление нужно изменить")
    async def edit_greeting(
        self, interaction: discord.Interaction, user: discord.Member
    ):
        guild_id = str(interaction.guild.id)
        if not database.is_admin(guild_id, str(interaction.user.id)):
            logger.warning(
                f"User {interaction.user} attempted to edit greeting without permissions."
            )
            await interaction.response.send_message(
                ADMIN_MESSAGES["no_permission"], ephemeral=True
            )
            return

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

    @app_commands.command(
        name="list_admins", description="Просмотреть список администраторов"
    )
    async def list_admins(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild.id)
        if not database.is_admin(guild_id, str(interaction.user.id)):
            logger.warning(
                f"User {interaction.user} attempted to list admins without permissions."
            )
            await interaction.response.send_message(
                ADMIN_MESSAGES["no_permission"], ephemeral=True
            )
            return

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


async def setup(bot):
    await bot.add_cog(AdminCommands(bot))


import discord
from discord import app_commands
from discord.ui import Modal, TextInput

from database.database import is_admin
from loader import bot, logger
from utils.messages import MESSAGES
from utils.settings import get_guild_setting, set_guild_setting


async def isChannelEmpty (guild_id: int):
    """Function to check if a welcome channel ID is empty or not.

    Args:
        guild_id (int): ID of the guild

    Returns:
        bool: True if channel is empty, False otherwise
    """
    if await get_guild_setting(guild_id, "WELCOME_CHANNEL_ID") is None:
        return True
    return False

class WelcomeMessageModal(Modal, title="Редактирование приветствия"):
    message = TextInput(
        label="Текст приветствия",
        style=discord.TextStyle.paragraph,
        placeholder="Введите текст приветствия. Используйте {member} и {guild}",
        required=True,
        max_length=2000,
    )

    async def on_submit(self, interaction: discord.Interaction):
        await set_guild_setting(
            interaction.guild_id, "WELCOME_MESSAGE", self.message.value
        )
        await interaction.response.send_message(
            "✅ Текст приветствия обновлен!", ephemeral=True
        )


@bot.tree.command(
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
    interaction: discord.Interaction, action: str, channel: discord.TextChannel = None
):
    if not is_admin(str(interaction.guild_id), str(interaction.user.id)):
        await interaction.response.send_message(
            "❌ У вас нет прав на использование этой команды!", ephemeral=True
        )
        return

    match action:
        case "enable":
            channel_id = await get_guild_setting(interaction.guild_id, "WELCOME_CHANNEL_ID")
            if await isChannelEmpty(interaction.guild_id) is True:
                await interaction.response.send_message(
                    "❌ Укажите канал для приветствий!", ephemeral=True
                )
                return
            await set_guild_setting(interaction.guild_id, "WELCOME_ENABLED", True)
            await interaction.response.send_message(
                "✅ Приветственные сообщения включены!", ephemeral=True
            )

        case "disable":
            await set_guild_setting(interaction.guild_id, "WELCOME_ENABLED", False)
            await interaction.response.send_message(
                "✅ Приветственные сообщения выключены!", ephemeral=True
            )

        case "edit":
            current_message = await get_guild_setting(
                interaction.guild_id,
                "WELCOME_MESSAGE",
                "Привет, {member}! Добро пожаловать на сервер {guild}!",
            )
            modal = WelcomeMessageModal()
            modal.message.default = current_message
            await interaction.response.send_modal(modal)

        case "channel":
            if not channel:
                await interaction.response.send_message(
                    "❌ Укажите канал!", ephemeral=True
                )
                return
            await set_guild_setting(
                interaction.guild_id, "WELCOME_CHANNEL_ID", channel.id
            )
            await interaction.response.send_message(
                f"✅ Канал для приветствий установлен: {channel.mention}",
                ephemeral=True,
            )
