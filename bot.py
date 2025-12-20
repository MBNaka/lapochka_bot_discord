import asyncio
from database import database
from loader import TOKEN, bot, logger, init_aiohttp_session

database.init_db()

async def main():
    logger.info("Initializing aiohttp session...")
    await init_aiohttp_session()
    logger.info("Loading extensions...")
    await bot.load_extension("commands.music_commands")
    await bot.load_extension("commands.admin_commands")
    await bot.load_extension("commands.birthday_commands")
    await bot.load_extension("commands.setup_commands")
    await bot.load_extension("events.events_cog")
    await bot.load_extension("tasks.scheduled_messages_task")
    await bot.load_extension("tasks.role_report_task")
    await bot.load_extension("tasks.birthday_task")
    logger.info("Extensions loaded. Starting bot...")
    await bot.start(TOKEN)
    logger.info("Bot stopped.")

if __name__ == "__main__":
    asyncio.run(main())
