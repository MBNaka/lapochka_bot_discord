import commands.music_commands
import events.on_guild_join
import events.on_member_join
import events.on_ready
import events.on_wavelink_inactive_player
import events.on_wavelink_track_end
import events.on_wavelink_track_start
from database import database
from lavalink import run_lavalink
from loader import TOKEN, bot, logger

# logger.info("Starting lavalink server...")
# run_lavalink()
# logger.info("Lavalink server started.")

database.init_db()

if __name__ == "__main__":
    logger.info("Run")
    bot.run(TOKEN)
    logger.info("Stop")
