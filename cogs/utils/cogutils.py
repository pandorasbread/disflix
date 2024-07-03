from typing import Callable
import discord
from discord import Colour


def get_safe_embeds(items: [], description_builder: Callable, embed_title: str = 'List', embed_color: Colour = Colour.random()) -> []:
    max_chars = 4096
    embeds = [discord.Embed(colour=embed_color, title=embed_title, description='')]
    embedindex = 0

    for item in items:
        desc = description_builder(item)

        if len(embeds[embedindex].description) + len(desc) >= max_chars:
            embedindex += 1
            embeds.append(discord.Embed(colour=embed_color, title=embed_title, description=''))
        embeds[embedindex].description += desc

    if len(embeds) != 1:
        embedindex = 1
        for embed in embeds:
            embed.title += ' (' + str(embedindex) + ' of ' + str(len(embeds)) + ')'
            embedindex += 1
    return embeds