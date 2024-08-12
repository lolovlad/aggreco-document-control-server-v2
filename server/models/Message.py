from pydantic import BaseModel
from typing import List
from enum import Enum


class TypeStatus(int, Enum):
    GRANTED = 1
    FORBIDDEN = 2
    BANED = 3


class Message(BaseModel):
    message: str


'''class Answers(BaseModel):
    menu: dict
    answers: List[AnswerGet]

'''


class StatusUser(BaseModel):
    id_user: int
    status: TypeStatus