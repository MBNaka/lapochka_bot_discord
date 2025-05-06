from typing import Any

import wavelink

import embeds.disconnect_embed
from loader import bot, logger


@bot.event
async def on_wavelink_inactive_player(player: wavelink.Player) -> None:
    logger.info(f"Player is inactive: {player.guild.name}")
    try:
        embed = await embeds.disconnect_embed.get_embed()
        await player.channel.send(embed=embed)
    except Exception as e:
        logger.error(f"Failed to send disconnect embed: {e}")
    try:
        await player.disconnect()
    except Exception as e:
        logger.error(f"Failed to disconnect player: {e}")
