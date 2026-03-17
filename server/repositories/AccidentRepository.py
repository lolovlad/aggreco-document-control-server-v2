from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete, and_

from fastapi import Depends

from uuid import UUID

from ..tables import Accident, StateAccident, SignsAccident, EquipmentToAccident
from ..database import get_session


class AccidentRepository:
    """
    Репозиторий аварий, больше не использующий таблицу object:
    фильтрация по объекту идёт по UUID, хранящемуся в самой записи Accident.
    """

    def __init__(self, session: AsyncSession = Depends(get_session)):
        self.__session: AsyncSession = session

    async def count_row(self, uuid_object: str | None) -> int:
        stmt = select(func.count(Accident.id)).where(Accident.is_delite == False)
        if uuid_object is not None:
            stmt = stmt.where(Accident.uuid_object == uuid_object)
        result = await self.__session.execute(stmt)
        return result.scalar_one_or_none() or 0

    async def get_limit_accident(
        self, uuid_object: str | None, start: int, count: int
    ) -> list[Accident]:
        stmt = select(Accident).where(Accident.is_delite == False)
        if uuid_object is not None:
            stmt = stmt.where(Accident.uuid_object == uuid_object)
        stmt = stmt.offset(start).fetch(count).order_by(Accident.id)
        result = await self.__session.execute(stmt)
        return result.scalars().unique().all()

    async def add(self, entity: Accident):
        try:
            self.__session.add(entity)
            await self.__session.commit()
        except Exception:
            await self.__session.rollback()
            raise

    async def add_equipment_links(self, accident_id: int, equipment_uuids: list[str]) -> None:
        """Добавляет связи аварии с оборудованием по UUID (таблица equipment_to_accident)."""
        for uuid_str in equipment_uuids:
            if not uuid_str:
                continue
            link = EquipmentToAccident(
                id_accident=accident_id,
                uuid_equipment=UUID(uuid_str) if isinstance(uuid_str, str) else uuid_str,
            )
            self.__session.add(link)
        try:
            await self.__session.commit()
        except Exception:
            await self.__session.rollback()
            raise

    async def replace_equipment_links(
        self, accident_id: int, equipment_uuids: list[str], accident_entity: Accident | None = None
    ) -> None:
        """Удаляет старые связи аварии с оборудованием и создаёт новые по списку UUID."""
        await self.__session.execute(delete(EquipmentToAccident).where(EquipmentToAccident.id_accident == accident_id))
        await self.__session.commit()
        await self.add_equipment_links(accident_id, equipment_uuids)
        if accident_entity is not None:
            self.__session.expire(accident_entity, ["damaged_equipment"])

    async def get_by_uuid(self, uuid_accident: str) -> Accident | None:
        stmt = select(Accident).where(Accident.uuid == uuid_accident)
        result = await self.__session.execute(stmt)
        return result.scalars().first()

    async def update(self, entity: Accident):
        try:
            self.__session.add(entity)
            await self.__session.commit()
        except Exception:
            await self.__session.rollback()
            raise

    async def get_state_accident_by_name(self, name: str) -> StateAccident:
        stmt = select(StateAccident).where(StateAccident.name == name)
        result = await self.__session.execute(stmt)
        return result.scalars().first()

    async def delete(self, entity: Accident):
        try:
            await self.__session.delete(entity)
            await self.__session.commit()
        except Exception:
            await self.__session.rollback()
            raise

    async def get_signs_accident_by_id_set(
        self, id_list: list[int]
    ) -> list[SignsAccident]:
        stmt = select(SignsAccident).where(SignsAccident.id.in_(id_list))
        result = await self.__session.execute(stmt)
        return result.scalars().all()

    async def get_accidents_between_dates(
        self,
        start_date,
        end_date,
    ) -> list[Accident]:
        """
        Возвращает аварии, у которых datetime_start попадает в интервал [start_date, end_date].
        """
        stmt = (
            select(Accident)
            .where(
                and_(
                    Accident.is_delite == False,
                    Accident.datetime_start >= start_date,
                    Accident.datetime_start <= end_date,
                )
            )
            .order_by(Accident.datetime_start)
        )
        result = await self.__session.execute(stmt)
        return result.scalars().unique().all()