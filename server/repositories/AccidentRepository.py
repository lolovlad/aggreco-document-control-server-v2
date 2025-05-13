from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from fastapi import Depends

from ..tables import Accident, Object, StateAccident, SignsAccident
from ..database import get_session


class AccidentRepository:
    def __init__(self, session: AsyncSession = Depends(get_session)):
        self.__session: AsyncSession = session

    async def count_row(self, uuid_object: str) -> int:
        if uuid_object is None:
            response = select(func.count(Accident.id)).where(Accident.is_delite == False)
        else:
            response = select(func.count(Accident.id)).where(Accident.is_delite == False).join(Object).where(Object.uuid == uuid_object)
        result = await self.__session.execute(response)
        return result.scalars().first()

    async def get_limit_accident(self, uuid_object: str, start: int, count: int) -> list[Accident]:
        if uuid_object is None:
            response = select(Accident).where(Accident.is_delite == False).offset(start).fetch(count).order_by(Accident.id)
        else:
            response = select(Accident).join(Object).where(Object.uuid == uuid_object).where(Accident.is_delite == False).offset(start).fetch(count).order_by(Accident.id)
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

    async def get_state_accident_by_name(self, name: str) -> StateAccident:
        response = select(StateAccident).where(Accident.is_delite == False).where(StateAccident.name == name)
        result = await self.__session.execute(response)
        return result.scalars().first()

    async def delete(self, entity: Accident):
        try:
            await self.__session.delete(entity)
            await self.__session.commit()
        except:
            await self.__session.rollback()
            raise Exception

    async def get_signs_accident_by_id_set(self, id_list: list[int]) -> list[SignsAccident]:
        response = select(SignsAccident).where(SignsAccident.id.in_(id_list))
        result = await self.__session.execute(response)
        return result.scalars().all()