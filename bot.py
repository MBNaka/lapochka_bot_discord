import asyncio
from database import database
from lavalink import run_lavalink
from loader import TOKEN, bot, logger

database.init_db()

async def main():
    logger.info("Loading extensions...")
    await bot.load_extension("commands.music_commands")
    await bot.load_extension("commands.admin_commands")
    await bot.load_extension("commands.birthday_commands")
    await bot.load_extension("commands.setup_commands")
    await bot.load_extension("events.events_cog")
    logger.info("Extensions loaded. Starting bot...")
    await bot.start(TOKEN)
    logger.info("Bot stopped.")

if __name__ == "__main__":
    asyncio.run(main())
