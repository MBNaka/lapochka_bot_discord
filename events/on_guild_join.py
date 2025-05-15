import discord
import json

from database import database
from embeds import guild_join
from loader import bot, logger
from utils.settings import load_settings, save_settings


@bot.event
async def on_guild_join(guild: discord.Guild) -> None:
    logger.info(f"Joined guild: {guild.name} (ID: {guild.id})")
    database.register_guild(str(guild.id))

    if database.is_admin(str(guild.id), str(guild.owner_id)) is False:
        database.add_admin(str(guild.id), str(guild.owner_id))
        logger.info(f"Add new admin in guild: {guild.name} (ID:{guild.id}): {guild.owner} (ID:{guild.owner_id})")
    else:
        logger.info(f"Owner guild: {guild.name} (ID:{guild.id}) is already admin")
    
    settings = await load_settings()
    new_guild_settings = {
        "GUILD_JOIN": "Привет, я твой Lapochka! Круто, что я оказался на сервере {username}. Теперь тебе нужно настроить меня, введи команду /setup, чтобы я смог помочь тебе ознакомиться с моими функциями",
        "BIRTHDAY_CHANNEL_ID": None,
        "GREETINGS_CHANNEL_ID": None,
        "BIRTHDAY_ROLE_ID": None,
        "RULES_CHANNEL_ID": None,
        "WELCOME_ENABLED": True,
        "WELCOME_CHANNEL_ID": None,
        "WELCOME_MESSAGE": "Привет, {member}! Добро пожаловать на сервер {guild}!\nНадеемся, тебе у нас понравится!",
        "WELCOME_EMBED": {
            "TEXT": ":flag_ru: Alatulya, <@{username}>! Рады приветствовать тебя на нашем сервере!\nПожалуйста, ознакомься с правилами сообщества: <#{channel}>\n\n:anusauk: Alatulya, <@456790730715955200>! We're glad to have you on the our server!\nPlease, familiarize yourself with the server rules: <#{channel}>",
            "THUMBNAIL_URL": "https://media.discordapp.net/attachments/1267898983666417786/1353734947936010351/ezgif-6fe6ac1197de50.gif?ex=6827496a&is=6825f7ea&hm=82a3758ed333686afa0c4acc1596cbe58d5a872cf0a096c7a7f46b972a0f2e87&=&width=80&height=80",
            "IMAGE_URL": "https://media.discordapp.net/attachments/1267898983666417786/1353735781184962631/ezgif-671abe36596d58.gif?ex=68274a31&is=6825f8b1&hm=4ed87f074f370f8be002edc7f78c28e3b7094cbfa3252f502d75776c8d037a8f&=&width=400&height=216"
        }
    }
    settings["guilds"][str(guild.id)] = new_guild_settings
    await save_settings(settings)

    channel = guild.system_channel
    if channel is not None:
        await channel.send(embed=await guild_join.get_embed(guild.id, str(guild.name)))
