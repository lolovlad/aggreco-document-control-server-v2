from typing import List, Tuple

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from httpx import AsyncClient

from ..models.Object import GetObject, PostObject, UpdateObject
from ..response import get_client
from ..settings import settings


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/users/v1/login/sign-in/",
)


class ObjectRepository:
    """
    Репозиторий-адаптер к микросервису Object & Equipment.
    Полностью заменяет прямую работу с локальными таблицами Object/ObjectToUser.
    """

    def __init__(
        self,
        client: AsyncClient = Depends(get_client),
        token: str = Depends(oauth2_scheme),
    ):
        self._client: AsyncClient = client
        self._base_url = settings.object_equipment_service_url.rstrip("/")
        self._token: str = token

    def _auth_headers(self) -> dict:
        return {"Authorization": f"Bearer {self._token}"}

    async def count_row(self) -> int:
        """
        Возвращает количество объектов.
        Реализовано через получение полного списка (предполагается умеренный размер справочника).
        """
        objects = await self.get_all_object(filter_user=None)
        return len(objects)

    async def get_limit_object(self, start: int, count: int) -> List[GetObject]:
        """
        Пагинация объектов на основе эндпоинта /v1/object/page.
        """
        page = start // count + 1
        resp = await self._client.get(
            f"{self._base_url}/v1/object/page",
            params={"page": page, "per_item_page": count},
            headers=self._auth_headers(),
        )
        if resp.status_code == status.HTTP_401_UNAUTHORIZED:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unauthorized in object-equipment service",
            )
        resp.raise_for_status()
        data = resp.json()
        return [GetObject.model_validate(item) for item in data]

    async def get_all_object(self, filter_user: str | None) -> List[GetObject]:
        """
        Возвращает список объектов.
        filter_user здесь используется только как флаг:
        - None  -> запрашиваем все объекты (для админов/экспертов)
        - not None -> полагаемся на фильтрацию по пользователю в микросервисе.
        """
        resp = await self._client.get(
            f"{self._base_url}/v1/object/list",
            headers=self._auth_headers(),
        )
        if resp.status_code == status.HTTP_401_UNAUTHORIZED:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unauthorized in object-equipment service",
            )
        if resp.status_code == status.HTTP_404_NOT_FOUND:
            return []
        resp.raise_for_status()
        data = resp.json()
        return [GetObject.model_validate(item) for item in data]

    async def add(self, obj: PostObject) -> None:
        """
        Создание объекта через POST /v1/object.
        """
        resp = await self._client.post(
            f"{self._base_url}/v1/object",
            json=obj.model_dump(),
            headers={**self._auth_headers(), "Content-Type": "application/json"},
        )
        if resp.status_code == status.HTTP_401_UNAUTHORIZED:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unauthorized in object-equipment service",
            )
        resp.raise_for_status()

    async def get_by_uuid(self, uuid: str) -> GetObject | None:
        try:
            resp = await self._client.get(
                f"{self._base_url}/v1/object/one/{uuid}",
                headers=self._auth_headers(),
            )
        except (httpx.ConnectError, httpx.RequestError):
            # Микросервис недоступен (хост не резолвится, таймаут и т.д.) — возвращаем None
            return None
        if resp.status_code == status.HTTP_401_UNAUTHORIZED:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unauthorized in object-equipment service",
            )
        if resp.status_code == status.HTTP_404_NOT_FOUND:
            return None
        resp.raise_for_status()
        return GetObject.model_validate(resp.json())

    async def update(self, uuid: str, entity: UpdateObject) -> None:
        resp = await self._client.put(
            f"{self._base_url}/v1/object/{uuid}",
            json=entity.model_dump(),
            headers={**self._auth_headers(), "Content-Type": "application/json"},
        )
        if resp.status_code == status.HTTP_401_UNAUTHORIZED:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unauthorized in object-equipment service",
            )
        resp.raise_for_status()

    async def delete(self, uuid_entity: str) -> None:
        resp = await self._client.delete(
            f"{self._base_url}/v1/object/{uuid_entity}",
            headers=self._auth_headers(),
        )
        if resp.status_code == status.HTTP_401_UNAUTHORIZED:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unauthorized in object-equipment service",
            )
        if resp.status_code == status.HTTP_404_NOT_FOUND:
            return
        resp.raise_for_status()

    async def get_user_by_uuid_object(self, uuid: str) -> list[str]:
        """
        Возвращает список UUID пользователей, привязанных к объекту.
        Основано на эндпоинте /v1/object/{uuid}/users.
        """
        resp = await self._client.get(
            f"{self._base_url}/v1/object/{uuid}/users",
            headers=self._auth_headers(),
        )
        if resp.status_code == status.HTTP_401_UNAUTHORIZED:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unauthorized in object-equipment service",
            )
        if resp.status_code == status.HTTP_404_NOT_FOUND:
            return []
        resp.raise_for_status()
        data = resp.json()
        # Модель UserGet находится в user-сервисе; здесь возвращаем только UUID.
        return [str(item.get("uuid")) for item in data if item.get("uuid") is not None]

    async def unique_object_to_user(self, uuid_object: str, uuid_user: str) -> bool:
        """
        Проверка, что пользователь ещё не привязан к объекту.
        Реализовано через чтение текущих пользователей объекта.
        """
        users = await self.get_user_by_uuid_object(uuid_object)
        return uuid_user not in users

    async def add_user_to_object(self, uuid_object: str, user_uuid: str) -> None:
        resp = await self._client.post(
            f"{self._base_url}/v1/object/{uuid_object}/user/{user_uuid}",
            headers=self._auth_headers(),
        )
        if resp.status_code == status.HTTP_401_UNAUTHORIZED:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unauthorized in object-equipment service",
            )
        # 200 и 201 считаем успешными (см. контракт)
        if resp.status_code not in (status.HTTP_200_OK, status.HTTP_201_CREATED):
            resp.raise_for_status()

    async def delete_user_to_object(self, uuid_object: str, uuid_user: str) -> None:
        resp = await self._client.delete(
            f"{self._base_url}/v1/object/{uuid_object}/user/{uuid_user}",
            headers=self._auth_headers(),
        )
        if resp.status_code == status.HTTP_401_UNAUTHORIZED:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unauthorized in object-equipment service",
            )
        if resp.status_code == status.HTTP_404_NOT_FOUND:
            return
        resp.raise_for_status()

    async def get_all_uuid_obj(self) -> List[Tuple[str, str]]:
        """
        Возвращает список (uuid, name) для всех объектов.
        Использует /v1/object/list.
        """
        objects = await self.get_all_object(filter_user=None)
        return [(str(obj.uuid), obj.name) for obj in objects]

    async def get_object_by_user_uuid(self, uuid_user: str) -> List[GetObject] | None:
        """
        Для конечного пользователя микросервис уже сам фильтрует объекты по пользователю
        на эндпоинте /v1/object/list, поэтому здесь просто возвращаем этот список.
        """
        objects = await self.get_all_object(filter_user=uuid_user)
        return objects or None

    async def get_object_by_uuid_equipment(self, uuid_user: str, uuid_equipment: str) -> GetObject | None:
        """
        Приближённый аналог старой логики:
        - получаем все объекты пользователя
        - для каждого объекта загружаем его оборудование и ищем uuid_equipment.
        """
        from ..models.Equipment import GetEquipment  # локальный импорт, чтобы избежать циклов

        # Получаем объекты, доступные пользователю
        objects = await self.get_object_by_user_uuid(uuid_user)
        if not objects:
            return None

        # Для каждого объекта проверяем наличие оборудования
        for obj in objects:
            resp = await self._client.get(
                f"{self._base_url}/v1/object/{obj.uuid}/equipment/list",
                headers=self._auth_headers(),
            )
            if resp.status_code == status.HTTP_401_UNAUTHORIZED:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Unauthorized in object-equipment service",
                )
            if resp.status_code == status.HTTP_404_NOT_FOUND:
                continue
            resp.raise_for_status()
            data = resp.json()
            equipment_list = [GetEquipment.model_validate(item) for item in data]
            if any(str(e.uuid) == uuid_equipment for e in equipment_list):
                return obj

        return None