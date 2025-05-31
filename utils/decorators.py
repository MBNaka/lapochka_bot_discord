from functools import wraps
from database.database import is_admin
from loader import logger
import discord


def admin_only():
    """Декоратор для проверки прав администратора на сервере."""
    def decorator(func):
        @wraps(func)
        async def wrapper(self, interaction: discord.Interaction, *args, **kwargs):
            guild_id = str(interaction.guild.id)
            user_id = str(interaction.user.id)
            if not is_admin(guild_id, user_id):
                logger.warning(f"User {interaction.user} tried to use admin command without permissions.")
                await interaction.response.send_message(
                    "❌ У вас нет прав на использование этой команды!", ephemeral=True
                )
                return
            return await func(self, interaction, *args, **kwargs)
        return wrapper
    return decorator
