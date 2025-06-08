import discord

async def get_embed() -> discord.Embed:
    embed: discord.Embed = discord.Embed(
        title="Настройка бота Lapochka",
        description="Добро пожаловать в меню настройки! Выберите, что хотите изменить. Подробнее о возможностях — кнопка 'О боте'.\n\nПанель управления ботом: http://193.222.62.167:8550/ \n\n Задать пароль для панели: /set_panel_password"
    )
    embed.colour = discord.Colour.purple()
    return embed