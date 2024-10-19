from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from ..tables import User, TypeUser as TypeUserORM, Profession
from ..database import get_session

from ..models.User import UserPost, TypeUser

from fastapi import Depends


class UserRepository:
    def __init__(self, session: AsyncSession = Depends(get_session)):
        self.__session: AsyncSession = session

    async def count_row(self) -> int:
        response = select(func.count(User.id))
        result = await self.__session.execute(response)
        return result.scalars().first()

    async def get_limit_user(self, start: int, end: int) -> list[User]:
        response = select(User).offset(start).limit(end).order_by(User.id)
        result = await self.__session.execute(response)
        return result.scalars().all()

    async def get_user_by_email(self, email: str) -> User:
        response = select(User).where(User.email == email)
        result = await self.__session.execute(response)
        return result.scalars().first()

    async def get_all_type_user(self) -> list[TypeUserORM]:
        response = select(TypeUserORM)
        result = await self.__session.execute(response)
        return result.scalars().all()

    async def get_all_prof_user(self) -> list[Profession]:
        response = select(Profession)
        result = await self.__session.execute(response)
        return result.scalars().all()

    async def add(self, user: User):
        try:
            self.__session.add(user)
            await self.__session.commit()
        except:
            await self.__session.rollback()
            raise Exception

    async def add_list(self, users: list[User]):
        try:
            self.__session.add_all(users)
            await self.__session.commit()
        except:
            await self.__session.rollback()
            raise Exception

    async def add_type_user(self, type_user: TypeUserORM):
        try:
            self.__session.add(type_user)
            await self.__session.commit()
        except:
            await self.__session.rollback()
            raise Exception

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

    async def get_user_by_uuid(self, uuid: str) -> User:
        response = select(User).where(User.uuid == uuid)
        result = await self.__session.execute(response)
        return result.scalars().one()

    async def get_users_by_search_field(self,
                                        surname: str,
                                        name: str,
                                        patronymic: str,
                                        count: int) -> list[User]:
        response = select(User).where(and_(
            User.surname.ilike(f'%{surname}%'),
            User.name.ilike(f'%{name}%'),
            User.patronymic.ilike(f'%{patronymic}%')
        )).limit(count).order_by(User.id)
        result = await self.__session.execute(response)
        return result.scalars().all()

    async def update(self, user: User):
        try:
            self.__session.add(user)
            await self.__session.commit()
        except:
            await self.__session.rollback()
            raise Exception

    async def delete(self, uuid: str):
        entity = await self.get_user_by_uuid(uuid)
        entity.is_deleted = True

        await self.__session.commit()

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
