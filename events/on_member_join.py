import discord
from discord import Member

from loader import bot, logger
from utils.settings import get_guild_setting
from utils.messages import get_welcome_embed


@bot.event
async def on_member_join(member: Member):
    """Обработка события входа пользователя на сервер"""
    logger.info(f"Member {member.name} joined guild {member.guild.name}")

    # Проверяем, включены ли приветственные сообщения
    welcome_enabled = await get_guild_setting(member.guild.id, "WELCOME_ENABLED", False)
    if not welcome_enabled:
        logger.info(f"Welcome messages are disabled for guild {member.guild.name}")
        return

    # Получаем ID канала для приветствий
    channel_id = await get_guild_setting(member.guild.id, "WELCOME_CHANNEL_ID")
    if not channel_id:
        logger.warning(f"Welcome channel not set for guild {member.guild.name}")
        return

    channel = member.guild.get_channel(channel_id)
    if not channel:
        logger.error(
            f"Welcome channel {channel_id} not found in guild {member.guild.name}"
        )
        return
    RULES_CHANNEL_ID = await get_guild_setting(member.guild.id, "RULES_CHANNEL_ID", None)
    embed = await get_welcome_embed(member.guild.id, member.id, RULES_CHANNEL_ID)

    if embed is None:
        welcome_message = await get_guild_setting(
            member.guild.id,
            "WELCOME_MESSAGE",
            "Привет, {member}! Добро пожаловать на сервер {guild}!",
        )
        formatted_message = welcome_message.format(
            member=member.mention, guild=member.guild.name
        )
        try:
            await channel.send(formatted_message)
            logger.info(f"Sent welcome message for {member.name} in {member.guild.name}")
        except Exception as e:
            logger.error(f"Failed to send welcome message: {e}")
    else:
        try:
            await channel.send(embed=embed)
            logger.info(f"Sent welcome embed for {member.name} in {member.guild.name}")
        except Exception as e:
            logger.error(f"Failed to send welcome embed: {e}")