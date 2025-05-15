import discord

async def get_embed() -> discord.Embed:
    embed: discord.Embed = discord.Embed(
            title="О боте Lapochka",
            description="Lapochka — это многофункциональный бот для управления сервером, поздравлений, музыки и многого другого!\n\n• Приветствия новых участников\n• Поздравления с днём рождения\n• Музыкальные функции\n• Гибкая настройка через это меню\n\nИспользуйте кнопки ниже для настройки!"
        )
    embed.colour = discord.Colour.purple()
    return embed