from datetime import datetime

from fastapi import Depends
from sqlalchemy import select, func, distinct
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_session
from ..tables import TechnicalProposals, StateClaim


class ProposalsRepository:
    """
    Репозиторий технических предложений.
    Фильтрация по объекту идёт по полю uuid_object (UUID из микросервиса), без JOIN к таблице object.
    """

    def __init__(self, session: AsyncSession = Depends(get_session)):
        self.__session: AsyncSession = session

    async def count_row(
        self,
        uuid_user: str | None,
        uuid_object: str,
        id_state_claim: int,
    ) -> int:
        response = select(func.count(distinct(TechnicalProposals.id)))
        if uuid_user is not None:
            response = response.where(TechnicalProposals.user_uuid == uuid_user)
        if uuid_object != "all":
            response = response.where(TechnicalProposals.uuid_object == uuid_object)
        if id_state_claim != 0:
            response = response.where(TechnicalProposals.id_state_claim == id_state_claim)

        result = await self.__session.execute(response)
        return result.scalar_one_or_none() or 0

    async def get_limit(
        self,
        uuid_user: str,
        uuid_object: str,
        id_state_claim: int,
        start: int,
        count: int,
    ) -> list[TechnicalProposals]:
        response = (
            select(TechnicalProposals)
            .distinct()
            .where(TechnicalProposals.user_uuid == uuid_user)
        )
        if uuid_object != "all":
            response = response.where(TechnicalProposals.uuid_object == uuid_object)
        if id_state_claim != 0:
            response = response.where(TechnicalProposals.id_state_claim == id_state_claim)

        response = response.order_by(TechnicalProposals.id.desc()).offset(start).fetch(count)
        result = await self.__session.execute(response)
        return result.scalars().unique().all()

    async def get_limit_admin(
        self,
        uuid_object: str,
        start: int,
        count: int,
    ) -> list[TechnicalProposals]:
        response = (
            select(TechnicalProposals)
            .distinct()
            .join(StateClaim, TechnicalProposals.id_state_claim == StateClaim.id)
        )
        if uuid_object != "all":
            response = response.where(TechnicalProposals.uuid_object == uuid_object)

        response = response.order_by(TechnicalProposals.id.desc()).offset(start).fetch(count)
        result = await self.__session.execute(response)
        return result.scalars().unique().all()

    async def add(self, entity: TechnicalProposals):
        try:
            self.__session.add(entity)
            await self.__session.commit()
        except:
            await self.__session.rollback()
            raise Exception

    async def get_by_uuid(self, uuid_entity: str) -> TechnicalProposals | None:
        response = select(TechnicalProposals).where(TechnicalProposals.uuid == uuid_entity)
        result = await self.__session.execute(response)
        return result.scalars().first()

    async def delete(self, entity: TechnicalProposals):
        try:
            await self.__session.delete(entity)
            await self.__session.commit()
        except:
            await self.__session.rollback()
            raise Exception
