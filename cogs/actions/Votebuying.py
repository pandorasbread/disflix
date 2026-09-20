import discord
from discord import Message
from cogs.actions.BaseAction import BaseAction
from cogs.actions.actionhelper import check_user


class Votebuying(BaseAction):
    async def add_user_vote(self, voter: str, msg: Message):
        check_user(self.db, msg.author)
        # Strip the Voter id from the Tagged user
        voter_id_int = int(voter.strip("<@!>"))
        # Get User information
        voter_user = await self.bot.fetch_user(voter_id_int)
        buyer_user = await self.bot.fetch_user(msg.author.id)
        if self.db.votebuys.count_documents({'voter': voter_user.id, 'chump': buyer_user.id}) != 0:
            # If data of the Voter and Chump already exist, update the `numberVotes` by 1
            bribe_info = self.db.votebuys.find_one_and_update({'voter': voter_user.id, 'chump': buyer_user.id},
                                                              {"$inc": {"numberVotes": 1}}).get("numberVotes")
            await msg.channel.send(
                voter_user.display_name + ' has has a vote bought again by ' + buyer_user.display_name + ' and now has ' + str(
                    bribe_info + 1) + ' votes bought.'
                + voter_user.display_name + ', please vote for the bought vote movie or face the wrath of the BUTTDFV.')  # You don't want this!!
        else:
            # If data of the Voter and Chump doesnt exist, start a new count
            self.db.votebuys.insert_one({'voter': voter_user.id, 'chump': buyer_user.id, "numberVotes": 1})
            await msg.channel.send(voter_user.display_name + ' has had a vote bought by ' + buyer_user.display_name)

    async def use_user_vote(self, chump: str, msg: Message):
        check_user(self.db, msg.author)
        # Strip the Chump id from the Tagged user
        chump_id_int = int(chump.strip("<@!>"))
        # Get User information
        chump_user = await self.bot.fetch_user(chump_id_int)
        voter_user = await self.bot.fetch_user(msg.author.id)
        # Check to see if the Voter and Chump relationship exists and if there is at least one vote
        if self.db.votebuys.count_documents(
                {'voter': voter_user.id, 'chump': chump_user.id}) != 0 and self.db.votebuys.find_one(
                {'voter': voter_user.id, 'chump': chump_user.id}).get('numberVotes') > 0:
            # If data of the Voter and Chump exists, decrease the `numberVotes` by 1
            bribe_info = self.db.votebuys.find_one_and_update({'voter': voter_user.id, 'chump': chump_user.id},
                                                              {"$inc": {"numberVotes": -1}}).get("numberVotes")
            await msg.channel.send(
                voter_user.display_name + ' has used a bribed vote from ' + chump_user.display_name + '.  '
                + chump_user.display_name + ' must now vote for the movie that ' + voter_user.display_name + ' says or they will face the wrath of the BUTTDVF')  # You don't want this!!
            if (bribe_info - 1) > 0:
                # If the voter still has votes from this chump, let them know
                await msg.channel.send(voter_user.display_name + ' still has ' + str(
                    bribe_info - 1) + ' votes from ' + chump_user.display_name)
        else:
            # Either doesnt exist or the count is 0
            await msg.channel.send("You have no votes bought by this user.")

    async def get_owned_votes(self, msg: Message):
        check_user(self.db, msg.author)
        voter_user = await self.bot.fetch_user(msg.author.id)
        votes = self.db.votebuys.find({'voter': voter_user.id})

        embed = discord.Embed(colour=discord.Colour.orange(), title='My Bribed Votes', description='')
        for vote in votes:
            chump_user = await self.bot.fetch_user(vote.get('chump'))
            embed.description += str(chump_user.display_name) + ' - ' + str(vote.get('numberVotes'))
            embed.description += '\n'
        await msg.channel.send(embed=embed)

    async def delete_owned_votes(self, msg: Message):
        def check(message: Message):
            # Check if the message is from the same author and in the same channel
            return message.author == msg.author and message.channel == msg.channel

        check_user(self.db, msg.author)
        # Since we delete all the voter values, check to make sure they really want to do this
        await msg.channel.send("Are you sure you want to delete all your saved votes? Reply YES to Delete")
        try:
            reply: Message = await self.bot.wait_for('message', check=check, timeout=60.0)
            if reply.content == 'YES':
                voter_user = await self.bot.fetch_user(msg.author.id)
                self.db.votebuys.delete_many({'voter': voter_user.id})
                await msg.add_reaction('🗑')
                await msg.channel.send("All saved votes have been deleted")
            else:
                # Any value other than YES goes here
                await msg.channel.send("Votes not Deleted")
        except TimeoutError:
            # Message if Timeout happens
            await msg.channel.send("Answer not recieved. Not deleting votes.")