import discord

from utils.messages import get_guild_join_message


async def get_embed(guild_id: int, username: str) -> discord.Embed:
    embed: discord.Embed = discord.Embed()
    embed.description = await get_guild_join_message(guild_id, username)
    embed.colour = discord.Colour.purple()
    return embed
