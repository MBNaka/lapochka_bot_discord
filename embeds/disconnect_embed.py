import discord

async def get_embed() -> discord.Embed:
    embed: discord.Embed = discord.Embed(title="Я отключаюсь, у меня лапки 🐾")
    embed.description = f"**Чтобы позвать меня**, используй `/play`\n Я могу играть треки из Яндекс Музыки, ВК Музыки и Youtube"
    embed.colour = discord.Colour.purple()
    return embed