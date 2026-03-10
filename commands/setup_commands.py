import discord
from discord import app_commands, Interaction
from discord.ext import commands
from discord.ui import View, Modal, TextInput

from utils.settings import load_settings, save_settings
from utils.messages import MESSAGES
from embeds import about_embed, settings_embed

class WelcomeMessageModal(Modal, title="Изменить приветственное сообщение (устар.)"):
    welcome_message = TextInput(label="Новое приветственное сообщение", style=discord.TextStyle.paragraph, required=True)

    def __init__(self, guild_id: int):
        super().__init__()
        self.guild_id = guild_id

    async def on_submit(self, interaction: Interaction):
        settings = await load_settings()
        settings["guilds"][str(self.guild_id)]["WELCOME_MESSAGE"] = self.welcome_message.value
        await save_settings(settings)
        await interaction.response.send_message(f"Приветственное сообщение обновлено!", ephemeral=True)

class WelcomeEmbedModal(Modal, title="Изменить embed приветствия"):
    def __init__(
        self,
        guild_id: int,
        text_default: str = "",
        thumbnail_default: str = "",
        image_default: str = "",
    ):
        super().__init__()
        self.guild_id = guild_id
        self.text = TextInput(
            label="Текст embed'а",
            style=discord.TextStyle.paragraph,
            required=True,
            default=text_default,
        )
        self.thumbnail_url = TextInput(
            label="Ссылка на миниатюру (THUMBNAIL_URL)",
            style=discord.TextStyle.short,
            required=False,
            default=thumbnail_default,
        )
        self.image_url = TextInput(
            label="Ссылка на изображение (IMAGE_URL)",
            style=discord.TextStyle.short,
            required=False,
            default=image_default,
        )
        self.add_item(self.text)
        self.add_item(self.thumbnail_url)
        self.add_item(self.image_url)

    async def on_submit(self, interaction: Interaction):
        settings = await load_settings()
        settings["guilds"][str(self.guild_id)]["WELCOME_EMBED"] = {
            "TEXT": self.text.value,
            "THUMBNAIL_URL": self.thumbnail_url.value,
            "IMAGE_URL": self.image_url.value
        }
        await save_settings(settings)
        await interaction.response.send_message("Embed приветствия обновлён!", ephemeral=True)

class ChannelSelectModal(Modal, title="Выбор канала приветствий"):
    def __init__(self, guild_id: int, channel_type: str):
        super().__init__()
        self.guild_id = guild_id
        self.channel_type = channel_type
        self.channel_id = TextInput(
            label="ID или #название канала",
            style=discord.TextStyle.short,
            required=True
        )
        self.add_item(self.channel_id)

    async def on_submit(self, interaction: Interaction):
        channel_id_or_name = self.channel_id.value.strip()
        guild = interaction.guild
        channel = None
        # Поиск по ID или имени
        if channel_id_or_name.isdigit():
            channel = guild.get_channel(int(channel_id_or_name))
        else:
            for ch in guild.text_channels:
                if ch.name == channel_id_or_name.lstrip('#'):
                    channel = ch
                    break
        if channel is None:
            await interaction.response.send_message("Канал не найден! Проверьте ID или имя.", ephemeral=True)
            return
        settings = await load_settings()
        settings["guilds"][str(self.guild_id)][self.channel_type] = channel.id
        await save_settings(settings)
        await interaction.response.send_message(f"Канал успешно сохранён: {channel.mention}", ephemeral=True)

class RoleSelectModal(Modal, title="Выбор роли для дней рождения"):
    def __init__(self, guild_id: int):
        super().__init__()
        self.guild_id = guild_id
        self.role_id = TextInput(
            label="ID или @название роли",
            style=discord.TextStyle.short,
            required=True
        )
        self.add_item(self.role_id)

    async def on_submit(self, interaction: Interaction):
        role_id_or_name = self.role_id.value.strip()
        guild = interaction.guild
        role = None
        # Поиск по ID или имени
        if role_id_or_name.isdigit():
            role = guild.get_role(int(role_id_or_name))
        else:
            for r in guild.roles:
                if r.name == role_id_or_name.lstrip('@'):
                    role = r
                    break
        if role is None:
            await interaction.response.send_message("Роль не найдена! Проверьте ID или имя.", ephemeral=True)
            return
        settings = await load_settings()
        settings["guilds"][str(self.guild_id)]["BIRTHDAY_ROLE_ID"] = role.id
        await save_settings(settings)
        await interaction.response.send_message(f"Роль успешно сохранена: {role.mention}", ephemeral=True)

