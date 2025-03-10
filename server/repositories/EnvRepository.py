from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_

from fastapi import Depends

from ..tables import (TypeUser,
                      Profession,
                      TypeEquipment,
                      StateObject,
                      Region,
                      ClassBrake,
                      SignsAccident,
                      FileDocument,
                      User,
                      TypeEvent,
                      StateEvent,
                      StateClaim)

from ..database import get_session

from datetime import datetime


class EnvRepository:
    def __init__(self, session: AsyncSession = Depends(get_session)):
        self.__session: AsyncSession = session

    async def get_all_type_user(self) -> list[TypeUser]:
        response = select(TypeUser)
        result = await self.__session.execute(response)
        return result.scalars().all()

    async def delete_prof(self, id_prof: int) -> bool:
        response = select(func.count(User.id)).where(User.id_profession == id_prof)
        result = await self.__session.execute(response)
        count = result.scalars().first()
        if count > 0:
            return False
        else:
            prof = await self.__session.get(Profession, id_prof)
            try:
                await self.__session.delete(prof)
                await self.__session.commit()
                return True
            except:
                await self.__session.rollback()
                return False

    async def add_list_prof_user(self, prof_users: list[Profession]):
        try:
            self.__session.add_all(prof_users)
            await self.__session.commit()
        except:
            await self.__session.rollback()
            raise Exception

    async def add_prof_user(self, prof: Profession) -> Profession:
        try:
            self.__session.add(prof)
            await self.__session.commit()
            return prof
        except:
            await self.__session.rollback()
            return None

    async def get_prof_by_name(self, prof_name: str) -> Profession | None:
        response = select(Profession).where(Profession.name == prof_name)
        result = await self.__session.execute(response)
        return result.scalars().one()

    async def get_all_prof_user(self) -> list[Profession]:
        response = select(Profession)
        result = await self.__session.execute(response)
        return result.scalars().all()

    async def get_all_type_equip(self) -> list[TypeEquipment]:
        response = select(TypeEquipment)
        result = await self.__session.execute(response)
        return result.scalars().all()

    async def add_list_type_equipment(self, type_equ: list[TypeEquipment]):
        try:
            self.__session.add_all(type_equ)
            await self.__session.commit()
        except:
            await self.__session.rollback()
            raise Exception

    async def get_all_state_object(self) -> list[StateObject]:
        response = select(StateObject)
        result = await self.__session.execute(response)
        return result.scalars().all()

    async def get_all_region(self) -> list[Region]:
        response = select(Region)
        result = await self.__session.execute(response)
        return result.scalars().all()

    async def add_list_region(self, regions: list[Region]):
        try:
            self.__session.add_all(regions)
            await self.__session.commit()
        except:
            await self.__session.rollback()
            raise Exception

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