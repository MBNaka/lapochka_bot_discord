import discord

async def get_embed() -> discord.Embed:
    embed: discord.Embed = discord.Embed(
        title="Настройка бота Lapochka",
        description="Добро пожаловать в меню настройки! Выберите, что хотите изменить. Подробнее о возможностях — кнопка 'О боте'."
    )
    embed.colour = discord.Colour.purple()
    return embed