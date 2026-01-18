from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_

from fastapi import Depends

from ..tables import Object, Equipment, TypeEquipment
from ..database import get_session


class EquipmentRepository:
    def __init__(self, session: AsyncSession = Depends(get_session)):
        self.__session: AsyncSession = session

    async def count_row(self, uuid_object: str) -> int:
        response = (select(func.count(Equipment.id))
                    .join(Object)
                    .where(Object.uuid == uuid_object)
                    .where(Equipment.is_delite == False))
        result = await self.__session.execute(response)
        return result.scalars().first()

    async def get_limit_equip(self, uuid_object: str, start: int, count: int) -> list[Equipment]:
        response = (select(Equipment)
                    .join(Object)
                    .where(Object.uuid == uuid_object)
                    .where(Equipment.is_delite == False)
                    .offset(start)
                    .fetch(count)
                    .order_by(Equipment.id))
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
        response = select(Equipment).where(Equipment.uuid == uuid).where(Equipment.is_delite == False)
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
            entity.is_delite = True
            self.__session.add(entity)
            await self.__session.commit()
        except Exception:
            await self.__session.rollback()

    async def get_all_equipment(self, uuid_object: str) -> list[Equipment]:
        response = select(Equipment).join(Object).where(Object.uuid == uuid_object).where(Equipment.is_delite == False).order_by(
            Equipment.id)
        result = await self.__session.execute(response)
        return result.scalars().all()

    async def get_equipment_by_uuid_set(self, uuid_list: list[str]) -> list[Equipment]:
        response = select(Equipment).where(Equipment.uuid.in_(uuid_list)).where(Equipment.is_delite == False)
        result = await self.__session.execute(response)
        return result.scalars().all()

    async def get_equipment_by_search_field(self, uuid_object: str, name_equipment: str) -> list[Equipment]:
        response = (select(Equipment)
                    .join(Object).where(Object.uuid == uuid_object)
                    .where(or_(Equipment.name.ilike(f'%{name_equipment}%'),
                               Equipment.code.ilike(f'%{name_equipment}%')))
                    .where(Equipment.is_delite == False)
                    .order_by(Equipment.id))
        result = await self.__session.execute(response)
        return result.scalars().all()

    async def get_by_uuid_object_ande_equipment(self, uuid_object: str, uuid_equipment: str) -> list[Equipment]:
        response = (select(Equipment)
                    .join(Object, Equipment.id_object == Object.id)
                    .where(Equipment.uuid == uuid_equipment)
                    .where(Equipment.is_delite == False)
                    .where(Object.uuid == uuid_object))
        result = await self.__session.execute(response)
        return result.scalars().all()

    async def find_equipment_by_name_parts(self, object_id: int, name_parts: list[str]) -> Equipment | None:
        """
        Ищет equipment по частям имени (для вложенных имен типа "СУЭС.Секция_1")
        Использует оптимизированный запрос с поиском по всем частям имени
        """
        if not name_parts:
            return None
        
        # Создаем условия для поиска: equipment.name должен содержать все части
        conditions = []
        for part in name_parts:
            if part.strip():  # Пропускаем пустые части
                conditions.append(Equipment.name.ilike(f'%{part.strip()}%'))
        
        if not conditions:
            return None
        
        # Используем AND для всех условий - имя должно содержать все части
        from sqlalchemy import and_
        response = (select(Equipment)
                    .where(Equipment.id_object == object_id)
                    .where(Equipment.is_delite == False)
                    .where(and_(*conditions))
                    .order_by(Equipment.id)
                    .limit(1))
        result = await self.__session.execute(response)
        return result.scalars().first()

    async def get_equipment_by_ids(self, equipment_ids: list[int]) -> list[Equipment]:
        """
        Оптимизированный SQL запрос для получения нескольких equipment по числовым id
        Использует IN для эффективного получения всех записей одним запросом
        """
        if not equipment_ids:
            return []
        response = (select(Equipment)
                    .where(Equipment.id.in_(equipment_ids))
                    .where(Equipment.is_delite == False))
        result = await self.__session.execute(response)
        return result.scalars().all()