from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from fastapi import Depends

from ..tables import Object, StateObject, User, ObjectToUser, Equipment
from ..database import get_session


class ObjectRepository:
    def __init__(self, session: AsyncSession = Depends(get_session)):
        self.__session: AsyncSession = session

    async def count_row(self) -> int:
        response = select(func.count(Object.id))
        result = await self.__session.execute(response)
        return result.scalars().first()

    async def get_limit_object(self, start: int, end: int) -> list[Object]:
        response = select(Object).where(Object.is_deleted == False).offset(start).fetch(end).order_by(Object.id)
        result = await self.__session.execute(response)
        return result.scalars().all()

    async def get_all_object(self, filter_user: int) -> list[Object]:
        if filter_user == 0:
            response = select(Object).where(Object.is_deleted == False).order_by(Object.id)
        else:
            response = (select(Object)
                        .join(ObjectToUser)
                        .where(Object.is_deleted == False)
                        .where(ObjectToUser.id_user == filter_user))
        result = await self.__session.execute(response)
        return result.unique().scalars().all()

    async def get_all_state_object(self) -> list[StateObject]:
        response = select(StateObject)
        result = await self.__session.execute(response)
        return result.scalars().all()

    async def add(self, object: Object):
        try:
            self.__session.add(object)
            await self.__session.commit()
        except:
            await self.__session.rollback()
            raise Exception

    async def get_by_uuid(self, uuid: str) -> Object | None:
        response = select(Object).where(Object.uuid == uuid)
        result = await self.__session.execute(response)
        return result.scalars().first()

    async def update(self, entity: Object):
        try:
            self.__session.add(entity)
            await self.__session.commit()
        except:
            await self.__session.rollback()
            raise Exception

    async def delete(self, uuid_entity: str):
        obj = await self.get_by_uuid(uuid_entity)
        response = select(ObjectToUser).join(Object).where(Object.uuid == uuid_entity)
        result = await self.__session.execute(response)
        staff = result.scalars().all()
        try:
            for i in staff:
                await self.__session.delete(i)
            obj.is_deleted = True
            await self.update(obj)
        except Exception:
            await self.__session.rollback()

    async def get_user_by_uuid_object(self, uuid: str) -> list[User]:
        entity = await self.get_by_uuid(uuid)
        response = select(User).join(ObjectToUser).where(ObjectToUser.id_object == entity.id)
        result = await self.__session.execute(response)
        return result.scalars().all()

    async def unique_object_to_user(self, uuid_object: str, uuid_user: str) -> bool:
        response = select(ObjectToUser).\
            join(Object).\
            join(User).\
            where(Object.uuid == uuid_object).\
            where(User.uuid == uuid_user)
        result = await self.__session.execute(response)
        entity = result.scalars().first()
        if entity is None:
            return True
        return False

    async def add_user_to_object(self, obj: Object, user: User):
        try:
            self.__session.add(ObjectToUser(
                id_object=obj.id,
                id_user=user.id
            ))
            await self.__session.commit()
        except:
            await self.__session.rollback()
            raise Exception

    async def delete_user_to_object(self, uuid_object: str, uuid_user: str):
        response = select(ObjectToUser). \
            join(Object). \
            join(User). \
            where(Object.uuid == uuid_object). \
            where(User.uuid == uuid_user)
        result = await self.__session.execute(response)
        entity = result.scalars().first()
        if entity is None:
            raise Exception
        try:
            await self.__session.delete(entity)
            await self.__session.commit()
        except Exception:
            await self.__session.rollback()

    async def get_all_uuid_obj(self) -> list:
        response = select(Object.uuid, Object.name)
        result = await self.__session.execute(response)
        return result.fetchall()

    async def get_registrate_user_by_object(self, user_id: int):
        response = select(ObjectToUser).where(ObjectToUser.id_user == user_id)
        result = await self.__session.execute(response)
        return result.scalars().all()

    async def get_object_by_user_uuid(self, uuid_user: str) -> Object | None:
        response = (select(Object)
                    .join(ObjectToUser, Object.id == ObjectToUser.id_object)
                    .join(User, User.id == ObjectToUser.id_user)
                    .where(User.uuid == uuid_user))
        result = await self.__session.execute(response)
        return result.scalars().first()

    async def get_object_by_uuid_equipment(self, uuid_user: str, uuid_equipment: str) -> Object | None:
        response = (select(Object)
                    .join(Equipment)
                    .where(Equipment.uuid == uuid_equipment)
                    .where(Equipment.is_delite == False)
                    .join(ObjectToUser, Object.id == ObjectToUser.id_object)
                    .join(User, User.id == ObjectToUser.id_user)
                    .where(User.uuid == uuid_user)
                    )
        result = await self.__session.execute(response)
        return result.scalars().first()