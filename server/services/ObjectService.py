from fastapi import Depends
from ..models.Object import *
from ..models.User import UserGet
from ..tables import Object, StateObject as StateObjectORM, Equipment, TypeEquipment

from ..repositories.ObjectRepository import ObjectRepository
from ..repositories import UserRepository


class ObjectService:
    def __init__(self,
                 object_repo: ObjectRepository = Depends(),
                 user_repo: UserRepository = Depends()
                 ):
        self.__user_repo: UserRepository = user_repo
        self.__object_repo: ObjectRepository = object_repo
        self.__count_item: int = 20

    @property
    def count_item(self) -> int:
        return self.__count_item

    @count_item.setter
    def count_item(self, item):
        self.__count_item = item

    async def get_count_page(self) -> int:
        count_row = await self.__object_repo.count_row()
        sub_page = 0
        if count_row % self.__count_item > 0:
            sub_page += 1
        return count_row // self.__count_item + sub_page

    async def get_page_object(self, num_page: int) -> list[GetObject]:
        start = (num_page - 1) * self.__count_item
        end = num_page * self.__count_item
        entity = await self.__object_repo.get_limit_object(start, end)
        objects = [GetObject.model_validate(entity, from_attributes=True) for entity in entity]
        return objects

    async def get_all_object(self, user: UserGet) -> list[GetObject]:
        if user.type.name == "admin":
            filter_user = 0
        else:
            user = await self.__user_repo.get_user_by_uuid(user.uuid)
            filter_user = user.id

        entity = await self.__object_repo.get_all_object(filter_user)
        objects = [GetObject.model_validate(entity, from_attributes=True) for entity in entity]
        return objects

    async def get_all_state_object(self) -> list[StateObject]:
        entity = await self.__object_repo.get_all_state_object()
        return [StateObject.model_validate(i, from_attributes=True) for i in entity]

    async def create_object(self, object_target: PostObject):
        entity = Object(
            name=object_target.name,
            address=object_target.address,
            cx=object_target.cx,
            cy=object_target.cy,
            description=object_target.description,
            counterparty=object_target.counterparty,
            id_state=object_target.id_state,
        )
        try:
            await self.__object_repo.add(entity)
        except Exception:
            raise Exception

    async def get_one(self, uuid: str) -> GetObject:
        entity = await self.__object_repo.get_by_uuid(uuid)
        if entity is None:
            return entity
        return GetObject.model_validate(entity, from_attributes=True)

    async def update_object(self, uuid: str, target: UpdateObject):
        entity = await self.__object_repo.get_by_uuid(uuid)

        target_dict = target.model_dump()

        for i in target_dict:
            setattr(entity, i, target_dict[i])
        try:
            await self.__object_repo.update(entity)
        except Exception:
            raise Exception

    async def delete_object(self, uuid: str):
        entity = await self.__object_repo.get_by_uuid(uuid)
        entity.is_deleted = True
        try:
            await self.__object_repo.update(entity)
        except Exception:
            raise Exception

    async def get_users_object(self, uuid: str) -> list[UserGet]:
        entity = await self.__object_repo.get_user_by_uuid_object(uuid)
        users = [UserGet.model_validate(entity, from_attributes=True) for entity in entity]
        return users

    async def registrate_user(self, uuid_object: str, uuid_user: str) -> bool:
        is_add = await self.__object_repo.unique_object_to_user(uuid_object, uuid_user)
        if is_add:
            user = await self.__user_repo.get_user_by_uuid(uuid_user)
            obj = await self.__object_repo.get_by_uuid(uuid_object)
            try:
                await self.__object_repo.add_user_to_object(obj, user)
                return True
            except Exception:
                raise Exception
        return False

    async def delete_user_in_object(self, uuid_object: str, uuid_user: str):
        try:
            await self.__object_repo.delete_user_to_object(uuid_object, uuid_user)
        except Exception:
            raise Exception
