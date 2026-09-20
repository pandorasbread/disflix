import discord
from discord.ext.commands import Cog
from discord import Message
from discord.ext.commands import Bot
from pymongo import database
from pymongo.mongo_client import MongoClient
from dotenv import load_dotenv
from cogs.actions.MovieManaging import MovieManaging
from cogs.actions.Polling import Polling
from cogs.actions.actionhelper import check_user
from cogs.actions.RoleManaging import RoleManaging
from cogs.actions.Votebuying import Votebuying
from cogs.actions.Rating import Rating
from cogs.utils.inpututils import *
import os
import random



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
    def registerCommands(self, db: database.Database, bot: Bot):
        self.ratingCommands = Rating(db, bot)
        self.voteBuyingCommands = Votebuying(db, bot)
        self.roleCommands = RoleManaging(db, bot)
        self.pollCommands = Polling(db, bot)
        self.movieCommands = MovieManaging(db, bot)

    def __init__(self, bot: Bot):
        self.bot = bot
        load_dotenv()
        self.mongo = MongoClient(str(os.environ.get('MONGO_CONNECTION')))
        self.db = self.mongo[str(os.environ.get('DB_NAME'))]
        self.registerCommands(self.db, bot)

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
                content = sanitize_input(content)

            if command == '$testing':
                await msg.channel.send('uwu')
            if command == '$whoami':
                await self.get_user(content, msg)
            if command == '$add':
                check_user(self.db, msg.author)
                await self.movieCommands.add_movie(content, msg)
            if command == '$delete':
                await self.movieCommands.delete_movie(content, msg)
            if command == '$nominate' or command == '$nom': #maybe add custom emoji to movie?
                check_user(self.db, msg.author)
                await self.movieCommands.nominate_movie(content, msg)
            if command == '$nommy' or command ==  '$nommysorry' or command == '$qn' or command == '$qnom':
                await self.movieCommands.nominate_db(content, msg, True)
            if command == '$nomdb':
                await self.movieCommands.nominate_db(content, msg, False)
            if command == '$omnomnom':
                await self.movieCommands.omnomnom(content, msg)
            if command == '$nominations' or command == '$noms':
                await self.movieCommands.get_nominations(msg.channel)
            if command == '$withdraw' or command == '$w':
                await self.movieCommands.withdraw_movie(content, msg)
            if command == '$randomnom':
                mymovies = self.movieCommands.get_my_movies(msg.author, True)
                titles = [movie.get('title') for movie in mymovies]
                if len(titles) == 0:
                    await msg.channel.send('You have no movies left to nominate randomly.')
                    return
                randmovie = random.choice(titles)
                await msg.channel.send('Nominating \'' + randmovie + '\'.')
                await self.movieCommands.nominate_movie(randmovie, msg)
            if command == '$clear':
                self.db.movies.update_many({"nominated": True}, {'$set': {"nominated": False, 'nominator': None}})
                await msg.add_reaction('🧻')
            if command == '$mymovies':
                mymovies = self.movieCommands.get_my_movies(msg.author)
                embed = discord.Embed(colour=discord.Colour.dark_red(), title='My Movies', description='')
                for movie in mymovies:
                    lwd = movie.get('last_win_date')
                    embed.description += movie.get('title')
                    if lwd is not None:
                        embed.description += ' - ' + str(lwd.date())
                    embed.description += '\n'
                await msg.channel.send(embed=embed)
            if command == '$havewewatched' or command == '$watched' or command == '$hww':
                return await self.movieCommands.have_we_watched(content, msg)
            if command == '$find' or command == '$search' or command == '$f' or command == '$s':
                return await self.movieCommands.find_movies(content, msg)
            if command == '$hist' or command == '$ha' or command == '$ah' or command == '$addhistory' or command == '$addh': #like $ha 04/20/2020 rise of skywalker
                await self.movieCommands.historical_add(content, msg)
            if command == '$wins':
                await self.movieCommands.score(msg)
            if command == '$poll' or command == '$vote':
                await self.pollCommands.run_poll(msg)
            if command == '$endvote' or command == '$endpoll':
                await self.pollCommands.end_poll(content == 'roll', msg)
            if command == '$movierole':
                await self.roleCommands.addrole(content, msg, 'movie_watcher')
            if command == '$buyvote':
                await self.voteBuyingCommands.add_user_vote(content, msg)
            if command == '$usevote':
                await self.voteBuyingCommands.use_user_vote(content, msg)
            if command == '$checkvotes':
                await self.voteBuyingCommands.get_owned_votes(msg)
            if command == '$deletevotes':
                await self.voteBuyingCommands.delete_owned_votes(msg)
            if command == '$rate':
                await self.ratingCommands.rate_movie(content, msg)
            if command == '$myratings':
                await self.ratingCommands.get_user_ratings(msg)
            if command == '$ratings':
                await self.ratingCommands.get_movie_ratings(content, msg)
            if command == '$topratings':
                await self.ratingCommands.get_top_ratings(msg)
            if command == '$migrateratings':
                await self.ratingCommands.migrate_ratings(msg)
            if command == '$out':
                check_user(self.db, msg.author)
                self.db.users.update_one({"username":msg.author.id}, {"$set": {"out":True}})
                await msg.add_reaction('🏃')
            if command == '$in':
                check_user(self.db, msg.author)
                self.db.users.update_one({"username":msg.author.id}, {"$set": {"out":False}})
                await msg.add_reaction('👁')
            # if command == '$swap':
            #if command == '$roll':
            #if command == '$rollall':
            # if command == '$audit':
            # if command == '$bestpicks':
        except Exception as e:
            print(e)
            await msg.channel.send('ERROR: '+str(e))

    def add_omdb(self, title: str, msg: Message):
        return
    
    async def get_user(self, user: str, msg: Message):
        user_id_int = int(user.strip("<@!>"))
        user = await self.bot.fetch_user(user_id_int)
        if user:
            await msg.channel.send(f"You are {user.display_name}")
        else:
            await msg.channel.send('You don\'t exist')

async def setup(bot):
    await bot.add_cog(ButtCommands(bot))
