import asyncio
from datetime import datetime
from datetime import time as dtime
from datetime import timedelta

import discord
from discord.ext import commands, tasks

from database import database
from loader import bot, logger
from utils.settings import get_guild_setting


def seconds_until_midnight():
    now = datetime.now()
    tomorrow = now + timedelta(days=1)
    midnight = datetime.combine(tomorrow.date(), dtime.min)
    return (midnight - now).total_seconds()


class BirthdayTask(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def birthday_check_loop(self):
        await self.bot.wait_until_ready()
        while True:
            await asyncio.sleep(
                seconds_until_midnight()
            )  # Для теста! Для продакшена заменить на seconds_until_midnight()
            today = datetime.now().strftime("%d.%m")
            logger.info(f"[BirthdayTask] Checking birthdays for {today}")
            for guild in self.bot.guilds:
                guild_id = str(guild.id)
                birthday_channel_id = await get_guild_setting(
                    guild_id, "BIRTHDAY_CHANNEL_ID"
                )
                if not birthday_channel_id:
                    logger.warning(
                        f"[BirthdayTask] No BIRTHDAY_CHANNEL_ID for guild {guild_id}"
                    )
                    continue
                channel = self.bot.get_channel(int(birthday_channel_id))
                if not channel:
                    logger.error(
                        f"[BirthdayTask] Birthday channel not found for guild {guild_id}."
                    )
                    continue
                user_ids = database.get_all_birthdays_on_date(guild_id, today)
                if not user_ids:
                    logger.info(
                        f"[BirthdayTask] No birthdays today for guild {guild_id}."
                    )
                    continue
                for user_id in user_ids:
                    greeting = database.get_greeting(guild_id, user_id)
                    if not greeting:
                        logger.warning(
                            f"[BirthdayTask] No greeting found for user {user_id} in guild {guild_id}."
                        )
                        continue
                    embed = discord.Embed(
                        title=greeting.get("title", "С Днём рождения!"),
                        description=greeting.get("description", ""),
                        url=greeting.get("url"),
                        color=discord.Color.gold(),
                    )
                    if greeting.get("image_url"):
                        embed.set_image(url=greeting["image_url"])
                    if greeting.get("footer"):
                        embed.set_footer(text=greeting["footer"])
                    member = guild.get_member(int(user_id))
                    if member:
                        embed.set_author(
                            name=member.name,
                            icon_url=member.avatar.url if member.avatar else None,
                        )
                    await channel.send(embed=embed)
                    birthday_role_id = get_guild_setting(guild_id, "BIRTHDAY_ROLE_ID")
                    if birthday_role_id:
                        role = guild.get_role(int(birthday_role_id))
                        if role and member:
                            try:
                                await member.add_roles(role, reason="День рождения!")
                                database.assign_birthday_role(guild_id, user_id)
                                logger.info(
                                    f"[BirthdayTask] Assigned birthday role to {member} in guild {guild_id}."
                                )
                            except discord.Forbidden:
                                logger.error(
                                    f"[BirthdayTask] Missing permissions to assign role to {member} in guild {guild_id}. Skipping."
                                )
                            except Exception as e:
                                logger.error(
                                    f"[BirthdayTask] Unexpected error assigning role: {e}"
                                )

    async def birthday_role_cleanup_loop(self):
        await self.bot.wait_until_ready()
        while True:
            await asyncio.sleep(
                seconds_until_midnight()
            )  # Для теста! Для продакшена заменить на seconds_until_midnight()
            logger.info("[BirthdayTask] Checking for birthday roles to remove...")
            for guild in self.bot.guilds:
                guild_id = str(guild.id)
                birthday_role_id = await get_guild_setting(guild_id, "BIRTHDAY_ROLE_ID")
                if not birthday_role_id:
                    continue
                role = guild.get_role(int(birthday_role_id))
                if not role:
                    continue
                for user_id, assigned_at in database.get_users_with_birthday_role(
                    guild_id
                ):
                    try:
                        assigned_time = datetime.fromisoformat(assigned_at)
                    except Exception:
                        continue
                    if datetime.now() - assigned_time >= timedelta(seconds=5):
                        member = guild.get_member(int(user_id))
                        if member and role in member.roles:
                            await member.remove_roles(
                                role, reason="Снятие роли именинника через сутки"
                            )
                            logger.info(
                                f"[BirthdayTask] Removed birthday role from {member} in guild {guild_id}."
                            )
                        database.remove_birthday_role(guild_id, user_id)


async def setup(bot):
    await bot.add_cog(BirthdayTask(bot))
