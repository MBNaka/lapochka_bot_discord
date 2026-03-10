import asyncio
from datetime import datetime, timedelta
import discord
from discord.ext import commands
from database import database
from loader import logger
from utils.settings import get_guild_setting
from utils.structured_log import log_event
from utils.timezones import UTC, local_naive_to_utc

REPEAT_DELTAS = {
    "day": timedelta(days=1),
    "week": timedelta(weeks=1),
    "month": None,  # Особая обработка
    "year": None,   # Особая обработка
}

MAX_SCHEDULED_SEND_ATTEMPTS = 5

class ScheduledMessagesTask(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._task = None

    async def cog_load(self):
        self._task = asyncio.create_task(self.scheduled_messages_loop())

    def cog_unload(self):
        if self._task:
            self._task.cancel()

    async def scheduled_messages_loop(self):
        await self.bot.wait_until_ready()
        while True:
            try:
                now_utc = datetime.now(UTC)
                for guild in self.bot.guilds:
                    guild_id = str(guild.id)
                    guild_tz = await get_guild_setting(guild_id, "TIMEZONE", "UTC")
                    messages = await database.run_in_thread(
                        database.get_scheduled_messages_with_meta, guild_id
                    )
                    for msg in messages:
                        (
                            msg_id,
                            repeat,
                            dt_str,
                            channel_id,
                            text,
                            enabled,
                            _last_error,
                            attempt_count,
                            _last_attempt_at,
                        ) = msg
                        if not enabled:
                            continue
                        try:
                            dt_local = datetime.fromisoformat(dt_str)
                        except Exception:
                            log_event(
                                logger,
                                "error",
                                "[ScheduledMessagesTask] Invalid datetime",
                                guild_id=guild_id,
                                msg_id=msg_id,
                                datetime=dt_str,
                            )
                            await database.run_in_thread(
                                database.record_scheduled_message_failure,
                                guild_id,
                                msg_id,
                                f"Invalid datetime format: {dt_str}",
                            )
                            continue

                        scheduled_utc = local_naive_to_utc(dt_local, guild_tz)
                        if now_utc >= scheduled_utc:
                            sent_successfully = False
                            channel = self.bot.get_channel(int(channel_id))
                            if channel:
                                try:
                                    await channel.send(text)
                                    sent_successfully = True
                                    log_event(
                                        logger,
                                        "info",
                                        "[ScheduledMessagesTask] Sent scheduled message",
                                        guild_id=guild_id,
                                        msg_id=msg_id,
                                        channel_id=channel_id,
                                        timezone=guild_tz,
                                    )
                                except Exception as e:
                                    log_event(
                                        logger,
                                        "error",
                                        "[ScheduledMessagesTask] Failed to send message",
                                        guild_id=guild_id,
                                        msg_id=msg_id,
                                        channel_id=channel_id,
                                        error=e,
                                    )
                                    await database.run_in_thread(
                                        database.record_scheduled_message_failure,
                                        guild_id,
                                        msg_id,
                                        f"Send failed: {e}",
                                    )
                            else:
                                log_event(
                                    logger,
                                    "error",
                                    "[ScheduledMessagesTask] Channel not found",
                                    guild_id=guild_id,
                                    msg_id=msg_id,
                                    channel_id=channel_id,
                                )
                                await database.run_in_thread(
                                    database.record_scheduled_message_failure,
                                    guild_id,
                                    msg_id,
                                    f"Channel not found: {channel_id}",
                                )

                            if not sent_successfully:
                                next_attempt_count = (attempt_count or 0) + 1
                                if next_attempt_count >= MAX_SCHEDULED_SEND_ATTEMPTS:
                                    await database.run_in_thread(
                                        database.update_scheduled_message,
                                        guild_id,
                                        msg_id,
                                        repeat,
                                        dt_str,
                                        channel_id,
                                        text,
                                        0,
                                    )
                                    log_event(
                                        logger,
                                        "warning",
                                        "[ScheduledMessagesTask] Auto-disabled after failures",
                                        guild_id=guild_id,
                                        msg_id=msg_id,
                                        attempts=next_attempt_count,
                                    )
                                continue

                            await database.run_in_thread(
                                database.record_scheduled_message_success,
                                guild_id,
                                msg_id,
                            )

                            # Обработка повторения
                            if repeat == "never":
                                await database.run_in_thread(
                                    database.update_scheduled_message,
                                    guild_id,
                                    msg_id,
                                    repeat,
                                    dt_str,
                                    channel_id,
                                    text,
                                    0,
                                )
                            else:
                                next_dt = self.get_next_datetime(dt_local, repeat)
                                if next_dt:
                                    await database.run_in_thread(
                                        database.update_scheduled_message,
                                        guild_id,
                                        msg_id,
                                        repeat,
                                        next_dt.isoformat(),
                                        channel_id,
                                        text,
                                        1,
                                    )
                                else:
                                    await database.run_in_thread(
                                        database.update_scheduled_message,
                                        guild_id,
                                        msg_id,
                                        repeat,
                                        dt_str,
                                        channel_id,
                                        text,
                                        0,
                                    )
            except asyncio.CancelledError:
                logger.info("[ScheduledMessagesTask] Loop cancelled")
                raise
            except Exception as e:
                logger.exception(f"[ScheduledMessagesTask] Loop error: {e}")
            await asyncio.sleep(60)

    def get_next_datetime(self, dt, repeat):
        if repeat == "day":
            return dt + timedelta(days=1)
        elif repeat == "week":
            return dt + timedelta(weeks=1)
        elif repeat == "month":
            # Переводим на следующий месяц, сохраняя день
            month = dt.month + 1 if dt.month < 12 else 1
            year = dt.year if dt.month < 12 else dt.year + 1
            try:
                return dt.replace(year=year, month=month)
            except ValueError:
                # Если такого дня нет (например, 31 февраля), берём последний день месяца
                from calendar import monthrange
                last_day = monthrange(year, month)[1]
                return dt.replace(year=year, month=month, day=last_day)
        elif repeat == "year":
            try:
                return dt.replace(year=dt.year + 1)
            except ValueError:
                # 29 февраля -> 28 февраля
                return dt.replace(year=dt.year + 1, day=28)
        return None

async def setup(bot):
    await bot.add_cog(ScheduledMessagesTask(bot))
