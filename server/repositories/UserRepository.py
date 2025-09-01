from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from ..tables import User, TypeUser as TypeUserORM, Profession
from ..database import get_session

from fastapi import Depends


class UserRepository:
    def __init__(self, session: AsyncSession = Depends(get_session)):
        self.__session: AsyncSession = session

    async def count_row(self) -> int:
        response = select(func.count(User.id))
        result = await self.__session.execute(response)
        return result.scalars().first()

    async def get_limit_user(self, start: int, count: int) -> list[User]:
        response = select(User).offset(start).fetch(count).order_by(User.id)
        result = await self.__session.execute(response)
        return result.scalars().all()

    async def get_user_by_email(self, email: str) -> User:
        response = select(User).where(User.email == email)
        result = await self.__session.execute(response)
        return result.scalars().first()

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

    async def get_user_by_uuid(self, uuid: str) -> User:
        response = select(User).where(User.uuid == uuid)
        result = await self.__session.execute(response)
        return result.scalars().one()

    async def get_users_by_search_field(self,
                                        surname: str,
                                        name: str,
                                        patronymic: str) -> list[User]:
        response = select(User).where(and_(
            User.surname.ilike(f'%{surname}%'),
            User.name.ilike(f'%{name}%'),
            User.patronymic.ilike(f'%{patronymic}%')
        )).order_by(User.id)
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

    async def get_user_by_access_email(self, email: str) -> User:
        response = select(User).where(User.email == email).where(User.is_deleted == False)
        result = await self.__session.execute(response)

    async def get_users_by_context_email(self, context: str) -> list[User]:
        stmt = select(User).where(User.email_send_info[context].astext == 'true')
        result = await self.__session.execute(stmt)
        return result.scalars().all()
