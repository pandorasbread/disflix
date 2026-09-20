import discord
from discord import Message
from pymongo import database


def check_user(db: database, user: Message.author):
    if db.users.count_documents({"username": user.id}) == 0:
        db.users.insert_one({"username": user.id, "out": False})


def tag_role(db: database, rolename: str, server: discord.Guild):
    role = db['roles'].find_one({'server_id': server.id, 'role': rolename})
    if role is None:
        return ""
    return server.get_role(role.get('role_id')).mention + "\r\n"


def movies_with_in_nominators(db: database, nominated_movies):
    nominators_out = [user['_id'] for user in db.users.find({"out": True})]
    movies = []
    for movie in nominated_movies:
        if movie.get("nominator") not in nominators_out:
            movies.append(movie)
    return movies
