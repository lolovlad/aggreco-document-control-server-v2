from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from fastapi import Depends

from ..tables import Event, StateEvent, TypeEvent, Accident
from ..database import get_session


class EventRepository:
    def __init__(self, session: AsyncSession = Depends(get_session)):
        self.__session: AsyncSession = session

    async def get_all_event_by_uuid_accident(self, uuid_accident: str) -> list[Event] | None:
        response = select(Event).join(Accident).where(Accident.uuid == uuid_accident).order_by(Event.date_finish)
        result = await self.__session.execute(response)
        return result.unique().scalars().all()

    async def add(self, entity: Event):
        try:
            self.__session.add(entity)
            await self.__session.commit()
        except:
            await self.__session.rollback()
            raise Exception

    async def get_by_uuid(self, uuid: str) -> Event | None:
        response = select(Event).where(Event.uuid == uuid)
        result = await self.__session.execute(response)
        return result.scalars().first()

    async def update(self, entity: Event):
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