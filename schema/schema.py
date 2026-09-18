#https://www.mongodb.com/community/forums/t/defining-data-schema-using-pymongo/8533/2
#https://earthly.dev/blog/pymongo-advanced/
from datetime import datetime
from typing import TypedDict

from bson import ObjectId


class Movie(TypedDict):
    _id: ObjectId
    name: str
    originator: str
    nominated: bool
    nominator: str
    last_win_date: datetime
    #TODO: Add MovieRatings { numRatings: int, sum: int }

class Poll(TypedDict):
    _id: ObjectId
    server_id: int
    message_id: int
    poll_time: datetime
    poll_code: str
    open: bool

class Role(TypedDict):
    _id: ObjectId
    server_id: int
    role: str
    role_id: int

class User(TypedDict):
    _id: ObjectId
    username: int
    out: bool
    #TODO: Add UserRatings { {movie: str, rating: int}, etc}

class VoteBuy(TypedDict):
    _id: ObjectId
    voter: int
    chump: int
    numberVotes: int

#TODO: Deprecate into movie and user ratings, run script to backfill
class MovieRatings(TypedDict):
    _id: ObjectId
    user_id: int
    movie: str
    rating: int


