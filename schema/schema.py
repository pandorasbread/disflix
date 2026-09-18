#https://www.mongodb.com/community/forums/t/defining-data-schema-using-pymongo/8533/2
#https://earthly.dev/blog/pymongo-advanced/
from datetime import datetime
from typing import TypedDict

from bson import ObjectId

class MovieRating:
    rating_count: int
    sum: int

class Movie(TypedDict):
    _id: ObjectId
    title: str
    originator: str
    nominated: bool
    nominator: str
    last_win_date: datetime
    movie_rating: MovieRating
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

class UserRating(TypedDict):
    title: str
    rating: int

class User(TypedDict):
    _id: ObjectId
    username: int
    out: bool
    user_ratings: list[UserRating]

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


