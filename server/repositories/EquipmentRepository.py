from typing import List

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from httpx import AsyncClient

from ..models.Equipment import GetEquipment, PostEquipment, UpdateEquipment
from ..response import get_client
from ..settings import settings


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/users/v1/login/sign-in/",
)


class EquipmentRepository:
    """
    Репозиторий-адаптер к микросервису Object & Equipment.
    Полностью заменяет прямую работу с локальными таблицами Equipment.
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

    async def count_row(self, uuid_object: str) -> int:
        """
        Количество оборудования по объекту.
        Используем пагинационный эндпоинт и суммарное количество элементов.
        """
        resp = await self._client.get(
            f"{self._base_url}/v1/object/{uuid_object}/equipment/page",
            params={"page": 1, "per_item_page": 1},
            headers=self._auth_headers(),
        )
        if resp.status_code == status.HTTP_401_UNAUTHORIZED:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unauthorized in object-equipment service",
            )
        if resp.status_code == status.HTTP_404_NOT_FOUND:
            return 0
        resp.raise_for_status()
        # Интерпретируем заголовки:
        # X-Count-Page - количество страниц
        # X-Count-Item - количество элементов на странице
        try:
            pages = int(resp.headers.get("X-Count-Page", "1"))
            per_page = int(resp.headers.get("X-Count-Item", "0"))
            return pages * per_page
        except ValueError:
            data = resp.json()
            return len(data)

    async def get_limit_equip(self, uuid_object: str, start: int, count: int) -> List[GetEquipment]:
        """
        Пагинация оборудования объекта на основе /v1/object/{uuid}/equipment/page.
        """
        page = start // count + 1
        resp = await self._client.get(
            f"{self._base_url}/v1/object/{uuid_object}/equipment/page",
            params={"page": page, "per_item_page": count},
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
        return [GetEquipment.model_validate(item) for item in data]

    async def add(self, uuid_object: str, entity: PostEquipment) -> None:
        """
        Добавление оборудования к объекту через POST /v1/object/{uuid}/equipment.
        """
        resp = await self._client.post(
            f"{self._base_url}/v1/object/{uuid_object}/equipment",
            json=entity.model_dump(),
            headers={**self._auth_headers(), "Content-Type": "application/json"},
        )
        if resp.status_code == status.HTTP_401_UNAUTHORIZED:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unauthorized in object-equipment service",
            )
        resp.raise_for_status()

    async def get_by_uuid(self, uuid: str) -> GetEquipment | None:
        resp = await self._client.get(
            f"{self._base_url}/v1/equipment/{uuid}",
            headers=self._auth_headers(),
        )
        if resp.status_code == status.HTTP_401_UNAUTHORIZED:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unauthorized in object-equipment service",
            )
        if resp.status_code == status.HTTP_404_NOT_FOUND:
            return None
        resp.raise_for_status()
        return GetEquipment.model_validate(resp.json())

    async def update(self, uuid: str, entity: UpdateEquipment) -> None:
        resp = await self._client.put(
            f"{self._base_url}/v1/equipment/{uuid}",
            json=entity.model_dump(),
            headers={**self._auth_headers(), "Content-Type": "application/json"},
        )
        if resp.status_code == status.HTTP_401_UNAUTHORIZED:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unauthorized in object-equipment service",
            )
        resp.raise_for_status()

    async def delete(self, uuid: str) -> None:
        resp = await self._client.delete(
            f"{self._base_url}/v1/equipment/{uuid}",
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

    async def get_all_equipment(self, uuid_object: str) -> List[GetEquipment]:
        resp = await self._client.get(
            f"{self._base_url}/v1/object/{uuid_object}/equipment/list",
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
        return [GetEquipment.model_validate(item) for item in data]

    async def get_equipment_by_uuid_set(self, uuid_list: list[str]) -> List[GetEquipment]:
        if not uuid_list:
            return []
        try:
            resp = await self._client.post(
                f"{self._base_url}/v1/equipment/batch",
                json=uuid_list,
                headers={**self._auth_headers(), "Content-Type": "application/json"},
            )
        except (httpx.ConnectError, httpx.RequestError):
            # Микросервис недоступен — возвращаем пустой список
            return []
        if resp.status_code == status.HTTP_401_UNAUTHORIZED:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unauthorized in object-equipment service",
            )
        if resp.status_code == status.HTTP_404_NOT_FOUND:
            return []
        resp.raise_for_status()
        data = resp.json()
        return [GetEquipment.model_validate(item) for item in data]

    async def get_equipment_by_search_field(self, uuid_object: str, name_equipment: str) -> List[GetEquipment]:
        resp = await self._client.get(
            f"{self._base_url}/v1/object/{uuid_object}/equipment/search",
            params={"search_field": name_equipment},
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
        return [GetEquipment.model_validate(item) for item in data]

    async def get_by_uuid_object_ande_equipment(self, uuid_object: str, uuid_equipment: str) -> List[GetEquipment]:
        """
        Возвращает оборудование по uuid объекта и uuid оборудования.
        Использует список оборудования объекта и фильтрует по uuid_equipment.
        """
        equipment_list = await self.get_all_equipment(uuid_object)
        return [e for e in equipment_list if str(e.uuid) == uuid_equipment]

    async def find_equipment_by_name_parts(self, object_uuid: str, name_parts: list[str]) -> GetEquipment | None:
        """
        Поиск оборудования по частям имени через search-эндпоинт.
        """
        if not name_parts:
            return None

        # Используем полное имя как join по точке (как было раньше в CSV)
        search_query = ".".join([p.strip() for p in name_parts if p.strip()])
        if not search_query:
            return None

        result = await self.get_equipment_by_search_field(object_uuid, search_query)
        return result[0] if result else None

    #async def get_equipment_by_ids(self, equipment_ids: list[int]) -> List[GetEquipment]:
    #    """
    #    Раньше метод работал по внутренним числовым id.
    #    Теперь основная логика Summarize/LogAnalysis должна оперировать UUID,
    #    поэтому здесь оставляем заглушку, чтобы не ломать интерфейс.
    #    """
    #
    #    # метод можно будет удалить или переписать на работу с UUID.
    #    return []