class SetupView(View):
    def __init__(self, guild: discord.Guild):
        super().__init__(timeout=None)
        self.guild = guild

    @discord.ui.button(label="Канал приветствий", custom_id="setup_welcome_channel", style=discord.ButtonStyle.primary)
    async def setup_welcome_channel(self, interaction: Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ChannelSelectModal(self.guild.id, "WELCOME_CHANNEL_ID"))

    @discord.ui.button(label="Канал для дней рождения", custom_id="setup_birthday_channel", style=discord.ButtonStyle.primary)
    async def setup_birthday_channel(self, interaction: Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ChannelSelectModal(self.guild.id, "BIRTHDAY_CHANNEL_ID"))

    @discord.ui.button(label="Роль для дней рождения", custom_id="setup_birthday_role", style=discord.ButtonStyle.primary)
    async def setup_birthday_role(self, interaction: Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(RoleSelectModal(self.guild.id))

    @discord.ui.button(label="Изменить embed приветствия", custom_id="setup_welcome_embed", style=discord.ButtonStyle.secondary)
    async def setup_welcome_embed(self, interaction: Interaction, button: discord.ui.Button):
        settings = await load_settings()
        embed_settings = settings.get("guilds", {}).get(str(self.guild.id), {}).get("WELCOME_EMBED", {})
        await interaction.response.send_modal(
            WelcomeEmbedModal(
                self.guild.id,
                text_default=embed_settings.get("TEXT", ""),
                thumbnail_default=embed_settings.get("THUMBNAIL_URL", ""),
                image_default=embed_settings.get("IMAGE_URL", ""),
            )
        )

    @discord.ui.button(label="Изменить текст приветствия", custom_id="setup_welcome_message", style=discord.ButtonStyle.secondary)
    async def change_welcome_message(self, interaction: Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(WelcomeMessageModal(self.guild.id))

    @discord.ui.button(label="О боте", custom_id="about_bot", style=discord.ButtonStyle.success)
    async def about_bot(self, interaction: Interaction, button: discord.ui.Button):
        await interaction.response.send_message(embed=await about_embed.get_embed(), ephemeral=True)

class Setup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="setup", description="Настроить бота для сервера")
    @app_commands.checks.has_permissions(administrator=True)
    async def setup(self, interaction: Interaction):
        await interaction.response.send_message(embed=await settings_embed.get_embed(), view=SetupView(interaction.guild), ephemeral=True)

    @app_commands.command(name="setup_status", description="Показать статус конфигурации бота")
    @app_commands.checks.has_permissions(administrator=True)
    async def setup_status(self, interaction: Interaction):
        guild_id = str(interaction.guild.id)
        settings = await load_settings()
        guild_settings = settings.get("guilds", {}).get(guild_id, {})

        def mark(value):
            return "OK" if value else "MISSING"

        lines = [
            f"WELCOME_ENABLED: {mark(guild_settings.get('WELCOME_ENABLED') is not None)}",
            f"WELCOME_CHANNEL_ID: {mark(guild_settings.get('WELCOME_CHANNEL_ID'))}",
            f"RULES_CHANNEL_ID: {mark(guild_settings.get('RULES_CHANNEL_ID'))}",
            f"BIRTHDAY_CHANNEL_ID: {mark(guild_settings.get('BIRTHDAY_CHANNEL_ID'))}",
            f"BIRTHDAY_ROLE_ID: {mark(guild_settings.get('BIRTHDAY_ROLE_ID'))}",
            f"ROLE_REPORT_CHANNEL_ID: {mark(guild_settings.get('ROLE_REPORT_CHANNEL_ID'))}",
            f"WELCOME_EMBED: {mark(guild_settings.get('WELCOME_EMBED'))}",
        ]

        embed = discord.Embed(
            title="Статус настройки бота",
            description="\n".join(lines),
            color=discord.Color.blurple(),
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @setup.error
    async def setup_error(self, interaction: Interaction, error):
        if isinstance(error, app_commands.errors.MissingPermissions):
            await interaction.response.send_message(MESSAGES["no_permission"], ephemeral=True)
        else:
            await interaction.response.send_message(f"Произошла ошибка: {error}", ephemeral=True)

    @setup_status.error
    async def setup_status_error(self, interaction: Interaction, error):
        if isinstance(error, app_commands.errors.MissingPermissions):
            await interaction.response.send_message(MESSAGES["no_permission"], ephemeral=True)
        else:
            await interaction.response.send_message(f"Произошла ошибка: {error}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Setup(bot))
