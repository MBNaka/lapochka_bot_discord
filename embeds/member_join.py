import discord

async def get_embed(data: dict, user_id: int, channel_id: int) -> discord.Embed:
    embed: discord.Embed = discord.Embed()
    embed.description = data.get("TEXT").format(username=user_id, channel=channel_id)
    embed.set_thumbnail(url=data.get("THUMBNAIL_URL") or None)
    embed.set_image(url=data.get("IMAGE_URL") or None)
    embed.colour = discord.Colour.purple()
    return embed
