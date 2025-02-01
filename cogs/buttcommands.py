import datetime

import discord
import pymongo
from discord.abc import Messageable
from discord.ext.commands import Cog
from discord import Message
from discord.ext.commands import Bot
from pymongo.mongo_client import MongoClient
from dotenv import load_dotenv, find_dotenv
from cogs.utils import cogutils
import os
import base64
import re
import random
import dateutil.parser as dparser


# scope creep
# TODO: If a poll is active and a nomination is added, if there are no votes, then add the option. Same with withdrawing.
# TODO: add closing polls from any channel
    # need to track channel that a poll was posted in.
# TODO: add auto-ending of polls
    # we know the poll update. The bot can start an async timer when a poll starts and kill it after that many days by checking .
# TODO: Movie emojis
    # add emoji code column to the movie object. If there's none, then use whatever the default is.
    # need a command to add an emoji to an existing movie
    # need a command to add a movie with an emoji
# TODO: AUDITING!
    # Create a table for user audits.
    # Save every unique instance of an issue per user. Delete after one year. Check for old records on table update.
    # Save every instance of voter fraud
    # TODO: Poll auditing!
        # when a poll closes, run a check:
        # see if a user voted on a poll more times than allowed -> voter fraud
        # notify buttdvf
        # see if a user voted but for fewer options than allowed -> sus behavior
        # TODO: DVF vote timeouts
            # ability to time a user out
            # exclude a user's votes if they are on time out.
        # TODO: USER AUDITING!
            # audit a user's behavior.
            # get a list of all infractions
    # TODO: USER BULLYING!
        # when a user makes a mistake, log it. Next time they make the same mistake, remind them of what they did.
# TODO: download OMDB movie and series datasets and upload into server.
    # update this dataset every week on sunday.
    # TODO: name verification
        # when a user runs $add or $nom, verify that the name is legal.
        # TODO: when a name matches multiple (such as a remake or a shared movie name), provide an embed so that a user can select the intended option via reacts. Delete the poll when a user selects a choice.
        # TODO: When a user adds a new movie, search our db for exact match, then search real db for exact match, then search our db for near match, then search big db for near match.
#TODO: additional warnings
    # when a user is marked as out but noms a movie
    # if someone tries to add an acronym but actually adds a movie, i think i can regex for this
