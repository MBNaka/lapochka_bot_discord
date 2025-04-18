import events.on_ready
import events.on_wavelink_track_start
import events.on_wavelink_track_end
import events.on_wavelink_inactive_player
import commands.music_commands

from loader import bot, TOKEN, logger

logger.info("Run")
bot.run(TOKEN)
logger.info("Stop")