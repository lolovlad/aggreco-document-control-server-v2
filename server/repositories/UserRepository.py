from typing import List

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from httpx import AsyncClient

from ..models.User import UserGet
from ..response import get_client
from ..settings import settings


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/users/v1/login/sign-in/",
)


class UserRepository:
    """
    Репозиторий-адаптер к микросервису пользователей.
    Работает ТОЛЬКО через HTTP, локальную таблицу user не трогаем.
    Во все запросы (кроме явного get_user_profile_by_token) прокидываем
    текущий Bearer-токен и корректно обрабатываем 401.
    """

    def __init__(
        self,
        client: AsyncClient = Depends(get_client),
        token: str = Depends(oauth2_scheme),
    ):
        self._client: AsyncClient = client
        self._base_url = settings.user_service_url.rstrip("/")
        self._token: str = token

    async def get_user_by_uuid(self, uuid: str) -> UserGet | None:
        resp = await self._client.get(
            f"{self._base_url}/v1/user/get_one/{uuid}",
            headers={"Authorization": f"Bearer {self._token}"},
        )
        if resp.status_code == status.HTTP_401_UNAUTHORIZED:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unauthorized in user service",
            )
        if resp.status_code != 200:
            return None
        return UserGet.model_validate(resp.json())

    async def get_user_profile_by_token(self, token: str) -> UserGet | None:
        """
        Специальный метод, который использует переданный токен (например, при логине).
        """
        resp = await self._client.get(
            f"{self._base_url}/v1/user/get/profile",
            headers={"Authorization": f"Bearer {token}"},
        )
        if resp.status_code == status.HTTP_401_UNAUTHORIZED:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unauthorized in user service",
            )
        if resp.status_code != 200:
            return None
        return UserGet.model_validate(resp.json())

    async def get_users_by_uuids(self, user_uuids: List[str]) -> List[UserGet]:
        """
        Запрашивает список пользователей по их UUID через микросервис.
        """
        if not user_uuids:
            return []
        resp = await self._client.post(
            f"{self._base_url}/v1/user/by-uuids",
            json={"uuids": user_uuids},
            headers={"Authorization": f"Bearer {self._token}"},
        )
        if resp.status_code == status.HTTP_401_UNAUTHORIZED:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unauthorized in user service",
            )
        if resp.status_code != 200:
            return []
        data = resp.json()
        return [UserGet.model_validate(item) for item in data]

    async def get_users_by_context_email(self, context: str) -> list[UserGet]:
        """
        Проксирующий вызов в микросервис, который возвращает
        пользователей по флагу email_send_info[context] == true.
        """
        resp = await self._client.get(
            f"{self._base_url}/v1/user/search",
            params={"context": context},
            headers={"Authorization": f"Bearer {self._token}"},
        )
        if resp.status_code == status.HTTP_401_UNAUTHORIZED:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unauthorized in user service",
            )
        if resp.status_code != 200:
            return []
        data = resp.json()
        return [UserGet.model_validate(item) for item in data]
