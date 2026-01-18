from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import Depends

from ..tables import LogMessageError
from ..database import get_session


class LogMessageErrorRepository:
    def __init__(self, session: AsyncSession = Depends(get_session)):
        self.__session: AsyncSession = session

    async def get_unprocessed_logs_by_object_and_equipment(
        self, 
        id_object: int, 
        id_equipment: int | None = None
    ) -> list[LogMessageError]:
        """Получить необработанные логи для объекта и оборудования"""
        query = (
            select(LogMessageError)
            .where(LogMessageError.id_object == id_object)
            .where(LogMessageError.is_processed == False)
        )
        
        if id_equipment is not None:
            query = query.where(LogMessageError.id_equipment == id_equipment)
        
        query = query.order_by(LogMessageError.create_at)
        
        result = await self.__session.execute(query)
        return result.scalars().all()

    async def get_unprocessed_logs_by_object_and_equipment_ids(
        self, 
        id_object: int, 
        equipment_ids: list[int]
    ) -> list[LogMessageError]:
        """Получить необработанные логи для объекта и списка оборудования по id_equipment"""
        if not equipment_ids:
            return []
        
        query = (
            select(LogMessageError)
            .where(LogMessageError.id_object == id_object)
            .where(LogMessageError.is_processed == False)
            .where(LogMessageError.id_equipment.in_(equipment_ids))
            .order_by(LogMessageError.create_at)
        )
        
        result = await self.__session.execute(query)
        return result.scalars().all()

    async def mark_logs_as_processed(self, log_ids: list[int]):
        """Пометить логи как обработанные"""
        if not log_ids:
            return
        
        query = (
            select(LogMessageError)
            .where(LogMessageError.id.in_(log_ids))
        )
        result = await self.__session.execute(query)
        logs = result.scalars().all()
        
        try:
            for log in logs:
                log.is_processed = True
                self.__session.add(log)
            await self.__session.commit()
        except Exception:
            await self.__session.rollback()
            raise

    async def add(self, entity: LogMessageError):
        try:
            self.__session.add(entity)
            await self.__session.commit()
        except:
            await self.__session.rollback()
            raise Exception