# TODO: buttfriend world dominance
#need to track servers for this to work.ordpy.readthedocs.io/en/latest/api.html#discord.Poll

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
            if command == '$nommy' or command ==  '$nommysorry' or command == '$qn' or command == '$qnom':
                await self.nominate_db(content, msg, True)
            if command == '$nomdb':
                await self.nominate_db(content, msg, False)
            if command == '$omnomnom':
                await self.omnomnom(content, msg)
            if command == '$nominations' or command == '$noms':
                await self.get_nominations(msg.channel)
            if command == '$withdraw' or command == '$w':
                await self.withdraw_movie(content, msg)
            if command == '$poll' or command == '$vote':
                await self.run_poll(msg)
            if command == '$endvote' or command == '$endpoll':
                await self.end_poll(content == 'roll', msg)
            if command == '$randomnom':
                mymovies = self.get_my_movies(msg.author, True)
                titles = [movie.get('title') for movie in mymovies]
                if len(titles) == 0:
                    await msg.channel.send('You have no movies left to nominate randomly.')
                    return
                randmovie = random.choice(titles)
                await msg.channel.send('Nominating \'' + randmovie + '\'.')
                await self.nominate_movie(randmovie, msg)
            if command == '$clear':
                self.db["movies"].update_many({"nominated": True}, {'$set': {"nominated": False, 'nominator': None}})
                await msg.add_reaction('🧻')
            if command == '$mymovies':
                mymovies = self.get_my_movies(msg.author)
                embed = discord.Embed(colour=discord.Colour.dark_red(), title='My Movies', description='')
                for movie in mymovies:
                    lwd = movie.get('last_win_date')
                    embed.description += movie.get('title')
                    if lwd is not None:
                        embed.description += ' - ' + str(lwd.date())
                    embed.description += '\n'
                await msg.channel.send(embed=embed)
            if command == '$havewewatched' or command == '$watched' or command == '$hww':
                return await self.have_we_watched(content, msg)
            if command == '$find' or command == '$search' or command == '$f' or command == '$s':
                return await self.find_movies(content, msg)

            if command == '$hist' or command == '$ha' or command == '$ah' or command == '$addhistory' or command == '$addh': #like $ha 04/20/2020 rise of skywalker
                await self.historical_add(content, msg)
            if command == '$out':
                self.check_user(msg.author)
                self.db["users"].update_one({"username":msg.author.id}, {"$set": {"out":True}})
                await msg.add_reaction('🏃')
            if command == '$in':
                self.check_user(msg.author)
                self.db["users"].update_one({"username":msg.author.id}, {"$set": {"out":False}})
                await msg.add_reaction('👁')
            # if command == '$swap':
            #if command == '$roll':
            #if command == '$rollall':
            # if command == '$audit':
            # if command == '$bestpicks':
        except Exception as e:
            print(e)
            await msg.channel.send('ERROR: '+str(e))

    async def withdraw_movie(self, content: str, msg: Message):
        self.check_user(msg.author)
        if not content:
            self.db["movies"].update_many(
                {"nominated": True, "nominator": self.db["users"].find_one({"username": msg.author.id}).get('_id')},
                {"$set": {"nominated": False, "nominator": None}})
        else:
            nommedmovie = self.db["movies"].find_one({"title": self.clean_case(content), "nominated": True})
            if nommedmovie is None:
                return await msg.channel.send('Are you sure that ' + content + ' is nominated?')
            nominator = self.db["users"].find_one({'_id': nommedmovie.get('nominator')})
            if nominator.get('username') != msg.author.id:
                nominatoruser = await self.bot.fetch_user(nominator.get('username'))
                return await msg.channel.send(content + ' must be removed by the nominator, ' + nominatoruser.display_name + '.')
            self.db["movies"].update_one(
                {"title": self.clean_case(content), "nominated": True}, {"$set": {"nominated": False, "nominator": None}})
        await msg.add_reaction('🧻')

    async def have_we_watched(self, searchtext: str, msg: Message):
        watched = []

        if (searchtext is None):
            watched = self.db["movies"].find({'last_win_date': {'$exists': True }})
        else:
            movie = self.db["movies"].find_one({'title': self.clean_case(searchtext), 'last_win_date':{'$exists': True}})
            if movie is not None:
                watched = self.db["movies"].find({'title': self.clean_case(searchtext), 'last_win_date':{'$exists': True}})
            else:
                return await msg.channel.send('`' + searchtext + '` has not been watched.')
        watched = watched.sort('last_win_date', pymongo.ASCENDING)

        def description_builder(watch):
            lwd = watch.get('last_win_date')
            return watch.get('title') + ' - ' + str(lwd.date()) + '\n'

        for embed in cogutils.get_safe_embeds(watched, description_builder, 'Watched Movies', discord.Colour.dark_gold()):
            await msg.channel.send(embed=embed)



    async def find_movies(self, searchtext: str, msg: Message):
        if searchtext is None:
            return await msg.channel.send('You forgot to enter something to search for, I think.')

        films = self.db["movies"].find({'title': self.clean_search(searchtext)}).sort('title', pymongo.ASCENDING)
        def description_builder(movie):
            lwd = movie.get('last_win_date')
            desc = movie.get('title')
            if lwd is not None:
                desc += ' - ' + str(lwd.date())
            desc += '\n'
            return desc

        for embed in cogutils.get_safe_embeds(films, description_builder, 'Found Movies:', discord.Colour.dark_gold()):
            await msg.channel.send(embed=embed)



    async def historical_add(self, dateAndMovie: str, msg: Message):
        histdate = dparser.parse(dateAndMovie.split(' ', 1)[0], fuzzy=True)
        if (len(dateAndMovie.split(' ', 1)) > 1):
            title = dateAndMovie.split(' ', 1)[1]
        else:
            return await msg.channel.send('You forgot to enter a movie, I think.')

        self.check_user(msg.author)
        isNew = await self.add_plain(title, msg, True)
        lastwindate = self.db["movies"].find_one({'title': self.clean_case(title)}).get('last_win_date')
        if lastwindate is not None and lastwindate > histdate:
            return await msg.channel.send(title + ' last won on ' + str(lastwindate.date()) + ', which is more recent than ' + str(histdate.date()) + '.')

        self.db["movies"].update_one({'title': self.clean_case(title)}, {'$set': {'last_win_date': histdate}})
        return await msg.add_reaction('📅')



    def get_my_movies(self, user: Message.author, only_free: bool = False):
        self.check_user(user)
        user_id = self.db["users"].find_one({"username": user.id}).get('_id')
        if only_free:
            return self.db["movies"].find({'originator': user_id, 'nominated': False, "last_win_date": {'$exists': False}})
        return self.db["movies"].find({'originator': user_id})

    async def run_poll(self, msg: Message, tiebreaker: bool = False):
        activepoll = self.db['polls'].find_one({'open': True})
        if activepoll is not None:
            try:
                pollmsg = ''
                if msg.channel.id != activepoll.get('channel_id'):
                    pollmsg += 'Poll is in a different channel. '
                    channel = msg.guild.get_channel_or_thread(activepoll.get('channel_id'))
                else:
                    channel = msg.channel
                activepollmessage = await channel.fetch_message(activepoll.get('message_id'))
                return await msg.channel.send(pollmsg + 'Current poll here: ' + activepollmessage.jump_url)

            except:
                await msg.channel.send('I could not find the poll at all so I will re-run the poll. Find a scapegoat to blame for deleting it or running it in a channel I cannot see.')
                self.db['polls'].update_one({'message_id': activepoll.get('message_id')}, {'$set': {'open': False}})


        movies = self.db["movies"].find({"nominated": True})
        movies = self.movies_with_in_nominators(movies)
        titles = [movie['title'] for movie in self.movies_with_in_nominators(movies)]
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

        self.db['polls'].insert_one({'server_id': msg.guild.id, 'message_id': sent_poll.id, 'channel_id':sent_poll.channel.id, 'poll_time': datetime.datetime.now(tz=datetime.timezone.utc), 'poll_code':poll_code, 'open':True})

    async def end_poll(self, roll: bool, msg: Message):
        poll = self.db['polls'].find_one({'server_id': msg.guild.id, 'poll_time': {"$lt": datetime.datetime.now(tz=datetime.timezone.utc)}, 'open': True})
        channel = await self.bot.fetch_channel(poll.get('channel_id'))
        pollmessage = await channel.fetch_message(poll.get('message_id'))
        sortedlist = sorted(pollmessage.poll.answers, key=lambda a: a.vote_count, reverse=True)
        winners = [answer for answer in sortedlist if answer.vote_count == sortedlist[0].vote_count]
        if len(winners) == 1:
            await msg.channel.send(winners[0].text + ' is the winner!')
            self.db['movies'].update_one({'title': self.clean_case(winners[0].text)}, {'$set': {'last_win_date': datetime.datetime.today()}})
            nominators_out = [user['_id'] for user in self.db["users"].find({"out": False})]
            self.db['movies'].update_many({'nominated': True, 'nominator': {'$in': nominators_out}}, {'$set': {'nominated': False, 'nominator': None}})
            self.db['polls'].update_one({'message_id': poll.get('message_id')}, {'$set': {'open':False}})
            await pollmessage.poll.end()
        else:
            for answer in sortedlist:
                if answer.vote_count != sortedlist[0].vote_count:
                    self.db['movies'].update_one({'title': answer.text, 'nominated': True}, {'$set': {'nominated': False, 'nominator': None}})
            self.db['polls'].update_one({'message_id': poll.get('message_id')}, {'$set': {'open': False}})
            await pollmessage.poll.end()
            await self.run_poll(msg, True)

    async def get_nominations(self, channel: Messageable):
        nominated_movies = self.db["movies"].find({"nominated": True})
        movies = self.movies_with_in_nominators(nominated_movies)
        titles = [[movie['title'], movie.get('last_win_date')] for movie in movies]
        msg = discord.Embed(colour=discord.Colour.yellow(), title='Current Nominations', description='')
        if len(titles) == 0:
            msg.description = 'No active nominations!'
        for title in titles:
            msg.description += title[0]
            if title[1] is not None:
                msg.description += ' - ' + str(title[1].date())
            msg.description += '\n'
            #msg.add_field(value= title)
        await channel.send(embed=msg)

    def movies_with_in_nominators(self, nominated_movies):
        nominators_out = [user['_id'] for user in self.db["users"].find({"out": True})]
        movies = []
        for movie in nominated_movies:
            if movie.get("nominator") not in nominators_out:
                movies.append(movie)
        return movies

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


    async def nominate_db(self, title: str, msg: Message, user_nominated: bool = False):
        self.check_user(msg.author)
        if title is None:
            return await msg.channel.send('You forgot to enter something to nominate, I think.')

        if user_nominated:
            user_id = self.db["users"].find_one({"username": msg.author.id}).get('_id')
            films = self.db["movies"].find({'title': self.clean_search(title), 'nominated': False, 'originator': user_id}).sort('title', pymongo.ASCENDING)
        else:
            films = self.db["movies"].find({'title': self.clean_search(title), 'nominated': False}).sort('title', pymongo.ASCENDING)
        film = None

        for f in films:
            if 'last_win_date' not in f:
                film = f
                break

        if film is None:
            return await msg.channel.send(
                'You have not entered a movie with a title like `' + title + '` or it is already nominated this week. Quick nom is meant as a way to reference your own nominations easily.')

        await self.nominate_movie(film['title'], msg)
        return await msg.channel.send('Nominated `' + film['title'] + '`.')

    async def omnomnom(self, title: str, msg: Message):
        self.check_user(msg.author)
        if title is None:
            return await msg.channel.send('You forgot to enter something to steal, I think.')

        user_id = self.db["users"].find_one({"username": msg.author.id}).get('_id')
        films = self.db["movies"].find({'title': self.clean_search(title), '$or':[{'nominated': False}, {'nominated': {'$exists':False}}]}).sort('title',
                                                                                                     pymongo.ASCENDING)
        film = None
        for f in films:
            if 'last_win_date' not in f:
                film = f
                break

        if film is None:
            return await msg.channel.send(
                'No one entered a movie with a title like `' + title + '`, or it is already nominated, or it has already won.')

        if film['originator'] == user_id:
            return await msg.channel.send('`'+film['title']+'` is your own movie, stealing it is legal and thus I will not assist you.')


        old_user = await self.bot.fetch_user(self.db["users"].find_one({"_id": film['originator']}).get('username'))
        await msg.channel.send('⛵😏'+ msg.author.name + '🏴‍☠️' + film['title'] + '🏴‍☠️  🌊🏝️🥺' + old_user.display_name)

        self.db["movies"].update_one({'title': self.clean_case(film['title'])}, {'$set': {'originator': user_id}})
        return await self.nominate_movie(film['title'], msg)



    def check_user(self, user: Message.author):
        if self.db["users"].count_documents({"username": user.id}) == 0:
            self.db["users"].insert_one({"username": user.id, "out": False})

    async def add_movie(self, title: str, msg: Message):
        isNew = await self.add_plain(title, msg)
        if not isNew:
            originatorid = self.db["movies"].find_one({'title': self.clean_case(title)}).get('originator')
            originator = self.db["users"].find_one({'_id': originatorid}).get('username')
            user = await self.bot.fetch_user(originator)
            await msg.channel.send(title + ' already added by ' + user.display_name)

    async def add_plain(self, title: str, msg: Message, frombot: bool = False) -> bool:
        if len(title) > 55:
            raise Exception('Movie names cannot be over 55 characters long.')
        isNew = self.db["movies"].count_documents({'title': self.clean_case(title)}) == 0
        if isNew:
            originator = self.bot.application_id if frombot else msg.author.id
            self.db["movies"].insert_one({"title": title, "originator": self.db["users"].find_one({'username': originator}).get('_id'), 'nominated': False})
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

    def clean_search(self, text: str):
        return re.compile(".*" + re.escape(text) + ".*", re.IGNORECASE)



async def setup(bot):
    await bot.add_cog(ButtCommands(bot))
