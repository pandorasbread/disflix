import discord
import asyncio
from discord.ext.commands import Bot
from dotenv import load_dotenv, find_dotenv
import pathlib
import os



intents = discord.Intents.default()
intents.message_content = True
bot = Bot("$", intents=intents, max_messages=None, help_command=None)

@bot.command()
async def help(context):
    embed = discord.Embed(colour=discord.Colour.yellow(), title='halp', description='')
    embed.description += 'MOVIE COMMANDS:\n'
    embed.description += '`$add` `movie_name`: Adds `movie_name` to the movie database\n'
    embed.description += '`$delete` `movie_name`: Deletes `movie_name` from the movie database\n'
    embed.description += '`$nominate` `movie_name` OR `$nom` `movie_name`: Nominates `movie_name` for movie night, also adds it to the database if it is not there.\n'
    embed.description += '`$nommy` OR `$nommysorry` OR `$qn` or `qnom`: Finds and nominates a movie of yours based on text comparison. Easier than typing a full name.\n'
    embed.description += '`$nomdb`: Finds and nominates anyone\'s movie in the database based on text comparison. Easier than typing a full name.\n'
    embed.description += '`$nominations` OR `$noms`: See current nominations.\n'
    embed.description += '`$mymovies`: See all movies you suggested.\n'
    embed.description += '`$randomnom`: Nominate a random movie of yours.\n'
    embed.description += '`$clear`: clears all nominations.\n'
    embed.description += '`$find` `text`: searches for `text` in all movie titles, returns list and if we have watched a movie.\n'
    embed.description += '`$hww`: returns all watched movies in chronological order.\n'
    embed.description += '`$hww` `movie_name`: returns when and if a movie was watched.\n'
    embed.description += '`$withdraw` OR `$w`: Removes all your nominations from the next movie night list. \n'
    embed.description += '`$withdraw` `movie_name` OR `$w` `movie_name`: Removes a specific nomination from the next movie night list. \n'
    embed.description += '`$poll` or `$vote`: creates a poll or links to an existing poll.\n'
    embed.description += '`$endpoll` or `$endvote`: ends a poll.\n'
    embed.description += '`$out` and `$in`: change user status for movie night. Will be used to determine if movies that a user suggested should be hidden.\n'
    embed.description += '`$addhistory` or `$ha` or `ah` or `$addh` or `$hist` `mm/dd/yyyy` `movie name`: add a previous win for a movie.\n'
    embed.description += 'ACRONYM COMMANDS:\n'
    embed.description += '`$ass` `ACRONYM`: get the expansion of an acronym.\n'
    embed.description += '`$ass` `ACRONYM` `\"Acronym Expansion\"`: add an expansion of an acronym.\n'
    embed.description += '`$asses` or `$as` or `$acrs` or `$acronyms` or `eatass`: get the expansions of all acronyms.\n'
    embed.description += '`$bidet` `ACRONYM` or `$bidet` `ACRONYM` `"definition"`: admin only command to delete acronyms or definitions.\n'
    embed.description += '`$buyvote` TAGGED_USER: The person who uses the command "buys" the vote of the tagged user, which is recorded to be used in a future vote.\n'
    embed.description += '`$usevote` TAGGED_USER: The person who uses the command uses the vote of the tagged user in a movie poll if they have a vote.\n'
    embed.description += '`$checkvotes`: Check the list of votes you have from people who have bought your vote in a past movie poll.\n'
    embed.description += '`$deletevotes`: Deletes all the votes in the database that the user has gained from being bought in past movie polls.\n'
    await context.send(embed=embed)


@bot.command(name='halp')
async def halp(context):
    await help(context)

async def start_bot():
    directory = pathlib.Path(__file__).parent.resolve()
    for filename in os.listdir(str(directory)+"/cogs"):
        if filename.endswith(".py"):
            print(filename)
            await bot.load_extension(f'cogs.{filename[:-3]}')
    load_dotenv(find_dotenv())
    token = str(os.environ.get('BUTTFRIEND_TOKEN'))
    await bot.start(token)

asyncio.run(start_bot())

