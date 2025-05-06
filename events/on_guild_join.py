import discord

from database import database
from embeds import guild_join
from loader import bot, logger


@bot.event
async def on_guild_join(guild: discord.Guild) -> None:
    logger.info(f"Joined guild: {guild.name} (ID: {guild.id})")
    database.register_guild(str(guild.id))
    channel = guild.system_channel
    if channel is not None:
        await channel.send(embed=guild_join.get_embed(guild.id, str(guild.name)))
