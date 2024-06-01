
import discord
from discord.abc import Messageable
from discord.ext.commands import Cog
from discord import Message
from discord.ext.commands import Bot
from discord.ext import commands
from pymongo.mongo_client import MongoClient
from dotenv import load_dotenv, find_dotenv
import os
import random
import re

class AssCommands(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        load_dotenv()
        self.mongo = MongoClient(str(os.environ.get('MONGO_CONNECTION')))
        self.db = self.mongo[str(os.environ.get('DB_NAME'))]


    @commands.command(name='ass', aliases=['acr', 'a', 'acronym'])
    async def acronym(self, context: commands.Context, acronym:str = None, definition:str = None):
        try:
            if acronym == None and definition == None:
                await context.channel.send(
                    "What the fuck did you just fucking say about me, you little bitch? I'll have you know I graduated top of my class in the Navy Seals, and I've been involved in numerous secret raids on Al-Quaeda, and I have over 300 confirmed kills. I am trained in gorilla warfare and I'm the top sniper in the entire US armed forces. You are nothing to me but just another target. I will wipe you the fuck out with precision the likes of which has never been seen before on this Earth, mark my fucking words. You think you can get away with saying that shit to me over the Internet? Think again, fucker. As we speak I am contacting my secret network of spies across the USA and your IP is being traced right now so you better ")
                await context.channel.send(
                    "prepare for the storm, maggot. The storm that wipes out the pathetic little thing you call your life. You're fucking dead, kid. I can be anywhere, anytime, and I can kill you in over seven hundred ways, and that's just with my bare hands. Not only am I extensively trained in unarmed combat, but I have access to the entire arsenal of the United States Marine Corps and I will use it to its full extent to wipe your miserable ass off the face of the continent, you little shit. If only you could have known what unholy retribution your little \"clever\" comment was about to bring down upon you, maybe you would have held your fucking tongue. But you couldn't, you didn't, and now you're paying the price, you goddamn idiot. I will shit fury all over you and you will drown in it. You're fucking dead, kiddo. ")
                return

            acronym = str.upper(acronym)
            if (definition == None):
                return await self.get_acronym(context, acronym)

            definition = str.title(definition)

            if len(str.split(definition, sep=' ')) == 1:
                await context.channel.send('Hey consider that you do not understand how acronyms work, as they should probably have more than one word in the un-acronymed phrase. So if you want to use this command, write something like `$ass TWP \"Three Word Phrase\". Yes you need the quotes. No this is not negotiable')
                return


            if (acronym == 'ASS'):
                await context.channel.send('You are unable to change perfection.')
                return

            if self.db['acronyms'].count_documents({'acronym': acronym, 'expanded': definition}) == 1:
                await context.channel.send(definition + ' is already listed as a potential expansion of ' + acronym+'.')
                return

            if self.db['acronyms'].count_documents({'acronym': acronym}) == 0:
                self.db['acronyms'].insert_one({'acronym':acronym, 'expanded': [definition]})
            elif self.db['acronyms'].count_documents({'acronym': acronym, 'expanded': definition}) == 0:
                self.db['acronyms'].update_one({'acronym': acronym}, {'$push': {'expanded': definition}})

            await context.message.add_reaction(random.choice(self.bot.emojis))
        except Exception as e:
            print(e)
            await context.channel.send('ERROR: '+str(e))

    async def get_acronym(self, context: commands.Context, acronym):

        embed = discord.Embed(colour=discord.Colour.random(), title='WhAt DoEs \"' + acronym + '\" sTaNd FoR?',
                             description='')
        acr = self.db['acronyms'].find_one({'acronym': self.clean_case(acronym)})
        if acr is None:
            embed.description += acronym + ' not unjarbled yet. Try `$ass ' + acronym + ' \"Some Definition\"` to dejangle it.'
        else:
            for definition in acr.get('expanded'):
                embed.description += definition+'\n'
        return await context.channel.send(embed=embed)

    def clean_case(self, text: str):
        return re.compile("^"+re.escape(text)+"$", re.IGNORECASE)


async def setup(bot):
    await bot.add_cog(AssCommands(bot))
