import discord
from discord.ext.commands import Cog
from discord.ext.commands import Bot
from discord.ext import commands
from pymongo.mongo_client import MongoClient
from dotenv import load_dotenv
from cogs.utils import cogutils
import os
import random
import re

class AssCommands(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        load_dotenv()
        self.mongo = MongoClient(str(os.environ.get('MONGO_CONNECTION')))
        self.db = self.mongo[str(os.environ.get('DB_NAME'))]

        @commands.command(name='kneecaps', aliases=['kc', 'kneecap', 'knees'])
        async def bust_kneecaps(self, context: commands.Context):
            try:
                await context.channel.send(embed=discord.Embed(url = 'https://cdn.discordapp.com/attachments/514221002117480451/1232873953610039347/Rian_bustin_kneecaps_Made_with_FlexClip1.gif?ex=674288d8&is=67413758&hm=8a79893799d085879905fefa88d7e68bffb5b9cc34b93b013831e35b6548e790&'))

            except Exception as e:
                print(e)
                await context.channel.send('ERROR: ' + str(e))

