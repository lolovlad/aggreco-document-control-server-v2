from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from fastapi import Depends

from ..tables import Object, Equipment, TypeEquipment
from ..database import get_session


class EquipmentRepository:
    def __init__(self, session: AsyncSession = Depends(get_session)):
        self.__session: AsyncSession = session

    async def count_row(self, uuid_object: str) -> int:
        response = select(func.count(Equipment.id)).join(Object).where(Object.uuid == uuid_object)
        result = await self.__session.execute(response)
        return result.scalars().first()

    async def get_limit_equip(self, uuid_object: str, start: int, end: int) -> list[Equipment]:
        response = select(Equipment).join(Object).where(Object.uuid == uuid_object).offset(start).fetch(end).order_by(Equipment.id)
        result = await self.__session.execute(response)
        return result.scalars().all()

    async def get_all_type_equip(self) -> list[TypeEquipment]:
        response = select(TypeEquipment)
        result = await self.__session.execute(response)
        return result.scalars().all()

    async def add(self, entity: Equipment):
        try:
            self.__session.add(entity)
            await self.__session.commit()
        except:
            await self.__session.rollback()
            raise Exception

    async def get_by_uuid(self, uuid: str) -> Equipment | None:
        response = select(Equipment).where(Equipment.uuid == uuid)
        result = await self.__session.execute(response)
        return result.scalars().first()

    async def update(self, entity: Equipment):
        try:
            self.__session.add(entity)
            await self.__session.commit()
        except:
            await self.__session.rollback()
            raise Exception

    async def delete(self, uuid: str):
        entity = await self.get_by_uuid(uuid)
        if entity is None:
            raise Exception
        try:
            await self.__session.delete(entity)
            await self.__session.commit()
        except Exception:
            await self.__session.rollback()

    async def add_list_type_equipment(self, type_equ: list[TypeEquipment]):
        try:
            self.__session.add_all(type_equ)
            await self.__session.commit()
        except:
            await self.__session.rollback()
            raise Exception

    async def get_all_equipment(self, uuid_object: str) -> list[Equipment]:
        response = select(Equipment).join(Object).where(Object.uuid == uuid_object).order_by(
            Equipment.id)
        result = await self.__session.execute(response)
        return result.scalars().all()

    async def get_equipment_by_uuid_set(self, uuid_list: list[str]) -> list[Equipment]:
        response = select(Equipment).where(Equipment.uuid.in_(uuid_list))
        result = await self.__session.execute(response)
        return result.scalars().all()

    async def get_equipment_by_search_field(self, uuid_object: str, name_equipment: str, count: int) -> list[Equipment]:
        response = (select(Equipment)
                    .join(Object).where(Object.uuid == uuid_object)
                    .where(Equipment.name.ilike(f'%{name_equipment}%')).
                    limit(count).
                    order_by(Equipment.id))
        result = await self.__session.execute(response)
        return result.scalars().all()