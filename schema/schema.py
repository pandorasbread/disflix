#https://www.mongodb.com/community/forums/t/defining-data-schema-using-pymongo/8533/2
#https://earthly.dev/blog/pymongo-advanced/
import datetime
from typing import TypedDict

class Movie(TypedDict):
    _id: str
    name: str
    originator: str
    nominated: bool
    nominator: str
    last_win_date: datetime
    #TODO: Add MovieRatings { numRatings: int, sum: int }

class Poll(TypedDict):
    _id: str
    server_id: int
    message_id: int
    poll_time: datetime
    poll_code: str
    open: bool

class Role(TypedDict):
    _id: str
    server_id: int
    role: str
    role_id: int

class User(TypedDict):
    _id: str
    username: int
    out: bool
    #TODO: Add UserRatings { {movie: str, rating: int}, etc}

class VoteBuy(TypedDict):
    _id: str
    voter: int
    chump: int
    numberVotes: int

#TODO: Deprecate into movie and user ratings, run script to backfill
class MovieRatings(TypedDict):
    _id: str
    user_id: int
    movie: str
    rating: int


