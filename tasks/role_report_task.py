import discord
from discord.ext import tasks, commands
import asyncio
from utils import settings as settings_utils

class RoleReportTask(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.role_reporter.start()

    def cog_unload(self):
        self.role_reporter.cancel()

    @tasks.loop(hours=1)
    async def role_reporter(self):
        await self.bot.wait_until_ready()
        settings = await settings_utils.load_settings()
        # Поддержка нескольких серверов (guilds)
        for guild_id, guild_settings in settings.get("guilds", {}).items():
            channel_id = guild_settings.get("ROLE_REPORT_CHANNEL_ID")
            role_groups = guild_settings.get("ROLE_GROUPS", [])
            # Если role_groups строка (например, из старого settings), пробуем преобразовать
            if isinstance(role_groups, str):
                import ast
                try:
                    role_groups = ast.literal_eval(role_groups)
                except Exception:
                    role_groups = []
            if not channel_id or not role_groups:
                continue
            guild = self.bot.get_guild(int(guild_id))
            if not guild:
                continue
            channel = guild.get_channel(channel_id)
            if not channel:
                continue
            for group in role_groups:
                group_name = group.get("name", "Группа")
                role_ids = group.get("roles", [])
                message_id = group.get("message_id", 0)
                lines = [f"# {group_name}"]
                for role_id in role_ids:
                    role = guild.get_role(role_id)
                    if not role:
                        continue
                    count = sum(1 for m in guild.members if role in m.roles)
                    lines.append(f"**{role.name}**: {count}")
                text = "\n".join(lines)
                # Обновление или отправка сообщения
                msg = None
                if message_id:
                    try:
                        msg = await channel.fetch_message(message_id)
                        await msg.edit(content=text)
                    except Exception:
                        msg = None
                if not msg:
                    msg = await channel.send(text)
                    group["message_id"] = msg.id
            # Сохраняем обновлённые message_id
            await settings_utils.set_guild_setting(guild_id, "ROLE_GROUPS", role_groups)

async def setup(bot):
    await bot.add_cog(RoleReportTask(bot))
