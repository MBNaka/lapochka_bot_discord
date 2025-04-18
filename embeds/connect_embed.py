import discord

async def get_embed(title, author, album_name, source):
    embed: discord.Embed=discord.Embed(title=f"{title} by `{author}`")
    embed.colour = discord.Colour.purple()
    description = f"**Трек добавлен в очередь**"
    if album_name:
        embed.add_field(name="Альбом", value=album_name, inline=True)
    embed.add_field(name="Источник", value=source, inline=True)
    embed.description = description
    return embed