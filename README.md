# disflix
This is a bot for a discord server full of friends. It currently:
- Handles nominations, polls, and voting of movies for movie nights
- Creates a database of acronyms to reference
 
It does this all using MongoDB's Atlas as a database and discord.py, without which, this project would be a lot more annoying :>

## Dependencies
- `pip install -r requirements`
- Additionally you need to create a file named `.env` that looks like:
BUTTFRIEND_TOKEN='enter token here'
MONGO_CONNECTION='enter mongodb token here'
DB_NAME='the db name'
OMDB_KEY='access to Open Movie DataBase' -> this is actually unused so this can be left out. I was trying to see if OMDB would fuzzy search for me - unfortunately not :(

## What's the point?
Long ago, we would have chaos when picking movies for our Friday movie nights. Nominations would trickle in over the course of a few days and would be manually added to a pinned message in a channel.  Then on Friday nights, we would run a poll to pick a movie, enabling multiple votes the more movies there were. We could hold tiebreakers which would still mean manually entering movies into a poll. This was annoying to do.
As a minor workaround, we tried to clean this up by creating a separate channel specifically for aggregating movies to vote on and handle the voting. This was still annoying, as we kept movie discussion out of this channel. 

Then I created this bot, and all was right. Handles nominations. Handles movie withdrawls. Handles tracking who added movie titles to our database. Runs polls. Runs tiebreakers. Tracks wins. Oh yeah. It can do it all.

## What was it about acronyms?
I added a low effort command to write out full acronyms. It's just a dictionary, nothing fancy.