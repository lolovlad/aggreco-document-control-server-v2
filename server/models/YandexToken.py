from pydantic import BaseModel


class YandexToken(BaseModel):
    access_token: str
    expires_in: int
    refresh_token: str
    token_type: str


class YandexUser(BaseModel):
    login: str
    default_email: str
    id: str
    client_id: str
    emails: list[str]
    psuid: str
