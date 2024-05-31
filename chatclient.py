import discord
import asyncio
from discord.ext.commands import Bot
from dotenv import load_dotenv, find_dotenv
import os

async def start_bot():
    intents = discord.Intents.default()
    intents.message_content = True
    bot = Bot("$", intents=intents, max_messages=None)


    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            print(filename)
            await bot.load_extension(f'cogs.{filename[:-3]}')
    load_dotenv(find_dotenv())
    token = str(os.environ.get('BUTTFRIEND_TOKEN'))
    await bot.start(token)

asyncio.run(start_bot())

