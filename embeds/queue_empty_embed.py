import discord

async def get_embed():
    embed: discord.Embed = discord.Embed(title="Очередь пуста 🐾")
    embed.description = f"Добавь новые треки с помощью команды **/play**. Я отключусь через 1 минуту неактивности."
    embed.colour = discord.Colour.purple()
    return embed