import discord
import pymongo
from discord import Message
from discord.abc import Messageable
from cogs.actions.BaseAction import BaseAction
from cogs.actions.actionhelper import check_user, movies_with_in_nominators
from cogs.utils import cogutils
from cogs.utils.inpututils import clean_case, clean_search
import dateutil.parser as dparser

class MovieManaging(BaseAction):
    async def withdraw_movie(self, content: str, msg: Message):
        check_user(self.db, msg.author)
        if not content:
            self.db.movies.update_many(
                {"nominated": True, "nominator": self.db.users.find_one({"username": msg.author.id}).get('_id')},
                {"$set": {"nominated": False, "nominator": None}})
        else:
            nommedmovie = self.db.movies.find_one({"title": clean_case(content), "nominated": True})
            if nommedmovie is None:
                return await msg.channel.send('Are you sure that ' + content + ' is nominated?')
            nominator = self.db.users.find_one({'_id': nommedmovie.get('nominator')})
            if nominator.get('username') != msg.author.id:
                nominatoruser = await self.bot.fetch_user(nominator.get('username'))
                return await msg.channel.send(
                    content + ' must be removed by the nominator, ' + nominatoruser.display_name + '.')
            self.db.movies.update_one(
                {"title": clean_case(content), "nominated": True}, {"$set": {"nominated": False, "nominator": None}})
        await msg.add_reaction('🧻')

    async def find_movies(self, searchtext: str, msg: Message):
        if searchtext is None:
            return await msg.channel.send('You forgot to enter something to search for, I think.')

        films = self.db.movies.find({'title': clean_search(searchtext)}).sort('title', pymongo.ASCENDING)

        def description_builder(movie):
            lwd = movie.get('last_win_date')
            desc = movie.get('title')
            if lwd is not None:
                desc += ' - ' + str(lwd.date())
            desc += '\n'
            return desc

        for embed in cogutils.get_safe_embeds(films, description_builder, 'Found Movies:', discord.Colour.dark_gold()):
            await msg.channel.send(embed=embed)

    def get_my_movies(self, user: Message.author, only_free: bool = False):
        check_user(self.db, user)
        user_id = self.db.users.find_one({"username": user.id}).get('_id')
        if only_free:
            return self.db.movies.find({'originator': user_id, 'nominated': False, "last_win_date": {'$exists': False}})
        return self.db.movies.find({'originator': user_id})

    async def nominate_movie(self, title: str, msg: Message):
        isNew = await self.add_plain(title, msg)
        isNominated = self.db.movies.count_documents({'title': clean_case(title), 'nominated': True}) != 0
        if not isNew and isNominated:
            nominatorid = self.db.movies.find_one({'title': clean_case(title)}).get('nominator')
            nominator = self.db.users.find_one({'_id': nominatorid}).get('username')
            user = await self.bot.fetch_user(nominator)
            await msg.channel.send(title + ' already nominated by ' + user.display_name)
        else:
            check_user(self.db, msg.author)
            self.db.movies.update_one({"title": clean_case(title)}, {"$set": {"nominated": True,
                                                                              "nominator": self.db.users.find_one(
                                                                                  {"username": msg.author.id}).get(
                                                                                  '_id')}})
            last_win = self.db['movies'].find_one({'title': clean_case(title)}).get('last_win_date')
            if last_win is not None:
                await msg.channel.send(title + ' won on ' + str(last_win.date()))
            await msg.add_reaction('🗳️')

    async def nominate_db(self, title: str, msg: Message, user_nominated: bool = False):
        check_user(self.db, msg.author)
        if title is None:
            return await msg.channel.send('You forgot to enter something to nominate, I think.')

        if user_nominated:
            user_id = self.db.users.find_one({"username": msg.author.id}).get('_id')
            films = self.db.movies.find({'title': clean_search(title), 'nominated': False, 'originator': user_id}).sort(
                'title', pymongo.ASCENDING)
        else:
            films = self.db.movies.find({'title': clean_search(title), 'nominated': False}).sort('title',
                                                                                                 pymongo.ASCENDING)
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
        check_user(self.db, msg.author)
        if title is None:
            return await msg.channel.send('You forgot to enter something to steal, I think.')

        user_id = self.db.users.find_one({"username": msg.author.id}).get('_id')
        films = self.db.movies.find(
            {'title': clean_search(title), '$or': [{'nominated': False}, {'nominated': {'$exists': False}}]}).sort(
            'title',
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
            return await msg.channel.send(
                '`' + film['title'] + '` is your own movie, stealing it is legal and thus I will not assist you.')

        old_user = await self.bot.fetch_user(self.db.users.find_one({"_id": film['originator']}).get('username'))
        await msg.channel.send('⛵😏' + msg.author.name + '🏴‍☠️' + film['title'] + '🏴‍☠️  🌊🏝️🥺' + old_user.display_name)

        self.db.movies.update_one({'title': clean_case(film['title'])}, {'$set': {'originator': user_id}})
        return await self.nominate_movie(film['title'], msg)

    async def add_movie(self, title: str, msg: Message):
        isNew = await self.add_plain(title, msg)
        if not isNew:
            originatorid = self.db.movies.find_one({'title': clean_case(title)}).get('originator')
            originator = self.db.users.find_one({'_id': originatorid}).get('username')
            user = await self.bot.fetch_user(originator)
            await msg.channel.send(title + ' already added by ' + user.display_name)

    async def add_plain(self, title: str, msg: Message, frombot: bool = False) -> bool:
        if len(title) > 55:
            raise Exception('Movie names cannot be over 55 characters long.')
        isNew = self.db.movies.count_documents({'title': clean_case(title)}) == 0
        if isNew:
            originator = self.bot.application_id if frombot else msg.author.id
            self.db.movies.insert_one(
                {"title": title, "originator": self.db.users.find_one({'username': originator}).get('_id'),
                 'nominated': False})
            await msg.add_reaction('👍')
        return isNew

    async def get_nominations(self, channel: Messageable):
        nominated_movies = self.db.movies.find({"nominated": True})
        movies = movies_with_in_nominators(self.db, nominated_movies)
        titles = [[movie['title'], movie.get('last_win_date')] for movie in movies]
        msg = discord.Embed(colour=discord.Colour.yellow(), title='Current Nominations', description='')
        if len(titles) == 0:
            msg.description = 'No active nominations!'
        for title in titles:
            msg.description += title[0]
            if title[1] is not None:
                msg.description += ' - ' + str(title[1].date())
            msg.description += '\n'
            # msg.add_field(value= title)
        await channel.send(embed=msg)

    async def historical_add(self, dateAndMovie: str, msg: Message):
        histdate = dparser.parse(dateAndMovie.split(' ', 1)[0], fuzzy=True)
        if (len(dateAndMovie.split(' ', 1)) > 1):
            title = dateAndMovie.split(' ', 1)[1]
        else:
            return await msg.channel.send('You forgot to enter a movie, I think.')

        check_user(self.db, msg.author)
        isNew = await self.add_plain(title, msg, True)
        lastwindate = self.db.movies.find_one({'title': clean_case(title)}).get('last_win_date')
        if lastwindate is not None and lastwindate > histdate:
            return await msg.channel.send(
                title + ' last won on ' + str(lastwindate.date()) + ', which is more recent than ' + str(
                    histdate.date()) + '.')

        self.db.movies.update_one({'title': clean_case(title)}, {'$set': {'last_win_date': histdate}})
        return await msg.add_reaction('📅')

    async def delete_movie(self, title: str, msg: Message):
        if self.db.movies.count_documents({"title": clean_case(title),
                                           "originator": self.db.users.find_one({'username': msg.author.id}).get(
                                                   '_id')}) != 0:
            self.db.movies.delete_one({"title": clean_case(title),
                                       "originator": self.db.users.find_one({'username': msg.author.id}).get('_id')})
            await msg.add_reaction('🗑')
        else:
            await msg.channel.send(
                'Movies can only be removed by the user who added them or the movie has already been deleted.')

    async def have_we_watched(self, searchtext: str, msg: Message):
        watched = []
        if (searchtext is None):
            watched = self.db.movies.find({'last_win_date': {'$exists': True }})
        else:
            movie = self.db.movies.find_one({'title': clean_case(searchtext), 'last_win_date':{'$exists': True}})
            if movie is not None:
                watched = self.db.movies.find({'title': clean_case(searchtext), 'last_win_date':{'$exists': True}})
            else:
                result = '`' + searchtext + '` has not been watched.'
                messyfind = self.db.movies.find_one({'title': clean_search(searchtext), 'last_win_date':{'$exists': True}})
                if messyfind is None:
                    return await msg.channel.send(result)
                result += ' Maybe one of these is what you are looking for?'
                await msg.channel.send(result)
                watched = self.db.movies.find({'title': clean_search(searchtext), 'last_win_date': {'$exists': True}})

        watched = watched.sort('last_win_date', pymongo.ASCENDING)

        def description_builder(watch):
            lwd = watch.get('last_win_date')
            return watch.get('title') + ' - ' + str(lwd.date()) + '\n'

        for embed in cogutils.get_safe_embeds(watched, description_builder, 'Watched Movies', discord.Colour.dark_gold()):
            await msg.channel.send(embed=embed)

    async def score(self, msg: Message):
        films = list(self.db.movies.find({"last_win_date": {'$exists': True}}))
        users = list(self.db.users.find())
        scores = dict()
        for film in films:
            nom = film.get("originator")
            for user in users:
                if user.get("_id") == nom and nom is not None:
                    if user.get('username') not in scores:
                        scores[user.get('username')] = 1
                        break
                    else:
                        scores[user.get('username')] = scores[user.get('username')]+1
                        break

        def score_builder(userToTotal):
            return userToTotal[0] + ' - ' + str(userToTotal[1]) + '\n'

        orderedscores = list(map(list, sorted(scores.items(), key=lambda item: item[1], reverse=True)))

        for score in orderedscores:
            usr = await self.bot.fetch_user(score[0])
            score[0] = usr.display_name

        for embed in cogutils.get_safe_embeds(orderedscores, score_builder, 'Movie Night Wins',
                                              discord.Colour.dark_gold()):
            await msg.channel.send(embed=embed)