from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_

from fastapi import Depends

from ..tables import *

from ..database import get_session

from datetime import datetime


class EnvRepository:
    def __init__(self, session: AsyncSession = Depends(get_session)):
        self.__session: AsyncSession = session

    async def delete_type_equipment(self, id_type_equipment: int) -> bool:
        response = (select(func.count(Equipment.id))
                    .where(Equipment.id_type == id_type_equipment))
        result = await self.__session.execute(response)
        count = result.scalars().first()
        if count > 0:
            return False
        else:
            prof = await self.__session.get(TypeEquipment, id_type_equipment)
            try:
                await self.__session.delete(prof)
                await self.__session.commit()
                return True
            except:
                await self.__session.rollback()
                return False

    async def add_type_equipment(self, type_equipment: TypeEquipment) -> TypeEquipment | None:
        try:
            self.__session.add(type_equipment)
            await self.__session.commit()
            return type_equipment
        except:
            await self.__session.rollback()
            return None

    async def get_all_type_equip(self) -> list[TypeEquipment]:
        response = select(TypeEquipment)
        result = await self.__session.execute(response)
        return result.scalars().all()

    async def add_list_type_equipment(self, type_equ: list[TypeEquipment]):
        try:
            self.__session.add_all(type_equ)
            await self.__session.commit()
        except:
            await self.__session.rollback()
            raise Exception

    async def get_all_state_object(self) -> list[StateObject]:
        response = select(StateObject)
        result = await self.__session.execute(response)
        return result.scalars().all()

    async def get_all_region(self) -> list[Region]:
        response = select(Region)
        result = await self.__session.execute(response)
        return result.scalars().all()

    async def add_list_region(self, regions: list[Region]):
        try:
            self.__session.add_all(regions)
            await self.__session.commit()
        except:
            await self.__session.rollback()
            raise Exception

    async def get_all_signs_accident(self) -> list[SignsAccident]:
        response = select(SignsAccident)
        result = await self.__session.execute(response)
        return result.scalars().all()

    async def add_list_signs_accident(self, signs_accident: list[SignsAccident]):
        try:
            self.__session.add_all(signs_accident)
            await self.__session.commit()
        except:
            await self.__session.rollback()
            raise Exception

    async def get_all_type_event(self) -> list[TypeEvent]:
        response = select(TypeEvent)
        result = await self.__session.execute(response)
        return result.scalars().all()

    async def get_all_state_event(self) -> list[StateEvent]:
        response = select(StateEvent)
        result = await self.__session.execute(response)
        return result.scalars().all()

    async def get_state_claim(self) -> list[StateClaim]:
        response = select(StateClaim)
        result = await self.__session.execute(response)
        return result.scalars().all()

    async def add(self, entity):
        try:
            self.__session.add(entity)
            await self.__session.commit()
            return entity
        except:
            await self.__session.rollback()
            return None
