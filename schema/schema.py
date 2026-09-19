from datetime import datetime
from typing import TypedDict

from bson import ObjectId

class MovieRating:
    count: int
    sum: int

class Movie(TypedDict):
    _id: ObjectId
    title: str
    originator: str
    nominated: bool
    nominator: str
    last_win_date: datetime
    movie_rating: MovieRating

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

class MovieRatings(TypedDict):
    _id: ObjectId
    user_id: ObjectId
    movie: str
    rating: int


