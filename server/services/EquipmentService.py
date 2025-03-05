from fastapi import Depends, UploadFile
from ..models.Equipment import *
from ..tables import Equipment, TypeEquipment as TypeEquipmentORM

from ..repositories import EquipmentRepository
from ..repositories.ObjectRepository import ObjectRepository


class EquipmentService:
    def __init__(self,
                 equipment_repo: EquipmentRepository = Depends(),
                 obj_repo: ObjectRepository = Depends()):
        self.__equipment_repo: EquipmentRepository = equipment_repo
        self.__obj_repo: ObjectRepository = obj_repo
        self.__count_item: int = 20

    @property
    def count_item(self) -> int:
        return self.__count_item

    @count_item.setter
    def count_item(self, item):
        self.__count_item = item

    async def get_count_page(self, uuid_object: str) -> int:
        count_row = await self.__equipment_repo.count_row(uuid_object)
        sub_page = 0
        if count_row % self.__count_item > 0:
            sub_page += 1
        return count_row // self.__count_item + sub_page

    async def get_page_equip(self, uuid_object: str, num_page: int) -> list[GetEquipment]:
        start = (num_page - 1) * self.__count_item
        end = num_page * self.__count_item
        entity = await self.__equipment_repo.get_limit_equip(uuid_object, start, end)
        equip = [GetEquipment.model_validate(entity, from_attributes=True) for entity in entity]
        return equip

    async def get_all_equip(self, uuid_object: str):
        entity = await self.__equipment_repo.get_all_equipment(uuid_object)
        equip = [GetEquipment.model_validate(entity, from_attributes=True) for entity in entity]
        return equip

    async def create_equip(self, uuid_object: str, equip_target: PostEquipment):

        obj = await self.__obj_repo.get_by_uuid(uuid_object)

        entity = Equipment(
            name=equip_target.name,
            code=equip_target.code,
            id_type=equip_target.id_type,
            id_object=obj.id,
            description=equip_target.description
        )
        try:
            await self.__equipment_repo.add(entity)
        except Exception:
            raise Exception

    async def get_one(self, uuid: str) -> GetEquipment | None:
        entity = await self.__equipment_repo.get_by_uuid(uuid)
        if entity is None:
            return entity
        return GetEquipment.model_validate(entity, from_attributes=True)

    async def update_equip(self, uuid: str, target: UpdateEquipment):
        entity = await self.__equipment_repo.get_by_uuid(uuid)

        target_dict = target.model_dump()

        for i in target_dict:
            setattr(entity, i, target_dict[i])
        try:
            await self.__equipment_repo.update(entity)
        except Exception:
            raise Exception

    async def delete_equip(self, uuid: str):
        try:
            await self.__equipment_repo.delete(uuid)
        except Exception:
            raise Exception

    async def get_equipment_by_search_field(self, uuid_object: str, search_filed: str, count: int) -> list[GetEquipment]:
        data_field = search_filed.replace(" ", "")
        equipment_entity = await self.__equipment_repo.get_equipment_by_search_field(
            uuid_object,
            data_field,
            count
        )
        equipment = [GetEquipment.model_validate(entity, from_attributes=True) for entity in equipment_entity]
        return equipment