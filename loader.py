import logging
import os
from logging.handlers import RotatingFileHandler

import aiohttp
import discord
from discord.ext import commands
from dotenv import load_dotenv

os.makedirs("logs", exist_ok=True)

# Общий формат логов
log_formatter = logging.Formatter(
    "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)

# Логгер для бота (основной)
bot_log_handler = RotatingFileHandler(
    filename="logs/bot.log",
    maxBytes=5 * 1024 * 1024,  # 5MB
    backupCount=10,
    encoding="utf-8",
)
bot_log_handler.setFormatter(log_formatter)
bot_log_handler.setLevel(logging.INFO)

# Настройка root logger для цветного вывода в консоль (Windows Terminal, PowerShell)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)

logger = logging.getLogger("Lapochka_bot")
logger.setLevel(logging.INFO)
logger.addHandler(bot_log_handler)
logger.propagate = True  # Важно: propagate=True, чтобы root logger выводил в консоль

# Логгер для Wavelink
wavelink_log_handler = RotatingFileHandler(
    filename="logs/wavelink.log",
    maxBytes=5 * 1024 * 1024,  # 5MB
    backupCount=5,
    encoding="utf-8",
)
wavelink_log_handler.setFormatter(log_formatter)
wavelink_log_handler.setLevel(logging.INFO)

wavelink_logger = logging.getLogger("wavelink")
wavelink_logger.setLevel(logging.INFO)
wavelink_logger.addHandler(wavelink_log_handler)
wavelink_logger.propagate = False

# Логгер для Discord.py
discord_log_handler = RotatingFileHandler(
    filename="logs/discord.log",
    maxBytes=5 * 1024 * 1024,  # 5MB
    backupCount=5,
    encoding="utf-8",
)
discord_log_handler.setFormatter(log_formatter)
discord_log_handler.setLevel(logging.INFO)

discord_logger = logging.getLogger("discord")
discord_logger.setLevel(logging.INFO)
discord_logger.addHandler(discord_log_handler)
discord_logger.propagate = False


load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
LAVALINK_HOST = os.getenv("LAVALINK_HOST")
LAVALINK_PASSWORD = os.getenv("LAVALINK_PASSWORD")
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
aiohttp_session = None

EXTENSIONS = [
    "commands.music_commands",
    "commands.birthday_commands",
    "commands.admin_commands",
    "commands.setup_commands",
    "events.events_cog",
    "tasks.birthday_task",
    "tasks.scheduled_messages_task",
    "tasks.role_report_task",
]


async def init_aiohttp_session():
    global aiohttp_session
    if aiohttp_session is None or aiohttp_session.closed:
        aiohttp_session = aiohttp.ClientSession()


async def close_aiohttp_session():
    global aiohttp_session
    if aiohttp_session is not None:
        await aiohttp_session.close()
        aiohttp_session = None
