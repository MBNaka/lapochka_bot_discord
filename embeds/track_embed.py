from typing import Any, Tuple

import discord
from discord import File

from utils.track_card import create_track_card


async def get_embed(track: Any, original: Any) -> Tuple[discord.Embed, File]:
    embed = discord.Embed(title="Сейчас играет:")
    embed.description = f"**{track.title}** by `{track.author}`"
    embed.colour = discord.Colour.purple()
    embed.set_author(
        name="Lapochka Bot",
        icon_url="https://media1.tenor.com/m/ZAMoMuQgf9UAAAAd/mapache-pedro.gif",
    )
    # Генерация изображения карточки
    try:
        if track.artwork:
            image = await create_track_card(track.title, track.author, track.artwork)
        else:
            image = await create_track_card(track.title, track.author, None)
        file = File(image, filename="track_card.png")
        embed.set_image(url="attachment://track_card.png")
    except Exception as e:
        file = None
        embed.description += f"\n(Ошибка генерации карточки: {e})"
    if original and getattr(original, "recommended", False):
        embed.description += f"\n\n`This track was recommended via {track.source}`"
    if getattr(track, "album", None) and getattr(track.album, "name", None):
        embed.add_field(name="Album", value=track.album.name)
    return embed, file
