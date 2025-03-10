from pydantic import BaseModel
from ..models.User import UserGet


class Token(BaseModel):
    access_token: str
    refresh_token: str = None
    token_type: str = 'bearer'
    user: UserGet


class UserSigIn(BaseModel):
    token: Token


class UserLogin(BaseModel):
    email: str
    password: str


class RedirectYandex(BaseModel):
    url: str

