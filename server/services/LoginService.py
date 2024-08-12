from jose import JWTError, jwt

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..tables import User
from ..models.User import UserGet, TypeUser
from ..models.UserLogin import UserLogin, Token, UserSigIn
from ..database import get_session
from ..settings import settings
from datetime import datetime, timedelta

oauth2_cheme = OAuth2PasswordBearer(tokenUrl='/v1/login/sign-in/')


def get_current_user(token: str = Depends(oauth2_cheme)) -> UserGet:
    return LoginServices.validate_token(token)


class LoginServices:
    def __init__(self, session: AsyncSession = Depends(get_session)):
        self.__session = session

    async def __get(self, email: str) -> User:
        response = select(User).where(User.email == email)
        result = await self.__session.execute(response)
        user = result.scalars().first()
        return user

    @classmethod
    def validate_token(cls, token: str) -> UserGet:
        exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                  detail="token",
                                  headers={
                                      "AggrecoDocument": 'Bearer'
                                  })
        try:
            payload = jwt.decode(token,
                                 settings.jwt_secret,
                                 algorithms=[settings.jwt_algorithm])
        except JWTError:
            raise exception

        user_data = payload.get("user")

        try:
            user = UserGet.model_validate(user_data)
        except Exception:
            raise exception
        return user

    @classmethod
    def create_token(cls, user: User) -> Token:
        user_data = UserGet.model_validate(user, from_attributes=True)

        now = datetime.utcnow()

        payload = {
            'iat': now,
            'nbf': now,
            'exp': now + timedelta(seconds=settings.jwt_expiration),
            'sub': str(user_data.uuid),
            'user': user_data.model_dump()
        }
        token = jwt.encode(payload,
                           settings.jwt_secret,
                           algorithm=settings.jwt_algorithm)
        return Token(access_token=token, user=user_data)

    async def login_user(self, user_login: UserLogin, request: Request) -> Token:
        user = await self.__get(user_login.email)
        if user:
            if user.check_password(user_login.password):
                return self.create_token(user)
