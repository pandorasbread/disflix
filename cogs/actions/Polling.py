import base64
import datetime
import os

import discord
from discord import Message
from cogs.actions.BaseAction import BaseAction
from cogs.utils.inpututils import *
from cogs.actions.actionhelper import movies_with_in_nominators, tag_role

class Polling(BaseAction):
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

        movies = self.db.movies.find({"nominated": True})
        movies = movies_with_in_nominators(self.db, movies)
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
        await msg.channel.send(tag_role(self.db, 'movie_watcher', msg.guild))
        sent_poll = await msg.channel.send(poll=result)

        self.db['polls'].insert_one({'server_id': msg.guild.id, 'message_id': sent_poll.id, 'channel_id':sent_poll.channel.id, 'poll_time': datetime.datetime.now(tz=datetime.timezone.utc), 'poll_code':poll_code, 'open':True})

    async def end_poll(self, roll: bool, msg: Message):
        poll = self.db['polls'].find_one({'server_id': msg.guild.id, 'poll_time': {"$lt": datetime.datetime.now(tz=datetime.timezone.utc)}, 'open': True})
        channel = await self.bot.fetch_channel(poll.get('channel_id'))
        pollmessage = await channel.fetch_message(poll.get('message_id'))
        sortedlist = sorted(pollmessage.poll.answers, key=lambda a: a.vote_count, reverse=True)
        winners = [answer for answer in sortedlist if answer.vote_count == sortedlist[0].vote_count]
        if len(winners) == 1:
            await msg.channel.send(tag_role(self.db, 'movie_watcher', msg.guild) + winners[0].text + ' is the winner!')
            self.db['movies'].update_one({'title': clean_case(winners[0].text)}, {'$set': {'last_win_date': datetime.datetime.today()}})
            nominators_out = [user['_id'] for user in self.db.users.find({"out": False})]
            self.db['movies'].update_many({'nominated': True, 'nominator': {'$in': nominators_out}}, {'$set': {'nominated': False, 'nominator': None}})
            self.db['polls'].update_one({'message_id': poll.get('message_id')}, {'$set': {'open':False}})
            self.db['users'].update_many({}, {'$set': {'out':False}})
            await pollmessage.poll.end()
        else:
            for answer in sortedlist:
                if answer.vote_count != sortedlist[0].vote_count:
                    self.db['movies'].update_one({'title': answer.text, 'nominated': True}, {'$set': {'nominated': False, 'nominator': None}})
            self.db['polls'].update_one({'message_id': poll.get('message_id')}, {'$set': {'open': False}})
            await pollmessage.poll.end()
            await self.run_poll(msg, True)



