from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from fastapi import Depends

from ..tables import Accident, Object
from ..database import get_session


class AccidentRepository:
    def __init__(self, session: AsyncSession = Depends(get_session)):
        self.__session: AsyncSession = session

    async def count_row(self, uuid_object: str) -> int:
        if uuid_object is None:
            response = select(func.count(Accident.id))
        else:
            response = select(func.count(Accident.id)).join(Object).where(Object.uuid == uuid_object)
        result = await self.__session.execute(response)
        return result.scalars().first()

    async def get_limit_accident(self, uuid_object: str, start: int, end: int) -> list[Accident]:
        if uuid_object is None:
            response = select(Accident).offset(start).fetch(end).order_by(Accident.id)
        else:
            response = select(Accident).join(Object).where(Object.uuid == uuid_object).offset(start).fetch(end).order_by(Accident.id)
        result = await self.__session.execute(response)
        return result.scalars().unique().all()

    async def add(self, entity: Accident):
        try:
            self.__session.add(entity)
            await self.__session.commit()
        except:
            await self.__session.rollback()
            raise Exception

    async def get_by_uuid(self, uuid_accident: str) -> Accident | None:
        response = select(Accident).where(Accident.uuid == uuid_accident)
        result = await self.__session.execute(response)
        return result.scalars().first()

    async def update(self, entity: Accident):
        try:
            self.__session.add(entity)
            await self.__session.commit()
        except:
            await self.__session.rollback()
            raise Exception