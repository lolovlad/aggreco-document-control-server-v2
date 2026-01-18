from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, and_, func, extract
from fastapi import Depends
from datetime import datetime, timedelta
from typing import Optional

from ..tables import Summarize
from ..database import get_session


class SummarizeRepository:
    def __init__(self, session: AsyncSession = Depends(get_session)):
        self.__session: AsyncSession = session

    async def get_by_object_and_equipment_and_month(
        self, 
        id_object: int, 
        id_equipment: int
    ) -> Summarize | None:
        """Получить Summarize для объекта и оборудования для текущего месяца"""
        now = datetime.now()
        current_year = now.year
        current_month = now.month
        
        query = (
            select(Summarize)
            .where(Summarize.id_object == id_object)
            .where(Summarize.id_equipment == id_equipment)
            .where(extract('year', Summarize.datetime_start) == current_year)
            .where(extract('month', Summarize.datetime_start) == current_month)
            .order_by(Summarize.datetime_start.desc())
            .limit(1)
        )
        result = await self.__session.execute(query)
        return result.scalars().first()

    async def get_by_object(
        self,
        id_object: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> list[Summarize]:
        """Получить все Summarize для объекта с фильтрацией по датам"""
        conditions = [Summarize.id_object == id_object]
        
        if start_date is not None:
            conditions.append(Summarize.datetime_start >= start_date)
        if end_date is not None:
            # Используем конец дня для включения всей конечной даты
            if isinstance(end_date, datetime):
                end_date_with_time = datetime.combine(end_date.date(), datetime.max.time().replace(microsecond=999999))
            else:
                end_date_with_time = datetime.combine(end_date, datetime.max.time().replace(microsecond=999999))
            conditions.append(Summarize.datetime_start <= end_date_with_time)
        
        query = (
            select(Summarize)
            .where(and_(*conditions))
            .order_by(Summarize.datetime_start.desc())
        )
        result = await self.__session.execute(query)
        return result.scalars().all()

    async def get_by_object_and_equipment(
        self,
        id_object: int,
        id_equipment: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> list[Summarize]:
        """Получить все Summarize для объекта и оборудования с фильтрацией по датам"""
        conditions = [
            Summarize.id_object == id_object,
            Summarize.id_equipment == id_equipment
        ]
        
        if start_date is not None:
            conditions.append(Summarize.datetime_start >= start_date)
        if end_date is not None:
            # Используем конец дня для включения всей конечной даты
            if isinstance(end_date, datetime):
                end_date_with_time = datetime.combine(end_date.date(), datetime.max.time().replace(microsecond=999999))
            else:
                end_date_with_time = datetime.combine(end_date, datetime.max.time().replace(microsecond=999999))
            conditions.append(Summarize.datetime_start <= end_date_with_time)
        
        query = (
            select(Summarize)
            .where(and_(*conditions))
            .order_by(Summarize.datetime_start.desc())
        )
        result = await self.__session.execute(query)
        return result.scalars().all()

    async def add(self, entity: Summarize):
        try:
            self.__session.add(entity)
            await self.__session.commit()
        except:
            await self.__session.rollback()
            raise Exception

    async def update(self, entity: Summarize):
        try:
            self.__session.add(entity)
            await self.__session.commit()
        except:
            await self.__session.rollback()
            raise Exception
