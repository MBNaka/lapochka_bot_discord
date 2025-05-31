import re
import discord
from discord import Interaction, app_commands
from discord.ext import commands

from database import database
from loader import logger


class BirthdayModal(discord.ui.Modal, title="Регистрация дня рождения"):
    def __init__(self, guild_id, user_id, username):
        super().__init__()
        self.guild_id = guild_id
        self.user_id = user_id
        self.username = username
        self.birthday = discord.ui.TextInput(
            label="Введите дату рождения (дд.мм.гггг)",
            placeholder="Например, 19.04.2000",
            required=True,
            max_length=10,
        )
        self.add_item(self.birthday)

    async def on_submit(self, interaction: Interaction):
        date_pattern = r"^(0[1-9]|[12][0-9]|3[01])\.(0[1-9]|1[0-2])\.(19|20)\d{2}$"
        if not re.match(date_pattern, str(self.birthday.value)):
            await interaction.response.send_message(
                "❌ Неверный формат даты. Используйте дд.мм.гггг", ephemeral=True
            )
            logger.info(
                f"User {interaction.user.name} provided invalid date format: {self.birthday.value}"
            )
            return
        database.set_birthday(self.guild_id, self.user_id, str(self.birthday.value))
        await interaction.response.send_message(
            f"✅ День рождения {self.birthday.value} успешно зарегистрирован!",
            ephemeral=True,
        )
        logger.info(
            f"User {interaction.user.name} registered birthday: {self.birthday.value}"
        )


class Birthday(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="birthday", description="Зарегистрировать свой день рождения"
    )
    async def birthday(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild.id)
        user_id = str(interaction.user.id)
        username = str(interaction.user.global_name or interaction.user.name)
        database.register_user(guild_id, user_id, username)
        await interaction.response.send_modal(
            BirthdayModal(guild_id=guild_id, user_id=user_id, username=username)
        )


async def setup(bot):
    await bot.add_cog(Birthday(bot))
