from fastapi import Depends
from ..models.Equipment import GetEquipment, PostEquipment, UpdateEquipment

from ..repositories import EquipmentRepository


class EquipmentService:
    def __init__(self, equipment_repo: EquipmentRepository = Depends()):
        self.__equipment_repo: EquipmentRepository = equipment_repo
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
        return await self.__equipment_repo.get_limit_equip(uuid_object, start, self.__count_item)

    async def get_all_equip(self, uuid_object: str):
        return await self.__equipment_repo.get_all_equipment(uuid_object)

    async def create_equip(self, uuid_object: str, equip_target: PostEquipment):
        try:
            await self.__equipment_repo.add(uuid_object, equip_target)
        except Exception:
            raise Exception

    async def get_one(self, uuid: str) -> GetEquipment | None:
        entity = await self.__equipment_repo.get_by_uuid(uuid)
        if entity is None:
            return entity
        return entity

    async def update_equip(self, uuid: str, target: UpdateEquipment):
        try:
            await self.__equipment_repo.update(uuid, target)
        except Exception:
            raise Exception

    async def delete_equip(self, uuid: str):
        try:
            await self.__equipment_repo.delete(uuid)
        except Exception:
            raise Exception

    async def get_equipment_by_search_field(self, uuid_object: str, search_filed: str) -> list[GetEquipment]:
        data_field = search_filed.replace(" ", "")
        equipment = await self.__equipment_repo.get_equipment_by_search_field(
            uuid_object,
            data_field
        )
        return equipment