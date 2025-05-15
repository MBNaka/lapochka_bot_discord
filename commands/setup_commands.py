import discord
from discord import app_commands, Interaction
from discord.ext import commands
from discord.ui import View, Modal, TextInput

from utils.settings import load_settings, save_settings
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
    def __init__(self, guild_id: int):
        super().__init__()
        self.guild_id = guild_id
        # Получаем старые значения из настроек (синхронно, но вызываем асинхронно в on_ready)
        self.text = TextInput(
            label="Текст embed'а",
            style=discord.TextStyle.paragraph,
            required=True,
            default=""
        )
        self.thumbnail_url = TextInput(
            label="Ссылка на миниатюру (THUMBNAIL_URL)",
            style=discord.TextStyle.short,
            required=False,
            default=""
        )
        self.image_url = TextInput(
            label="Ссылка на изображение (IMAGE_URL)",
            style=discord.TextStyle.short,
            required=False,
            default=""
        )
        self.add_item(self.text)
        self.add_item(self.thumbnail_url)
        self.add_item(self.image_url)

    async def on_ready(self, interaction: Interaction):
        settings = await load_settings()
        embed_settings = settings["guilds"].get(str(self.guild_id), {}).get("WELCOME_EMBED", {})
        self.text.default = embed_settings.get("TEXT", "")
        self.thumbnail_url.default = embed_settings.get("THUMBNAIL_URL", "")
        self.image_url.default = embed_settings.get("IMAGE_URL", "")

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
        await interaction.response.send_modal(WelcomeEmbedModal(self.guild.id))

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

    @setup.error
    async def setup_error(self, interaction: Interaction, error):
        if isinstance(error, app_commands.errors.MissingPermissions):
            await interaction.response.send_message("❌ Только администратор сервера может использовать эту команду.", ephemeral=True)
        else:
            await interaction.response.send_message(f"Произошла ошибка: {error}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Setup(bot))
