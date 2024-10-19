from jose import JWTError, jwt

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer

from ..repositories import UserRepository
from ..models.User import UserGet, TypeUser
from ..models.UserLogin import UserLogin, Token, UserSigIn
from ..settings import settings
from ..tables import User
from datetime import datetime, timedelta

oauth2_cheme = OAuth2PasswordBearer(tokenUrl='/v1/login/sign-in/')


def get_current_user(token: str = Depends(oauth2_cheme)) -> UserGet:
    return LoginServices.validate_token(token)


class LoginServices:
    exception_unauthorized = HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                           detail="token",
                                           headers={
                                               "AggrecoDocument": 'Bearer'
                                           })

    def __init__(self, repo: UserRepository = Depends()):
        self.__repo: UserRepository = repo

    @classmethod
    def __decode_token(cls, token: str) -> dict:
        try:
            payload = jwt.decode(token,
                                 settings.jwt_secret,
                                 algorithms=[settings.jwt_algorithm])
        except JWTError:
            raise cls.exception_unauthorized

        return payload

    @classmethod
    def validate_token(cls, token: str) -> UserGet:
        payload = cls.__decode_token(token)
        user_data = payload.get("user")

        try:
            user = UserGet.model_validate(user_data)
        except Exception:
            raise cls.exception_unauthorized
        return user

    @classmethod
    def create_token(cls, user: User) -> Token:
        user_data = UserGet.model_validate(user, from_attributes=True)

        now = datetime.utcnow()

        payload = {
            'iat': now,
            'nbf': now,
            'exp': now + timedelta(seconds=settings.jwt_expiration_access),
            'sub': str(user_data.uuid),
            'user': user_data.model_dump()
        }
        token = jwt.encode(payload,
                           settings.jwt_secret,
                           algorithm=settings.jwt_algorithm)
        return Token(access_token=token,
                     user=user_data,
                     refresh_token=cls.create_refresh_token(user))

    @classmethod
    def create_refresh_token(cls, user: User) -> str:
        user_data = UserGet.model_validate(user, from_attributes=True)

        now = datetime.utcnow()

        payload = {
            'iat': now,
            'nbf': now,
            'exp': now + timedelta(seconds=settings.jwt_expiration_refresh),
            'sub': str(user_data.uuid)
        }
        token = jwt.encode(payload,
                           settings.jwt_secret,
                           algorithm=settings.jwt_algorithm)
        return token

    async def login_user(self, user_login: UserLogin, request: Request) -> Token:
        user = await self.__repo.get_user_by_email(user_login.email)
        if user:
            if user.check_password(user_login.password):
                return self.create_token(user)

    async def refresh_token(self, refresh_token: str) -> Token:
        uuid_user = self.__decode_token(refresh_token).get("sub")

        try:
            user = await self.__repo.get_user_by_uuid(uuid_user)
            return self.create_token(user)
        except Exception:
            raise self.exception_unauthorized
