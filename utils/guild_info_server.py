# utils/guild_info_server.py
# Мини-сервер для получения информации о гильдиях (название, иконка) через discord.py
import os
from aiohttp import web
import discord
from discord.ext import commands
import logging

# Локальный логгер для микросервиса
logger = logging.getLogger("guild_info_server")
if not logger.hasHandlers():
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(name)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
logger.setLevel(logging.INFO)

from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")
PORT = int(os.environ.get("GUILD_INFO_PORT") or 8765)

intents = discord.Intents.none()
intents.guilds = True
bot = commands.Bot(command_prefix="!", intents=intents)

GUILD_CACHE = {}

@bot.event
async def on_ready():
    logger.info("[guild_info_server] on_ready triggered!")
    global GUILD_CACHE
    GUILD_CACHE = {}
    for guild in bot.guilds:
        GUILD_CACHE[str(guild.id)] = {
            "id": str(guild.id),
            "name": guild.name,
            "icon_url": guild.icon.url if guild.icon else None
        }
        logger.info(f"[guild_info_server] Guild: {guild.id} | {guild.name} | icon: {guild.icon.url if guild.icon else 'None'}")
    logger.info(f"[guild_info_server] Cached {len(GUILD_CACHE)} guilds. Starting web server...")
    app = web.Application()
    app.add_routes([
        web.get("/guilds", handle_guilds),
        web.get("/guild/{guild_id}", handle_guild_by_id)
    ])
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", PORT)
    await site.start()
    logger.info(f"[guild_info_server] Web server running on http://127.0.0.1:{PORT}")

async def handle_guilds(request):
    return web.json_response(list(GUILD_CACHE.values()))

async def handle_guild_by_id(request):
    guild_id = request.match_info["guild_id"]
    info = GUILD_CACHE.get(guild_id)
    if info:
        return web.json_response(info)
    return web.Response(status=404, text="Guild not found")

if __name__ == "__main__":
    if not DISCORD_TOKEN:
        raise RuntimeError("DISCORD_TOKEN is not set for guild_info_server")
    logger.info("[guild_info_server] Bot starting...")
    bot.run(DISCORD_TOKEN)
