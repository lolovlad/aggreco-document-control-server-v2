from jose import JWTError, jwt

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from httpx import AsyncClient

from .DocumentService import DocumentService
from ..repositories import UserRepository
from ..models.User import UserGet, TypeUser
from ..models.UserLogin import UserLogin, Token, RedirectYandex
from ..settings import settings
from ..response import get_client
from datetime import datetime, timedelta

import re

USER_PROFILE_URL = f"{settings.user_service_url.rstrip('/')}/v1/user/get/profile"

oauth2_cheme = OAuth2PasswordBearer(
    tokenUrl="/api/users/v1/login/sign-in/"
)


exception_unauthorized = HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                           detail="token",
                                           headers={
                                               "AgcDocument": 'Bearer'
                                           })


async def get_current_user(
    token: str = Depends(oauth2_cheme),
    client: AsyncClient = Depends(get_client),
) -> UserGet:
    try:
        response = await client.get(
            USER_PROFILE_URL,
            headers={"Authorization": f"Bearer {token}"},
        )
    except Exception:
        raise exception_unauthorized

    if response.status_code != 200:
        raise exception_unauthorized

    data = response.json()
    return UserGet.model_validate(data)
