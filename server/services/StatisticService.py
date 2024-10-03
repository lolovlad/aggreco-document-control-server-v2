from fastapi import Depends

from ..repositories import StatisticRepository, ObjectRepository, TypeBrakeRepository
from ..models.Statistic import GetAllStatistic
from ..models.Accident import ClassBrake

from copy import deepcopy
from datetime import datetime


class StatisticService:
    def __init__(self,
                 statistic_repo: StatisticRepository = Depends(),
                 object_repo: ObjectRepository = Depends(),
                 type_brake_repo: TypeBrakeRepository = Depends()):
        self.__statistic_repo: StatisticRepository = statistic_repo
        self.__object_repo: ObjectRepository = object_repo
        self.__type_brake_repo: TypeBrakeRepository = type_brake_repo

    async def __get_table_accident_all(self) -> dict:
        list_obj = await self.__object_repo.get_all_uuid_obj()
        list_type = await self.__type_brake_repo.get_all_class_brake()
        table = {}

        type_count = {i.id: {"name": i.description, "count": 0} for i in list_type}

        for obj in list_obj:
            table[str(obj[0])] = {
                "name": obj[1],
                "type_count": deepcopy(type_count),

            }
        return table

    async def __get_table_object(self, type_filter: str, param: str) -> dict:
        if type_filter == "all":
            list_type = await self.__type_brake_repo.get_all_type_brake()
        elif type_filter == "type":
            list_type = await self.__type_brake_repo.get_all_type_brake_by_class_id(int(param))
        table = {}

        for tp in list_type:
            table[tp.id] = {
                "name": tp.name,
                "count": 0,

            }
        return table

    async def get_accident_statistic(self, year: int) -> GetAllStatistic:
        statistics = await self.__statistic_repo.get_statistic_state_group_by(year)

        stat = GetAllStatistic()

        table = await self.__get_table_accident_all()

        for i in statistics:
            table[str(i.object_uuid)]["type_count"][i.class_brake_id]["count"] = i.accident_count

        stat.obj = table
        return stat

    async def get_accident_statistic_slice_date(self, start_date: str, end_date: str) -> GetAllStatistic:
        start_date = datetime.strptime(start_date, "%Y-%m-%d")
        end_date = datetime.strptime(end_date, "%Y-%m-%d")

        table = await self.__get_table_accident_all()
        statistics = await self.__statistic_repo.get_statistic_state_group_by_slice(start_date, end_date)
        stat = GetAllStatistic()

        for i in statistics:
            table[str(i.object_uuid)]["type_count"][i.class_brake_id]["count"] = i.accident_count

        stat.obj = table
        return stat

    async def get_object_statistic(self, uuid_object: str, type_filter: str, param: str) -> GetAllStatistic:
        if type_filter == "all":
            statistics = await self.__statistic_repo.get_statistic_object_all(uuid_object)
        elif type_filter == "type":
            statistics = await self.__statistic_repo.get_statistic_object_by_type(uuid_object, int(param))

        table = await self.__get_table_object(type_filter, param)
        stat = GetAllStatistic()

        for i in statistics:
            table[i.type_brake_id]["count"] = i.accident_count

        stat.obj = table
        return stat

    async def get_list_class_brake(self) -> list[ClassBrake]:
        list_class = await self.__type_brake_repo.get_all_class_brake()
        return [ClassBrake.model_validate(i, from_attributes=True) for i in list_class]