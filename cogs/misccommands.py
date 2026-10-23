import discord
from discord.ext.commands import Cog
from discord.ext.commands import Bot
from discord.ext import commands
from pymongo.mongo_client import MongoClient
from dotenv import load_dotenv
from datetime import timedelta
import os
import aiohttp
import io


class MiscCommands(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        load_dotenv()
        self.mongo = MongoClient(str(os.environ.get('MONGO_CONNECTION')))
        self.db = self.mongo[str(os.environ.get('DB_NAME'))]

    @commands.command(name='untimeout', aliases=['uto', 'uko', 'save'])
    async def untimeout(self, context: commands.Context, user: discord.Member, *, reason: str = ''):
        try:
            ismod = False
            for role in context.message.author.roles:
                if role.name == 'Mini Moderator':
                    ismod = True
            if not (context.message.author.guild_permissions.administrator or ismod):
                return await context.channel.send('Oh, you believe in freeing your fellow revolutionaries? cringe')

            self.db.timeouts.find_one_and_update(
                {"user": user.id},
                {"$set": {"spared": True, "sparedReason":reason}},
                sort=[("timestamp", -1)],
            )

            await context.message.add_reaction('😇')
            await context.send(user.mention + ' has proven to be a little angel')
            return await user.timeout(None, reason=reason)

        except Exception as e:
            print(e)
            await context.channel.send('ERROR: ' + str(e))

    @commands.command(name='timeout', aliases=['to', 'ko', 'tyrant'])
    async def timeout(self, context: commands.Context, user: discord.Member, minutes: float = 1, *, reason: str = 'bad behavior, probably'):
        try:
            ismod = False
            for role in context.message.author.roles:
                if role.name == 'Mini Moderator':
                    ismod = True
            if not (context.message.author.guild_permissions.administrator or ismod):
                return await context.channel.send('The wolf does not have the keys to the gun safe. But if he did, he would take on the authorities.')
            self.db.timeouts.insert_one({"minutes":minutes, "reason":reason, "user":user.id, "timestamp":context.message.created_at})
            await context.message.add_reaction('🧑‍⚖️')
            await context.send(user.mention + ' has been JUDGED with `' + reason + '`!!!')
            return await user.timeout(timedelta(seconds=minutes*60), reason=reason)

        except Exception as e:
            print(e)
            await context.channel.send('ERROR: ' + str(e))

    @commands.command(name='kneecaps', aliases=['kc', 'kneecap', 'knees'])
    async def bust_kneecaps(self, context: commands.Context):
        try:
            #self.high_data_method(context)
            await self.kc_low_data_method(context)

        except Exception as e:
            print(e)
            await context.channel.send('ERROR: ' + str(e))

    @commands.command(name='mykneecaps', aliases=['mykc', 'myknees', 'peter'])
    async def my_kneecaps(self, context: commands.Context):
        try:
            await self.mykc_low_data_method(context)

        except Exception as e:
            print(e)
            await context.channel.send('ERROR: ' + str(e))

    async def mykc_low_data_method(self, context: commands.Context):
        await context.channel.send('i\'ve been busted :(')
        await context.channel.send("https://media.discordapp.net/attachments/1230913367447961600/1492348684057444492/image0.gif?ex=69db0184&is=69d9b004&hm=b981c479939bf4c59af88957e557cadbd40ace61cd6bea9288cee225e321a85a&=")

    async def kc_low_data_method(self, context: commands.Context):
        await context.channel.send('bustin\' makes me feel good')
        await context.channel.send("https://cdn.discordapp.com/attachments/514221002117480451/1232873953610039347/Rian_bustin_kneecaps_Made_with_FlexClip1.gif?ex=674288d8&is=67413758&hm=8a79893799d085879905fefa88d7e68bffb5b9cc34b93b013831e35b6548e790&")

    async def kc_high_data_method(self, context: commands.Context):
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
