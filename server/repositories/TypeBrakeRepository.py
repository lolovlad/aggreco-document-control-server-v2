from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from fastapi import Depends

from ..tables import ClassBrake, TypeBrake
from ..database import get_session


class TypeBrakeRepository:
    def __init__(self, session: AsyncSession = Depends(get_session)):
        self.__session: AsyncSession = session

    async def get_class_brake_by_name(self, name: str) -> ClassBrake | None:
        response = select(ClassBrake).where(ClassBrake.name == name)
        result = await self.__session.execute(response)
        return result.scalars().first()

    async def get_all_type_brake_by_class(self, class_name: str) -> list[TypeBrake] | None:
        response = select(TypeBrake).join(ClassBrake).where(ClassBrake.name == class_name)
        result = await self.__session.execute(response)
        return result.scalars().all()

    async def add_list_type_blake(self, list_brake: list[TypeBrake]):
        try:
            self.__session.add_all(list_brake)
            await self.__session.commit()
        except:
            await self.__session.rollback()
            raise Exception

    async def get_brakes_by_uuid_set(self, uuid_list: list[str]) -> list[TypeBrake]:
        response = select(TypeBrake).where(TypeBrake.id.in_(uuid_list))
        result = await self.__session.execute(response)
        return result.scalars().all()