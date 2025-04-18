from loader import bot, logger
import embeds.disconnect_embed
import wavelink

@bot.event
async def on_wavelink_inactive_player(player: wavelink.Player) -> None:
    logger.info(f"Player is inactive: {player.guild.name}")
    embed = await embeds.disconnect_embed.get_embed()
    await player.channel.send(embed=embed)
    await player.disconnect()