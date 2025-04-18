import discord
from discord import File
from utils.track_card import create_track_card

async def get_embed(track, original):
    embed = discord.Embed(title="Сейчас играет:")
    embed.description = f"**{track.title}** by `{track.author}`"
    embed.colour = discord.Colour.purple()

    embed.set_author(name="Lapochka Bot", icon_url="https://media1.tenor.com/m/ZAMoMuQgf9UAAAAd/mapache-pedro.gif")
    
    # Генерация изображения карточки
    if track.artwork:
        image = await create_track_card(track.title, track.author, track.artwork)
    else:
        image = await create_track_card(track.title, track.author, None)
    file = File(image, filename="track_card.png")
    embed.set_image(url="attachment://track_card.png")

    if original and original.recommended:
        embed.description += f"\n\n`This track was recommended via {track.source}`"

    if track.album.name:
        embed.add_field(name="Album", value=track.album.name)

    return embed, file