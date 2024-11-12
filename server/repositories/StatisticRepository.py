from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, extract, and_

from fastapi import Depends

from ..tables import Accident, Object, TypeBrakeToAccident, TypeBrake, ClassBrake, StateAccident
from ..database import get_session

from datetime import datetime


class StatisticRepository:
    def __init__(self, session: AsyncSession = Depends(get_session)):
        self.__session: AsyncSession = session

    async def get_statistic_state_group_by(self, year: int):

        response = (select(Object.uuid.label("object_uuid"),
                           ClassBrake.id.label('class_brake_id'),
                           func.coalesce(func.count(Accident.id), 0).label('accident_count')).
                    select_from(Accident).
                    outerjoin(TypeBrakeToAccident, Accident.id == TypeBrakeToAccident.id_accident).
                    outerjoin(TypeBrake, TypeBrake.id == TypeBrakeToAccident.id_type_brake).
                    outerjoin(ClassBrake, TypeBrake.id_type == ClassBrake.id).
                    outerjoin(Object, Object.id == Accident.id_object).
                    outerjoin(StateAccident, StateAccident.id == Accident.id_state_accident).
                    where(extract('year', Accident.datetime_start) == year, StateAccident.name == "accepted").
                    group_by(Object.uuid, ClassBrake.id))

        result = await self.__session.execute(response)
        return result.fetchall()

    async def get_statistic_state_by_object_and_type(self, uuid_object: str):
        sub_response = select(ClassBrake.name.label('type_brake_name'),
                              ClassBrake.id.label('type_brake_id')).select_from(ClassBrake)

        response = (select(ClassBrake.name.label('type_name'),
                           func.coalesce(func.count(Accident.id), 0).label('accident_count')).
                    select_from(sub_response).
                    outerjoin(Accident, Accident.id == TypeBrakeToAccident.id_accident).
                    outerjoin(TypeBrake, TypeBrake.id == TypeBrakeToAccident.id_type_brake).
                    outerjoin(ClassBrake, TypeBrake.id_type == sub_response.c.type_brake_id).
                    outerjoin(Object, Object.id == Accident.id_object).
                    outerjoin(StateAccident, StateAccident.id == Accident.id_state_accident).
                    where(Object.uuid == uuid_object, StateAccident.name == "accepted").
                    group_by(sub_response.c.type_brake_name)
                    )

        print(response)
        result = await self.__session.execute(response)
        return result.fetchall()

    async def get_statistic_state_group_by_slice(self,
                                                 start_date: datetime,
                                                 end_date: datetime):
        response = (select(Object.uuid.label("object_uuid"),
                           ClassBrake.id.label('class_brake_id'),
                           func.coalesce(func.count(Accident.id), 0).label('accident_count')).
                    select_from(Accident).
                    outerjoin(TypeBrakeToAccident, Accident.id == TypeBrakeToAccident.id_accident).
                    outerjoin(TypeBrake, TypeBrake.id == TypeBrakeToAccident.id_type_brake).
                    outerjoin(ClassBrake, TypeBrake.id_type == ClassBrake.id).
                    outerjoin(Object, Object.id == Accident.id_object).
                    outerjoin(StateAccident, StateAccident.id == Accident.id_state_accident).
                    where(and_(Accident.datetime_start >= start_date, Accident.datetime_end <= end_date, StateAccident.name == "accepted")).
                    group_by(Object.uuid, ClassBrake.id))

        result = await self.__session.execute(response)
        return result.fetchall()

    async def get_statistic_object_all(self, uuid_object: str):
        response = (select(TypeBrake.id.label('type_brake_id'),
                           func.coalesce(func.count(Accident.id), 0).label('accident_count')).
                    select_from(Accident).
                    outerjoin(TypeBrakeToAccident, Accident.id == TypeBrakeToAccident.id_accident).
                    outerjoin(TypeBrake, TypeBrake.id == TypeBrakeToAccident.id_type_brake).
                    outerjoin(Object, Object.id == Accident.id_object).
                    outerjoin(StateAccident, StateAccident.id == Accident.id_state_accident).
                    where(Object.uuid == uuid_object, StateAccident.name == "accepted").
                    group_by(TypeBrake.id))

        result = await self.__session.execute(response)
        return result.fetchall()

    async def get_statistic_object_by_type(self, uuid_object: str, class_brake: int):
        response = (select(TypeBrake.id.label('type_brake_id'),
                           func.coalesce(func.count(Accident.id), 0).label('accident_count')).
                    select_from(Accident).
                    outerjoin(TypeBrakeToAccident, Accident.id == TypeBrakeToAccident.id_accident).
                    outerjoin(TypeBrake, TypeBrake.id == TypeBrakeToAccident.id_type_brake).
                    outerjoin(Object, Object.id == Accident.id_object).
                    outerjoin(StateAccident, StateAccident.id == Accident.id_state_accident).
                    where(and_(Object.uuid == uuid_object, TypeBrake.id_type == class_brake, StateAccident.name == "accepted")).
                    group_by(TypeBrake.id))

        result = await self.__session.execute(response)
        return result.fetchall()