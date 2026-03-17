from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_

from fastapi import Depends

from ..tables import *

from ..database import get_session

from datetime import datetime


class EnvRepository:
    def __init__(self, session: AsyncSession = Depends(get_session)):
        self.__session: AsyncSession = session

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

    async def get_all_error_code_accident(self) -> list[CodeErrorAccident]:
        response = select(CodeErrorAccident)
        result = await self.__session.execute(response)
        return result.scalars().all()

    async def add_list_error_code_accident(self, error_codes: list[CodeErrorAccident]):
        try:
            self.__session.add_all(error_codes)
            await self.__session.commit()
        except:
            await self.__session.rollback()
            # Игнорируем ошибку на уровне батч‑импорта, чтобы не ронять весь запрос
            # (например, при дубликатах или частичных проблемах данных).
            return

    async def get_error_code_accident_by_id(self, id_error: int) -> CodeErrorAccident | None:
        return await self.__session.get(CodeErrorAccident, id_error)

    async def update(self, entity):
        try:
            self.__session.add(entity)
            await self.__session.commit()
            return entity
        except:
            await self.__session.rollback()
            return None

    async def delete_error_code_accident(self, id_error: int) -> bool:
        response = select(func.count(Accident.id)).where(Accident.id_error_code_accident == id_error)
        result = await self.__session.execute(response)
        count = result.scalars().first()
        if count and count > 0:
            return False

        entity = await self.__session.get(CodeErrorAccident, id_error)
        if entity is None:
            return False
        try:
            await self.__session.delete(entity)
            await self.__session.commit()
            return True
        except:
            await self.__session.rollback()
            return False
