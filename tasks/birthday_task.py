import asyncio
from datetime import datetime, timezone
from datetime import time as dtime
from datetime import timedelta

import discord
from discord.ext import commands

from database import database
from loader import logger
from utils.settings import get_guild_setting
from utils.structured_log import log_event
from utils.timezones import now_in_timezone


def seconds_until_midnight():
    now = datetime.now()
    tomorrow = now + timedelta(days=1)
    midnight = datetime.combine(tomorrow.date(), dtime.min)
    return (midnight - now).total_seconds()


class BirthdayTask(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._birthday_task_started = False
        self._birthday_task = None
        self._cleanup_task = None

    async def cog_load(self):
        self._birthday_task = asyncio.create_task(self._wait_and_start_birthday_task())
        self._cleanup_task = asyncio.create_task(self.birthday_role_cleanup_loop())

    def cog_unload(self):
        if self._birthday_task:
            self._birthday_task.cancel()
        if self._cleanup_task:
            self._cleanup_task.cancel()

    async def _wait_and_start_birthday_task(self):
        await self.bot.wait_until_ready()
        await asyncio.sleep(2)  # Дать Discord API время загрузить гильдии
        if not self._birthday_task_started:
            self._birthday_task_started = True
            await self.birthday_check_loop()

    async def birthday_check_loop(self):
        while True:
            try:
                log_event(
                    logger,
                    "info",
                    "[BirthdayTask] birthday_check_loop started",
                    guilds_count=len(self.bot.guilds),
                )
                await self._check_birthdays()
            except asyncio.CancelledError:
                logger.info("[BirthdayTask] Birthday loop cancelled")
                raise
            except Exception as e:
                logger.exception(f"[BirthdayTask] Birthday loop error: {e}")
            # Проверяем периодически, потому что у серверов может быть разный часовой пояс.
            await asyncio.sleep(900)

    async def _check_birthdays(self):
        for guild in self.bot.guilds:
            guild_id = str(guild.id)
            guild_tz = await get_guild_setting(guild_id, "TIMEZONE", "UTC")
            local_now = now_in_timezone(guild_tz)
            today = local_now.strftime("%d.%m")
            today_key = local_now.strftime("%Y-%m-%d")
            birthday_channel_id = await get_guild_setting(
                guild_id, "BIRTHDAY_CHANNEL_ID"
            )
            if not birthday_channel_id:
                log_event(
                    logger,
                    "warning",
                    "[BirthdayTask] Missing BIRTHDAY_CHANNEL_ID",
                    guild_id=guild_id,
                    timezone=guild_tz,
                )
                continue
            channel = self.bot.get_channel(int(birthday_channel_id))
            if not channel:
                log_event(
                    logger,
                    "error",
                    "[BirthdayTask] Birthday channel not found",
                    guild_id=guild_id,
                    channel_id=birthday_channel_id,
                )
                continue
            user_ids = await database.run_in_thread(
                database.get_all_birthdays_on_date, guild_id, today
            )
            if not user_ids:
                logger.info(
                    f"[BirthdayTask] No birthdays today for guild {guild_id}."
                )
                continue
            for user_id in user_ids:
                delivered = await database.run_in_thread(
                    database.has_birthday_delivery, guild_id, user_id, today_key
                )
                if delivered:
                    continue

                greeting = await database.run_in_thread(
                    database.get_greeting, guild_id, user_id
                )
                if not greeting:
                    log_event(
                        logger,
                        "warning",
                        "[BirthdayTask] No greeting found",
                        guild_id=guild_id,
                        user_id=user_id,
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
                try:
                    await channel.send(embed=embed)
                    await database.run_in_thread(
                        database.mark_birthday_delivered, guild_id, user_id, today_key
                    )
                except Exception as e:
                    log_event(
                        logger,
                        "error",
                        "[BirthdayTask] Failed to send birthday message",
                        guild_id=guild_id,
                        user_id=user_id,
                        error=e,
                    )
                    continue
                birthday_role_id = await get_guild_setting(guild_id, "BIRTHDAY_ROLE_ID")
                if birthday_role_id:
                    role = guild.get_role(int(birthday_role_id))
                    if role and member:
                        try:
                            await member.add_roles(role, reason="День рождения!")
                            await database.run_in_thread(
                                database.assign_birthday_role, guild_id, user_id
                            )
                            logger.info(
                                f"[BirthdayTask] Assigned birthday role to {member} in guild {guild_id}."
                            )
                        except discord.Forbidden:
                            log_event(
                                logger,
                                "error",
                                "[BirthdayTask] Missing permission to assign birthday role",
                                guild_id=guild_id,
                                user_id=user_id,
                            )
                        except Exception as e:
                            log_event(
                                logger,
                                "error",
                                "[BirthdayTask] Unexpected error assigning role",
                                guild_id=guild_id,
                                user_id=user_id,
                                error=e,
                            )

    async def birthday_role_cleanup_loop(self):
        await self.bot.wait_until_ready()
        while True:
            try:
                await asyncio.sleep(3600)  # Проверять раз в час
                logger.info("[BirthdayTask] Checking for birthday roles to remove...")
                for guild in self.bot.guilds:
                    guild_id = str(guild.id)
                    birthday_role_id = await get_guild_setting(guild_id, "BIRTHDAY_ROLE_ID")
                    if not birthday_role_id:
                        continue
                    role = guild.get_role(int(birthday_role_id))
                    if not role:
                        continue
                    assigned_rows = await database.run_in_thread(
                        database.get_users_with_birthday_role, guild_id
                    )
                    for user_id, assigned_at in assigned_rows:
                        try:
                            assigned_time = datetime.fromisoformat(assigned_at)
                            if assigned_time.tzinfo is None:
                                assigned_time = assigned_time.replace(tzinfo=timezone.utc)
                        except Exception:
                            continue
                        if datetime.now(timezone.utc) - assigned_time >= timedelta(days=1):
                            member = guild.get_member(int(user_id))
                            if member and role in member.roles:
                                await member.remove_roles(
                                    role, reason="Снятие роли именинника через сутки"
                                )
                                logger.info(
                                    f"[BirthdayTask] Removed birthday role from {member} in guild {guild_id}."
                                )
                            await database.run_in_thread(
                                database.remove_birthday_role, guild_id, user_id
                            )
            except asyncio.CancelledError:
                logger.info("[BirthdayTask] Cleanup loop cancelled")
                raise
            except Exception as e:
                logger.exception(f"[BirthdayTask] Cleanup loop error: {e}")


async def setup(bot):
    await bot.add_cog(BirthdayTask(bot))
