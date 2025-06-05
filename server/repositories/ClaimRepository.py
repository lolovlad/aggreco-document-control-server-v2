from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_

from fastapi import Depends

from ..tables import Claim, Accident, Object, ObjectToUser, StateClaim
from ..database import get_session

from datetime import datetime


class ClaimRepository:
    def __init__(self, session: AsyncSession = Depends(get_session)):
        self.__session: AsyncSession = session

    async def count_row(self, id_user: int | None,
                        uuid_object: str,
                        id_state_claim: int) -> int:
        response = (select(func.count(Claim.id))
                    .join(Accident, Claim.id_accident == Accident.id)
                    .join(Object, Accident.id_object == Object.id)
                    .join(ObjectToUser, ObjectToUser.id_object == Object.id))
        if id_user is not None:
            response = response.where(ObjectToUser.id_user == id_user)
        if uuid_object != "all":
            response = response.where(Object.uuid == uuid_object)
        if id_state_claim != 0:
            response = response.where(Claim.id_state_claim == id_state_claim)
        result = await self.__session.execute(response)
        return result.scalars().first()

    async def get_limit_claim(self,
                              id_user: int,
                              uuid_object: str,
                              id_state_claim: int,
                              start: int,
                              count: int) -> list[Claim]:
        response = (select(Claim)
                    .join(Accident, Claim.id_accident == Accident.id)
                    .join(Object, Accident.id_object == Object.id)
                    .join(ObjectToUser, ObjectToUser.id_object == Object.id)
                    .where(ObjectToUser.id_user == id_user))
        if uuid_object != "all":
            response = response.where(Object.uuid == uuid_object)
        if id_state_claim != 0:
            response = response.where(Claim.id_state_claim == id_state_claim)
        response = response.offset(start).fetch(count).order_by(Claim.id)

        result = await self.__session.execute(response)
        return result.scalars().unique().all()

    async def get_limit_claim_admin(self,
                                    uuid_object: str,
                                    id_state_claim: int,
                                    start: int,
                                    count: int) -> list[Claim]:
        response = (select(Claim)
                    .join(Accident, Claim.id_accident == Accident.id)
                    .join(StateClaim, Claim.id_state_claim == StateClaim.id)
                    .join(Object, Accident.id_object == Object.id)
                    .join(ObjectToUser, ObjectToUser.id_object == Object.id))
        if uuid_object != "all":
            response = response.where(Object.uuid == uuid_object)
        if id_state_claim != 0:
            response = response.where(Claim.id_state_claim == id_state_claim)
        else:
            response = response.where(or_(StateClaim.name == "accepted", StateClaim.name == "under_consideration"))
        response = response.offset(start).fetch(count).order_by(Claim.id)

        result = await self.__session.execute(response)
        return result.scalars().unique().all()

    async def get_state_claim_by_name(self, name: str) -> StateClaim:
        response = select(StateClaim).where(StateClaim.name == name)
        result = await self.__session.execute(response)
        return result.scalars().first()

    async def add(self, entity: Claim):
        try:
            self.__session.add(entity)
            await self.__session.commit()
        except:
            await self.__session.rollback()
            raise Exception

    async def get_by_uuid(self, uuid_claim: str) -> Claim | None:
        response = select(Claim).where(Claim.uuid == uuid_claim)
        result = await self.__session.execute(response)
        return result.scalars().first()

    async def update(self, entity: Object):
        try:
            self.__session.add(entity)
            await self.__session.commit()
        except:
            await self.__session.rollback()
            raise Exception

    async def delete(self, entity: Claim):
        try:
            await self.__session.delete(entity)
            await self.__session.commit()
        except:
            await self.__session.rollback()
            raise Exception