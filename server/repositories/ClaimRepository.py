from datetime import datetime
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, distinct
from fastapi import Depends

from ..tables import Claim, Accident, StateClaim
from ..database import get_session


class ClaimRepository:
    """
    Репозиторий заявок, переписанный под новую архитектуру:
    - не использует таблицы object / object_to_user;
    - фильтрация по объекту идёт по UUID, хранящемуся в самой аварии;
    - доступ пользователя к объектам проверяется на уровне сервисов через ObjectRepository.
    """

    def __init__(self, session: AsyncSession = Depends(get_session)):
        self.__session: AsyncSession = session

    async def count_row(
        self,
        user_uuid: Optional[str],
        uuid_object: str,
        id_state_claim: int,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> int:
        """
        user_uuid сейчас используется только как маркер "пользователь" vs "админ".
        Фактическая фильтрация по доступным объектам выполняется в сервисе,
        поэтому здесь фильтруем только по UUID объекта (если передан не "all").
        """
        stmt = (
            select(func.count(distinct(Claim.id)))
            .join(Accident, Claim.id_accident == Accident.id)
        )

        if uuid_object != "all":
            # В миграции uuid_object хранится как UUID-колонка в accident
            stmt = stmt.where(Accident.uuid_object == uuid_object)

        if id_state_claim != 0:
            stmt = stmt.where(Claim.id_state_claim == id_state_claim)

        if date_from:
            stmt = stmt.where(Claim.datetime >= date_from)
        if date_to:
            stmt = stmt.where(Claim.datetime <= date_to)

        result = await self.__session.execute(stmt)
        return result.scalar_one_or_none() or 0

    async def get_limit_claim(
        self,
        user_uuid: str,
        uuid_object: str,
        id_state_claim: int,
        start: int,
        count: int,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> list[Claim]:
        """
        Для обычного пользователя фильтр по объектам выполняется выше (через ObjectService).
        Здесь оставляем только фильтрацию по UUID объекта и состоянию заявки.
        """
        stmt = (
            select(Claim)
            .distinct()
            .join(Accident, Claim.id_accident == Accident.id)
        )

        if uuid_object != "all":
            stmt = stmt.where(Accident.uuid_object == uuid_object)
        if id_state_claim != 0:
            stmt = stmt.where(Claim.id_state_claim == id_state_claim)

        if date_from:
            stmt = stmt.where(Claim.datetime >= date_from)
        if date_to:
            stmt = stmt.where(Claim.datetime <= date_to)

        stmt = stmt.order_by(Claim.datetime.desc()).offset(start).fetch(count)
        result = await self.__session.execute(stmt)
        return result.scalars().unique().all()

    async def get_limit_claim_admin(
        self,
        uuid_object: str,
        id_state_claim: int,
        start: int,
        count: int,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> list[Claim]:
        stmt = (
            select(Claim)
            .distinct()
            .join(Accident, Claim.id_accident == Accident.id)
            .join(StateClaim, Claim.id_state_claim == StateClaim.id)
        )

        if uuid_object != "all":
            stmt = stmt.where(Accident.uuid_object == uuid_object)
        if id_state_claim != 0:
            stmt = stmt.where(Claim.id_state_claim == id_state_claim)
        else:
            stmt = stmt.where(
                or_(
                    StateClaim.name == "accepted",
                    StateClaim.name == "under_consideration",
                )
            )

        if date_from:
            stmt = stmt.where(Claim.datetime >= date_from)
        if date_to:
            stmt = stmt.where(Claim.datetime <= date_to)

        stmt = stmt.order_by(Claim.datetime.desc()).offset(start).fetch(count)
        result = await self.__session.execute(stmt)
        return result.scalars().unique().all()

    async def get_state_claim_by_name(self, name: str) -> StateClaim:
        stmt = select(StateClaim).where(StateClaim.name == name)
        result = await self.__session.execute(stmt)
        return result.scalars().first()

    async def add(self, entity: Claim):
        try:
            self.__session.add(entity)
            await self.__session.commit()
        except Exception:
            await self.__session.rollback()
            raise

    async def get_by_uuid(self, uuid_claim: str) -> Claim | None:
        stmt = select(Claim).where(Claim.uuid == uuid_claim)
        result = await self.__session.execute(stmt)
        return result.scalars().first()

    async def update(self, entity: Claim):
        try:
            self.__session.add(entity)
            await self.__session.commit()
        except Exception:
            await self.__session.rollback()
            raise

    async def delete(self, entity: Claim):
        try:
            await self.__session.delete(entity)
            await self.__session.commit()
        except Exception:
            await self.__session.rollback()
            raise