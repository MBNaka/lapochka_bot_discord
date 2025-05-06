import logging
import os

import discord
import wavelink

from loader import (EXTENSIONS, LAVALINK_HOST, LAVALINK_PASSWORD, bot,
                    init_aiohttp_session, logger)


@bot.event
async def on_ready():
    discord.utils.setup_logging(level=logging.DEBUG)
    for extention in EXTENSIONS:
        try:
            await bot.load_extension(extention)
            logger.info(f"Extension {extention} loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load extension {extention}: {e}")

    await init_aiohttp_session()
    logger.info("Logged in: %s | %s", bot.user, bot.user.id)

    selected_node = {"host": LAVALINK_HOST, "password": LAVALINK_PASSWORD}
    node = wavelink.Node(
        uri=selected_node["host"],
        password=selected_node["password"],
    )

    await wavelink.Pool.connect(nodes=[node], client=bot)
    logger.info("Lavalink node connected!")
    await bot.tree.sync()
    logger.info("Slash commands synced!")
    logger.info(f"Bot is ready. Logged in as {bot.user}")

    # Запуск задач для поздравлений и снятия роли именинника
    birthday_cog = bot.get_cog("BirthdayTask")
    if birthday_cog and not hasattr(birthday_cog, "_tasks_started"):
        birthday_cog._tasks_started = True
        bot.loop.create_task(birthday_cog.birthday_check_loop())
        bot.loop.create_task(birthday_cog.birthday_role_cleanup_loop())
        logger.info("Birthday tasks started.")
