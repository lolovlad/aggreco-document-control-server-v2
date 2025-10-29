from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, distinct

from fastapi import Depends

from ..tables import TechnicalProposals, User, StateClaim, Object
from ..database import get_session

from datetime import datetime


class ProposalsRepository:
    def __init__(self, session: AsyncSession = Depends(get_session)):
        self.__session: AsyncSession = session

    async def count_row(self,
                        uuid_user: str | None,
                        uuid_object: str,
                        id_state_claim: int) -> int:
        response = (select(func.count(distinct(TechnicalProposals.id)))
                    .join(User, TechnicalProposals.id_user == User.id)
                    .join(Object, TechnicalProposals.id_object == Object.id))
        if uuid_user is not None:
            response = response.where(User.uuid == uuid_user)
        if uuid_object != "all":
            response = response.where(Object.uuid == uuid_object)
        if id_state_claim != 0:
            response = response.where(TechnicalProposals.id_state_claim == id_state_claim)

        result = await self.__session.execute(response)
        return result.scalars().first()

    async def get_limit(self,
                        uuid_user: str,
                        uuid_object: str,
                        id_state_claim: int,
                        start: int,
                        count: int) -> list[TechnicalProposals]:
        response = (select(TechnicalProposals).distinct()
                    .join(User, User.id == TechnicalProposals.id_user)
                    .join(Object, TechnicalProposals.id_object == Object.id)
                    .where(User.uuid == uuid_user))

        if uuid_object != "all":
            response = response.where(Object.uuid == uuid_object)
        if id_state_claim != 0:
            response = response.where(TechnicalProposals.id_state_claim == id_state_claim)

        response = response.order_by(TechnicalProposals.id.desc()).offset(start).fetch(count)
        result = await self.__session.execute(response)
        return result.scalars().unique().all()

    async def get_limit_admin(self,
                              uuid_object: str,
                              start: int,
                              count: int) -> list[TechnicalProposals]:
        response = (select(TechnicalProposals).distinct()
                    .join(User, TechnicalProposals.id_user == User.id)
                    .join(StateClaim, TechnicalProposals.id_state_claim == StateClaim.id)
                    .join(Object, TechnicalProposals.id_object == Object.id))
        if uuid_object != "all":
            response = response.where(Object.uuid == uuid_object)

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
