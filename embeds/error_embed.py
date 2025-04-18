import discord

async def get_embed(error):
    embed: discord.Embed = discord.Embed(title="Произошла ошибка, но у меня лапки 🐾")
    embed.description = f"Может быть тебе поможет эта информация: {error}"
    embed.colour = discord.Colour.red()
    return embed