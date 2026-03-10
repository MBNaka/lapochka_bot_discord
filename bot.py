import asyncio
from database import database
from loader import (
    EXTENSIONS,
    TOKEN,
    bot,
    close_aiohttp_session,
    init_aiohttp_session,
    logger,
)

database.init_db()


async def load_extensions():
    for extension in EXTENSIONS:
        await bot.load_extension(extension)


async def main():
    if not TOKEN:
        logger.error("DISCORD_TOKEN is not set. Bot cannot be started.")
        return

    logger.info("Initializing aiohttp session...")
    await init_aiohttp_session()
    try:
        logger.info("Loading extensions...")
        await load_extensions()
        logger.info("Extensions loaded. Starting bot...")
        await bot.start(TOKEN)
        logger.info("Bot stopped.")
    finally:
        await close_aiohttp_session()

if __name__ == "__main__":
    asyncio.run(main())
