import discord

from cogs.actions.actionhelper import check_user
from cogs.actions.BaseAction import BaseAction
from cogs.utils import cogutils
from cogs.utils.inpututils import *
from datetime import datetime
from discord import Message
from schema.schema import *


class Rating(BaseAction):
    async def rate_movie(self, rating_info: str, msg: Message):
        # Split message into the rating and the Title ex 10 Jurassic Park makes rating 10 and title Jurassic Park
        rating, title = rating_info.split(" ", maxsplit=1)
        delete_rating = False
        force_rate = False

        # If rating is a 'x', set the rating to be deleted
        if rating == 'x':
            delete_rating = True
            rating: float = 0.0
        else:
            if 'n' in rating:
                force_rate = True
                rating = str(rating).replace('n', '')
            try:
                rating: float = round(float(rating), 2)
                # Check to see if rating is between 0 and 10.0
                if not 0 <= rating <= 10.0:
                    await msg.channel.send(f'Rating {str(rating)} is not between 0 and 10.')
                    return
            except ValueError:
                # If the value has an error, put possible reasons why
                return await msg.channel.send(
                    'Hey, I think you messed up bub. You either:\n'
                    '* Put your Title in from of the rating. It should looke like `$rate 10 Your Mom`\n'
                    '* Put a letter that wasn\'t "n" to add a movie. That would look like `$rate n1 Your Dad`\n'
                    'Fix your command and come back!')

        # Get the User of the command
        check_user(self.db, msg.author)
        user: User = self.db.users.find_one({"username": msg.author.id})  # .get('_id')
        user_id = user['_id']

        # Use the Title saves in the Movies table. If the Movie 
        title_search = self.db.movies.find_one({'title': clean_search(title)})
        if title_search is None:
            if force_rate == True:
                if len(title) > 55:
                    raise Exception('Movie names cannot be over 55 characters long.')
                originator = msg.author.id
                # Insert Movie into the Database
                self.db.movies.insert_one(
                    {"title": title, "originator": self.db.users.find_one({'username': originator}).get('_id'),
                    'nominated': False})
                await msg.add_reaction('👍')
                full_title = title
            else:
                return await msg.channel.send(f'Movie {title} does not exist. To add the movie to the database with your rating, add a \'n\' to the rating. Ex. `$rate n8 New Movie`')
        else:
            if force_rate == True:
                return await msg.channel.send(f'Trying to get around using the new movie flag huh? Watch the movie for a movie night to rate this movie, or else... -BUTTSPLUG')
            else:
                full_title = title_search.get('title')

        if delete_rating:
            user_rating = next((x['rating'] for x in user['user_ratings'] if x['title'] == full_title), None)

            self.db.users.update_one({"_id": user_id}, {"$pull": {"user_ratings": {"title": full_title}}})
            self.db.movies.update_one({"title": full_title},
                                      {"$inc": {"movie_rating.sum": -user_rating, "movie_rating.count": -1}})
            return await msg.channel.send(f'{full_title}\'s rating has been deleted')

        # Shouldn't ever hit here, but if title and rating are none, send a message back
        if title is None and rating is None:
            await msg.channel.send('You didn\'t even put a movie or a rating...')

        # Check if movie exists. If not, send back a message
        if self.db.movies.count_documents({'title': clean_search(title)}) == 0:
            return await msg.channel.send(f'Movie {title} does not exist.')

        # If not forcing a rating, search to see if the movie has been watched, and if not, return a message
        if force_rate == False:
            movie = self.db.movies.find_one({'title': clean_search(title), 'last_win_date': {'$exists': True}})
            if movie is None:
                return await msg.channel.send(f'{full_title} has not been watched for Movie Night so it cannot be rated yet. '
                                               'Use the $hist command to add watch history to a movie if this is a mistake.')

        # If already rated before, update the row. If not, add a new row.
        if self.db.users.count_documents({'_id': user_id, 'user_ratings.title': full_title}) != 0:
            user_rating = next((x['rating'] for x in user['user_ratings'] if x['title'] == full_title), None)
            self.db.users.update_one({"_id": user_id, "user_ratings.title": full_title}, {"$set": {"user_ratings.$.rating": rating}})
            self.db.movies.update_one({'title': full_title}, {'$inc': {'movie_rating.sum': rating - user_rating}}, upsert=True)
            await msg.add_reaction('🍿')
            await msg.channel.send(f'You have updated your rating of {full_title} to {str(rating)}')
        else:
            self.db.users.update_one({'_id': user_id}, {'$addToSet': {'user_ratings': {'title': full_title, 'rating': rating}}}, upsert=True)
            self.db.movies.update_one({'title': full_title}, {'$inc': {'movie_rating.count': 1, 'movie_rating.sum': rating}}, upsert=True)
            await msg.add_reaction('🍿')
            await msg.channel.send(f'You have rated {full_title} a score of {str(rating)}')


    async def get_user_ratings(self, flag: str, msg: Message):
        # Get the username and their list of movie reviews
        check_user(self.db, msg.author)
        ratings: list[UserRating] = list(self.db.users.find_one({"username": msg.author.id}).get('user_ratings'))
        # If user gives the n flag after the command, sort by rating. Else, default to title
        if flag == 'n':
            ratings.sort(key=lambda x: x['rating'], reverse=True)
            embed = discord.Embed(colour=discord.Colour.orange(), title='My Movie Ratings - Sorted by Rating', description='')
        else:
            ratings.sort(key=lambda x: x['title'])
            embed = discord.Embed(colour=discord.Colour.orange(), title='My Movie Ratings - Sorted Alphabetically', description='')
        for rating in ratings:
            embed.description += rating['title'] + " - " + str(rating['rating'])
            embed.description += '\n'
        await msg.channel.send(embed=embed)


    async def get_movie_ratings(self, title: str, msg: Message):
        if title == None:
            await msg.channel.send(f'Didja forget a title?')
            return

        # Check if movie exists. If not, send back a message
        if self.db.movies.count_documents({'title': clean_search(title)}) == 0:
            await msg.channel.send(f'Movie {title} does not exist.')
            return

        # Get Ratings in Desending (Highest Rating Value) order
        movie: Movie = self.db.movies.find_one({'title': clean_search(title)})

        embed = discord.Embed(colour=discord.Colour.orange(), title=f'Ratings for {movie["title"]}', description='')

        users_that_rated: list[User] = list(self.db.users.find({"user_ratings.title": movie['title']}))
        if len(users_that_rated) == 0:
            return await msg.channel.send(f'Movie has not been rated.')
        # For each rating, get the username of the member who rated it and their rating per line.
        for rating in users_that_rated:
            username = rating['username']
            user = await self.bot.fetch_user(username)
            embed.description += user.name + ' - ' + str(
                next((x['rating'] for x in rating['user_ratings'] if x['title'] == movie['title']), 'N/A'))
            embed.description += '\n'

        # Calculate the average
        average: float = movie['movie_rating']['sum'] / movie['movie_rating']['count']
        embed.description += '\n'
        embed.description += f'**Average Rating:**  {str(round(average, 2))}'

        await msg.channel.send(embed=embed)


    async def get_top_ratings(self, msg: Message):
        MAX_RATINGS = 10  # Current Max number of Top Movie ratings
        # Get the list of every distinct movie title in the `movieratings` table
        movies: list[Movie] = list(
            self.db.movies.find({'movie_rating': {'$exists': True}, 'movie_rating.count': {'$gt': 0}, 'last_win_date': {'$exists': True}}))
        movies.sort(key=lambda x: round(x['movie_rating']['sum'] / x['movie_rating']['count'], 2), reverse=True)

        def description_builder(mov):
            average: float = round(mov['movie_rating']['sum'] / mov['movie_rating']['count'], 2)
            return f'## **{mov["title"]}** - **{str(average)}**\n'

        for embed in cogutils.get_safe_embeds(movies[:MAX_RATINGS], description_builder, 'Top Movie Reviews',
                                              discord.Colour.yellow()):
            await msg.channel.send(embed=embed)

    #this was used to migrate from the old UserRating table to Movie.movie_rating and User.user_ratings[]
    #async def migrate_ratings(self, msg):
    #    legacy_ratings: list[MovieRatings] = list(self.db.movieratings.find())
    #    for leg in legacy_ratings:
    #        self.db.movies.update_one({'title':leg['movie']}, {'$inc': {'movie_rating.count': 1, 'movie_rating.sum': leg['rating']}}, upsert=True)
    #        self.db.users.update_one({'_id': leg['user_id']}, {"$addToSet": {"user_ratings": {'title': leg['movie'], 'rating': leg['rating']}}}, upsert=True)
    #    await msg.channel.send(str(len(legacy_ratings)) + ' ratings migrated.')