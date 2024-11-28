import discord
from discord.ext.commands import Cog
from discord.ext.commands import Bot
from discord.ext import commands
from pymongo.mongo_client import MongoClient
from dotenv import load_dotenv
import os
import aiohttp
import io


class MiscCommands(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        load_dotenv()
        self.mongo = MongoClient(str(os.environ.get('MONGO_CONNECTION')))
        self.db = self.mongo[str(os.environ.get('DB_NAME'))]

    @commands.command(name='kneecaps', aliases=['kc', 'kneecap', 'knees'])
    async def bust_kneecaps(self, context: commands.Context):
        try:
            #self.high_data_method(context)
            await self.low_data_method(context)


        except Exception as e:
            print(e)
            await context.channel.send('ERROR: ' + str(e))

    async def low_data_method(self, context: commands.Context):
        await context.channel.send('bustin\' makes me feel good')
        await context.channel.send("https://cdn.discordapp.com/attachments/514221002117480451/1232873953610039347/Rian_bustin_kneecaps_Made_with_FlexClip1.gif?ex=674288d8&is=67413758&hm=8a79893799d085879905fefa88d7e68bffb5b9cc34b93b013831e35b6548e790&")

    async def high_data_method(self, context: commands.Context):
        async with aiohttp.ClientSession() as session:
            async with session.get(
                    'https://cdn.discordapp.com/attachments/514221002117480451/1232873953610039347/Rian_bustin_kneecaps_Made_with_FlexClip1.gif?ex=674288d8&is=67413758&hm=8a79893799d085879905fefa88d7e68bffb5b9cc34b93b013831e35b6548e790&') as resp:
                if resp.status != 200:
                    return await context.channel.send('oh shit kneecaps gif went missing')
                data = io.BytesIO(await resp.read())
                await context.channel.send('bustin\' makes me feel good')
                await context.channel.send(file=discord.File(data, 'rian_kneecaps.gif'))
async def setup(bot):
    await bot.add_cog(MiscCommands(bot))
