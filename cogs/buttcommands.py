import datetime

import discord
from discord.abc import Messageable
from discord.ext.commands import Cog
from discord import Message
from discord.ext.commands import Bot
from pymongo.mongo_client import MongoClient
from dotenv import load_dotenv, find_dotenv
import os
import base64
import re

#TODO: Poll options can't be longer than 55 characters
#TODO: In/Out and nominations
#TODO: If a poll is active and a nomination is added, if there are no votes, then add the option. Same with withdrawing.
#TODO: add rolling
#TODO: add closing or deleting specific polls
#TODO: Always close active poll when new poll is called
#TODO: hook into the actual Help methods
#TODO: do something for making a poll with no active nominations
#TODO: $mymovies
#REMEMBER: do not forget https://discordpy.readthedocs.io/en/latest/api.html#discord.Poll
class ButtCommands(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        load_dotenv()
        #self.mongo = MongoClient(os.getenv('MONGO_CONNECTION'))
        #name = os.getenv('DB_NAME')
        self.mongo = MongoClient(str(os.environ.get('MONGO_CONNECTION')))

        self.db = self.mongo[str(os.environ.get('DB_NAME'))]

    #OMDB API http://www.omdbapi.com/

    @Cog.listener()
    async def on_ready(self):
        print('Logged in as {0.user}'.format(self.bot))

    @Cog.listener()
    async def on_message(self, msg: Message):
        try:
            command = msg.content.split(' ', 1)[0]
            content = None
            if (len(msg.content.split(' ', 1)) > 1):
                content = msg.content.split(' ', 1)[1]

            if command == '$testing':
                await msg.channel.send('uwu')
            if command == '$add':
                self.check_user(msg.author)
                await self.add_movie(content, msg)
            if command == '$delete':
                await self.delete_movie(content, msg)
            if command == '$nominate' or command == '$nom': #maybe add custom emoji to movie?
                self.check_user(msg.author)
                await self.nominate_movie(content, msg)
            if command == '$nominations' or command == '$noms':
                await self.get_nominations(msg.channel)
            if command == '$withdraw' or command == '$w':
                self.check_user(msg.author)
                if not content:
                    self.db["movies"].update_many({"nominated": True, "nominator": self.db["users"].find_one({"username": msg.author.id}).get('_id')}, {"$set": {"nominated": False,"nominator": None}})
                else:
                    self.db["movies"].update_one({"title":self.clean_case(content), "nominated": True, "nominator": self.db["users"].find_one(
                        {"username": msg.author.id}).get('_id')}, {"$set": {"nominated": False, "nominator": None}})
                    #add messaging when you withdraw a movie that isn't yours
                await msg.add_reaction('🧻')

            #if command == '$roll':
            #if command == '$rollall':
            if command == '$poll' or command == '$vote':
                await self.run_poll(msg)

            if command == '$endvote' or command == '$endpoll':
                await self.end_poll(content == 'roll', msg)

            #if command == '$nominateminerandom':
            #if command == '$nominaterandom':
            if command == '$clear':
                self.db["movies"].update_many({"nominated": True}, {'$set': {"nominated": False, 'nominator': None}})
                await msg.add_reaction('🧻')
            #if command == '$swap':
            if command == '$moviehelp':
                embed = discord.Embed(colour=discord.Colour.yellow(), title='halp', description='')
                embed.description += '`$add` `movie_name`: Adds `movie_name` to the movie database\n'
                embed.description += '`$delete` `movie_name`: Deletes `movie_name` from the movie database\n'
                embed.description += '`$nominate` `movie_name` OR `$nom` `movie_name`: Nominates `movie_name` for movie night, also adds it to the database if it is not there.\n'
                embed.description += '`$nominations` OR `$noms`: See current nominations.\n'
                embed.description += '`$clear`: clears all nominations.\n'
                embed.description += '`$withdraw` OR `$w`: Removes all your nominations from the next movie night list. \n'
                embed.description += '`$withdraw` `movie_name` OR `$w` `movie_name`: Removes a specific nomination from the next movie night list. \n'
                embed.description += '`$poll or $vote`: creates a poll.\n'
                embed.description += '`$endpoll or $endvote`: ends a poll.\n'
                embed.description += '`$out` and `$in`: change user status for movie night. Will be used to determine if movies that a user suggested should be hidden.\n'
                await msg.channel.send(embed=embed)

            #if command == '$audit':
            #if command == '$bestpicks':
            #if command == '$historicaladd': #like $historicaladd 04/20/2020 rise of skywalker

            if command == '$out':
                self.check_user(msg.author)
                self.db["users"].update_one({"username":msg.author.id}, {"$set": {"out":True}})
                await msg.add_reaction('🏃')
            if command == '$in':
                self.check_user(msg.author)
                self.db["users"].update_one({"username":msg.author.id}, {"$set": {"out":False}})
                await msg.add_reaction('👁')
        except Exception as e:
            print(e)
            await msg.channel.send('ERROR: '+str(e))

    async def run_poll(self, msg: Message, tiebreaker: bool = False):
        movies = self.db["movies"].find({"nominated": True})
        titles = [movie['title'] for movie in movies]
        duration = datetime.timedelta(hours=24)
        if len(titles) == 0:
            embed = discord.Embed(colour=discord.Colour.yellow(), title='', description='')
            embed.description = 'No active nominations!'
            return await msg.channel.send(embed=embed)
        numvotes = '0'
        if len(titles) <= 4:
            numvotes = '1'
        elif len(titles) > 4 and len(titles) <= 7:
            numvotes = '2'
        else:
            numvotes = '3'

        poll_code = base64.urlsafe_b64encode(os.urandom(6)).decode('ascii')
        result = discord.Poll(question= 'TIEBREAKER! [Poll Code: `'+ poll_code + '`]' if tiebreaker else 'Which movie? ' + numvotes + ' vote(s) [Poll Code: `' + poll_code + '`]', multiple=len(titles) > 4 and not tiebreaker,
                              duration=duration)
        for title in titles:
            result.add_answer(text=title)
        sent_poll = await msg.channel.send(poll=result)

        self.db['polls'].insert_one({'server_id': msg.guild.id, 'message_id': sent_poll.id, 'poll_time': datetime.datetime.now(tz=datetime.timezone.utc), 'poll_code':poll_code, 'open':True})

    async def end_poll(self, roll: bool, msg: Message):
        pollid = self.db['polls'].find_one({'server_id': msg.guild.id, 'poll_time': {"$lt": datetime.datetime.now(tz=datetime.timezone.utc)}, 'open': True}).get('message_id')
        channel = await self.bot.fetch_channel(msg.channel.id)
        pollmessage = await channel.fetch_message(pollid)
        sortedlist = sorted(pollmessage.poll.answers, key=lambda a: a.vote_count, reverse=True)
        winners = [answer for answer in sortedlist if answer.vote_count == sortedlist[0].vote_count]
        if len(winners) == 1:
            await msg.channel.send(winners[0].text + ' is the winner!')
            self.db['movies'].update_one({'title': self.clean_case(winners[0].text)}, {'$set': {'last_win_date': datetime.datetime.today()}})
            self.db['movies'].update_many({'nominated': True}, {'$set': {'nominated': False, 'nominator': None}})
            self.db['polls'].update_one({'message_id': pollid}, {'$set': {'open':False}})
            await pollmessage.poll.end()
        else:
            for answer in sortedlist:
                if answer.vote_count != sortedlist[0].vote_count:
                    self.db['movies'].update_one({'title': answer.text, 'nominated': True}, {'$set': {'nominated': False, 'nominator': None}})
            self.db['polls'].update_one({'message_id': pollid}, {'$set': {'open': False}})
            await pollmessage.poll.end()
            await self.run_poll(msg, True)

    async def get_nominations(self, channel: Messageable):
        movies = self.db["movies"].find({"nominated": True})
        titles = [[movie['title'], movie.get('last_win_date')] for movie in movies]
        msg = discord.Embed(colour=discord.Colour.yellow(), title='Current Nominations', description='')
        if len(titles) == 0:
            msg.description = 'No active nominations!'
        for title in titles:
            msg.description += title[0]
            if title[1] is not None:
                msg.description += ' - won on ' + str(title[1].date())
            msg.description += '\n'
            #msg.add_field(value= title)
        await channel.send(embed=msg)

    async def nominate_movie(self, title: str, msg: Message):
        isNew = await self.add_plain(title, msg)
        isNominated = self.db["movies"].count_documents({'title': self.clean_case(title), 'nominated': True}) != 0
        if not isNew and isNominated:
            nominatorid = self.db["movies"].find_one({'title': self.clean_case(title)}).get('nominator')
            nominator = self.db["users"].find_one({'_id': nominatorid}).get('username')
            user = await self.bot.fetch_user(nominator)
            await msg.channel.send(title + ' already nominated by ' + user.display_name)
        else:
            self.check_user(msg.author)
            self.db["movies"].update_one({"title": self.clean_case(title)}, {"$set": {"nominated": True, "nominator": self.db["users"].find_one({"username": msg.author.id}).get('_id')}})
            last_win = self.db['movies'].find_one({'title': self.clean_case(title)}).get('last_win_date')
            if last_win is not None:
                await msg.channel.send(title + ' won on ' + str(last_win.date()))
            await msg.add_reaction('🗳️')


    def check_user(self, user: Message.author):
        if self.db["users"].count_documents({"username": user.id}) == 0:
            self.db["users"].insert_one({"username": user.id, "out": 0})

    async def add_movie(self, title: str, msg: Message):
        isNew = await self.add_plain(title, msg)
        if not isNew:
            originatorid = self.db["movies"].find_one({'title': self.clean_case(title)}).get('originator')
            originator = self.db["users"].find_one({'_id': originatorid}).get('username')
            user = await self.bot.fetch_user(originator)
            await msg.channel.send(title + ' already added by ' + user.display_name)

    async def add_plain(self, title: str, msg: Message) -> bool:
        isNew = self.db["movies"].count_documents({'title': self.clean_case(title)}) == 0
        if isNew:
            self.db["movies"].insert_one({"title": title, "originator":self.db["users"].find_one({'username': msg.author.id}).get('_id')})
            await msg.add_reaction('👍')
        return isNew

    def add_omdb(self, title: str, msg: Message):
        return

    async def delete_movie(self, title: str, msg: Message):
        if self.db["movies"].count_documents({"title": self.clean_case(title), "originator":self.db["users"].find_one({'username': msg.author.id}).get('_id')}) != 0:
            self.db["movies"].delete_one({"title": self.clean_case(title), "originator":self.db["users"].find_one({'username': msg.author.id}).get('_id')})
            await msg.add_reaction('🗑')
        else:
            await msg.channel.send('Movies can only be removed by the user who added them or the movie has already been deleted.')

    def clean_case(self, text: str):
        return re.compile("^"+re.escape(text)+"$", re.IGNORECASE)



async def setup(bot):
    await bot.add_cog(ButtCommands(bot))
