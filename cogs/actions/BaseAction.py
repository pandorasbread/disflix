from discord.ext.commands import Bot
from pymongo import database


class BaseAction:
    def __init__(self, db: database.Database, bot: Bot):
        self.bot = bot
        self.db = db
