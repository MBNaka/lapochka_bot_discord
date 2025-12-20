import asyncio
from datetime import datetime, timedelta
import discord
from discord.ext import commands
from database import database
from loader import logger

REPEAT_DELTAS = {
    "day": timedelta(days=1),
    "week": timedelta(weeks=1),
    "month": None,  # Особая обработка
    "year": None,   # Особая обработка
}

class ScheduledMessagesTask(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._task = None

    async def cog_load(self):
        self._task = asyncio.create_task(self.scheduled_messages_loop())

    async def scheduled_messages_loop(self):
        await self.bot.wait_until_ready()
        while True:
            now = datetime.now()
            for guild in self.bot.guilds:
                guild_id = str(guild.id)
                messages = database.get_scheduled_messages(guild_id)
                for msg in messages:
                    msg_id, repeat, dt_str, channel_id, text, enabled = msg
                    if not enabled:
                        continue
                    try:
                        dt = datetime.fromisoformat(dt_str)
                    except Exception:
                        logger.error(f"[ScheduledMessagesTask] Invalid datetime: {dt_str}")
                        continue
                    if now >= dt:
                        channel = self.bot.get_channel(int(channel_id))
                        if channel:
                            try:
                                await channel.send(text)
                                logger.info(f"[ScheduledMessagesTask] Sent scheduled message {msg_id} to {channel_id} in guild {guild_id}")
                            except Exception as e:
                                logger.error(f"[ScheduledMessagesTask] Failed to send message: {e}")
                        # Обработка повторения
                        if repeat == "never":
                            database.update_scheduled_message(guild_id, msg_id, repeat, dt_str, channel_id, text, enabled=0)
                        else:
                            next_dt = self.get_next_datetime(dt, repeat)
                            if next_dt:
                                database.update_scheduled_message(guild_id, msg_id, repeat, next_dt.isoformat(), channel_id, text, enabled=1)
                            else:
                                database.update_scheduled_message(guild_id, msg_id, repeat, dt_str, channel_id, text, enabled=0)
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
