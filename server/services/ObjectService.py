from fastapi import Depends, UploadFile
from httpx import AsyncClient

from ..models.Object import (
    GetObject,
    PostObject,
    UpdateObject,
    GetObjectSettings,
    ObjectSettingsPost,
    ObjectSettingsUpdate,
    KeyIdNameMapping,
)
from ..models.User import UserGet

from ..repositories.ObjectRepository import ObjectRepository
from ..repositories import UserRepository
from ..response import get_client
from ..settings import settings
from typing import Dict


class ObjectService:
    def __init__(
        self,
        object_repo: ObjectRepository = Depends(),
        user_repo: UserRepository = Depends(),
        client: AsyncClient = Depends(get_client),
    ):
        self.__user_repo: UserRepository = user_repo
        self.__object_repo: ObjectRepository = object_repo
        self.__client: AsyncClient = client
        self.__base_url = settings.object_equipment_service_url.rstrip("/")
        self.__count_item: int = 20

    @property
    def count_item(self) -> int:
        return self.__count_item

    @count_item.setter
    def count_item(self, item):
        self.__count_item = item

    async def is_user_in_object(self, user: UserGet, uuid_object: str) -> bool:
        obj = await self.__object_repo.get_object_by_user_uuid(user.uuid)

        set_uuid = set([i.uuid for i in obj])
        if obj is None:
            return False
        return uuid_object in set_uuid

    async def is_user_in_object_by_uuid_equipment(self, user: UserGet, uuid_equipment: str) -> bool:
        obj = await self.__object_repo.get_object_by_uuid_equipment(user.uuid, uuid_equipment)
        if obj is None:
            return False
        return True

    async def get_count_page(self) -> int:
        count_row = await self.__object_repo.count_row()
        sub_page = 0
        if count_row % self.__count_item > 0:
            sub_page += 1
        return count_row // self.__count_item + sub_page

    async def get_page_object(self, num_page: int) -> list[GetObject]:
        start = (num_page - 1) * self.__count_item
        return await self.__object_repo.get_limit_object(start, self.__count_item)

    async def get_all_object(self, user: UserGet) -> list[GetObject]:
        # Для не обычных пользователей (админы/эксперты) возвращаем все объекты
        if user.type.name != "user":
            filter_user = None
        else:
            # Для обычного пользователя фильтруем по его UUID
            filter_user = str(user.uuid)

        return await self.__object_repo.get_all_object(filter_user)

    async def create_object(self, object_target: PostObject):
        try:
            await self.__object_repo.add(object_target)
        except Exception:
            raise Exception

    async def get_one(self, uuid: str) -> GetObject:
        entity = await self.__object_repo.get_by_uuid(uuid)
        if entity is None:
            return entity
        return entity

    async def update_object(self, uuid: str, target: UpdateObject):
        try:
            await self.__object_repo.update(uuid, target)
        except Exception:
            raise Exception

    async def delete_object(self, uuid: str):
        try:
            await self.__object_repo.delete(uuid)
        except Exception:
            raise Exception

    async def get_users_object(self, uuid: str) -> list[UserGet]:
        # Получаем UUID пользователей, привязанных к объекту
        user_uuids = await self.__object_repo.get_user_by_uuid_object(uuid)
        if not user_uuids:
            return []

        # Загружаем пользователей из микросервиса по их UUID
        users = await self.__user_repo.get_users_by_uuids(user_uuids)
        return users

    async def registrate_user(self, uuid_object: str, uuid_user: str) -> bool:
        is_add = await self.__object_repo.unique_object_to_user(uuid_object, uuid_user)

        if is_add:
            # Проверяем пользователя в микросервисе
            user = await self.__user_repo.get_user_by_uuid(uuid_user)
            if user is None or user.type.name != "user":
                return False

            obj = await self.__object_repo.get_by_uuid(uuid_object)
            try:
                await self.__object_repo.add_user_to_object(obj, uuid_user)
                return True
            except Exception:
                raise Exception
        return False

    async def delete_user_in_object(self, uuid_object: str, uuid_user: str):
        try:
            await self.__object_repo.delete_user_to_object(uuid_object, uuid_user)
        except Exception:
            raise Exception

    async def get_object_to_user(self, uuid_user: str) -> list[GetObject] | None:
        obj = await self.__object_repo.get_object_by_user_uuid(uuid_user)
        if obj is None:
            return obj
        return obj

    async def get_settings(self, uuid: str) -> GetObjectSettings:
        """
        Проксирующий вызов к микросервису: GET /v1/object/{uuid}/settings
        """
        resp = await self.__client.get(f"{self.__base_url}/v1/object/{uuid}/settings")
        if resp.status_code == 404:
            return GetObjectSettings()
        resp.raise_for_status()
        data = resp.json()
        return GetObjectSettings.model_validate(data)

    async def create_settings(self, uuid: str, settings_post: ObjectSettingsPost, csv_file: UploadFile) -> None:
        """
        Создает settings для объекта, проксируя запрос в микросервис:
        POST /v1/object/{uuid}/settings (multipart/form-data)
        """
        form = {
            "db_host": settings_post.db_host,
            "db_port": str(settings_post.db_port),
            "db_name": settings_post.db_name,
            "db_user": settings_post.db_user,
            "db_password": settings_post.db_password,
        }
        file_bytes = await csv_file.read()
        files = {"csv_file": (csv_file.filename or "mapping.csv", file_bytes, csv_file.content_type or "text/csv")}
        resp = await self.__client.post(
            f"{self.__base_url}/v1/object/{uuid}/settings",
            data=form,
            files=files,
        )
        await csv_file.close()
        resp.raise_for_status()

    async def update_settings(self, uuid: str, settings_update: ObjectSettingsUpdate) -> None:
        """
        Обновляет settings объекта через микросервис:
        PUT /v1/object/{uuid}/settings
        """
        payload = settings_update.model_dump(exclude_unset=True)
        resp = await self.__client.put(
            f"{self.__base_url}/v1/object/{uuid}/settings",
            json=payload,
        )
        resp.raise_for_status()
