from fastapi import Depends
from typing import Optional, List
from uuid import UUID
import csv
import io
from datetime import datetime

from ..repositories import StatisticRepository, ObjectRepository, TypeBrakeRepository
from ..models.Statistic import (
    GetAllStatistic,
    ObjectStatistic,
    ObjectDetailStatistic,
    GetMonthlyStatistic,
    MonthStatistic,
    GetClassBrakeStatistic,
    ClassBrakeStatisticItem,
    GetTypeBrakeStatistic,
    TypeBrakeStatisticItem,
    GetMonthlyClassBrakeStatistic,
    MonthClassBrakeStatisticItem,
)
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

    async def get_accident_statistic_universal(
            self,
            start_date: Optional[str] = None,
            end_date: Optional[str] = None,
            list_object: Optional[List[str]] = None,
            sort_by: Optional[str] = "claim_count",
            sort_order: Optional[str] = "desc"
    ) -> GetAllStatistic:
        """
        Универсальный метод для получения статистики заявок с поддержкой фильтров:
        - start_date: начальная дата в формате "%Y-%m-%d" (опционально)
        - end_date: конечная дата в формате "%Y-%m-%d" (опционально)
        - list_object: список UUID объектов для фильтрации (опционально)
        - sort_by: поле для сортировки ("claim_count" или "object_name"), по умолчанию "claim_count"
        - sort_order: порядок сортировки ("asc" или "desc"), по умолчанию "desc"
        """
        from typing import Literal
        
        start_date_dt = None
        end_date_dt = None
        list_object_uuid = None

        if start_date is not None:
            start_date_dt = datetime.strptime(start_date, "%Y-%m-%d")

        if end_date is not None:
            end_date_dt = datetime.strptime(end_date, "%Y-%m-%d")

        if list_object is not None and len(list_object) > 0:
            list_object_uuid = [UUID(obj_uuid) for obj_uuid in list_object]

        # Валидация параметров сортировки
        valid_sort_by = ["claim_count", "object_name"]
        valid_sort_order = ["asc", "desc"]
        
        sort_by_value: Literal["claim_count", "object_name"] = (
            sort_by if sort_by in valid_sort_by else "claim_count"
        )
        sort_order_value: Literal["asc", "desc"] = (
            sort_order if sort_order in valid_sort_order else "desc"
        )

        statistics = await self.__statistic_repo.get_statistic_state_group_by_universal(
            start_date=start_date_dt,
            end_date=end_date_dt,
            list_object=list_object_uuid,
            sort_by=sort_by_value,
            sort_order=sort_order_value
        )

        # Формируем список статистики по объектам (название уже есть в результате запроса)
        objects_statistic = [
            ObjectStatistic(
                object_uuid=str(stat.object_uuid),
                object_name=stat.object_name or "",
                claim_count=stat.claim_count
            )
            for stat in statistics
        ]

        return GetAllStatistic(objects=objects_statistic)

    async def get_accident_statistic_by_month(
            self,
            start_date: Optional[str] = None,
            end_date: Optional[str] = None,
            list_object: Optional[List[str]] = None,
            sort_by: Optional[str] = "claim_count",
            sort_order: Optional[str] = "desc"
    ) -> GetMonthlyStatistic:
        """
        Метод для получения статистики, сгруппированной по месяцам и объектам:
        - start_date: начальная дата в формате "%Y-%m-%d" (опционально)
        - end_date: конечная дата в формате "%Y-%m-%d" (опционально)
        - list_object: список UUID объектов для фильтрации (опционально)
        - sort_by: поле для сортировки ("claim_count" или "object_name"), по умолчанию "claim_count"
        - sort_order: порядок сортировки ("asc" или "desc"), по умолчанию "desc"
        """
        from typing import Literal
        
        start_date_dt = None
        end_date_dt = None
        list_object_uuid = None

        if start_date is not None:
            start_date_dt = datetime.strptime(start_date, "%Y-%m-%d")

        if end_date is not None:
            end_date_dt = datetime.strptime(end_date, "%Y-%m-%d")

        if list_object is not None and len(list_object) > 0:
            list_object_uuid = [UUID(obj_uuid) for obj_uuid in list_object]

        # Валидация параметров сортировки
        valid_sort_by = ["claim_count", "object_name"]
        valid_sort_order = ["asc", "desc"]
        
        sort_by_value: Literal["claim_count", "object_name"] = (
            sort_by if sort_by in valid_sort_by else "claim_count"
        )
        sort_order_value: Literal["asc", "desc"] = (
            sort_order if sort_order in valid_sort_order else "desc"
        )

        statistics = await self.__statistic_repo.get_statistic_by_month_and_object(
            start_date=start_date_dt,
            end_date=end_date_dt,
            list_object=list_object_uuid,
            sort_by=sort_by_value,
            sort_order=sort_order_value
        )

        # Группируем результаты по месяцам
        months_dict = {}
        for stat in statistics:
            month = stat.month
            if month not in months_dict:
                months_dict[month] = []
            
            months_dict[month].append(
                ObjectStatistic(
                    object_uuid=str(stat.object_uuid),
                    object_name=stat.object_name or "",
                    claim_count=stat.claim_count
                )
            )

        # Преобразуем в список и сортируем по месяцам
        months_list = [
            MonthStatistic(month=month, objects=objects)
            for month, objects in sorted(months_dict.items())
        ]

        return GetMonthlyStatistic(months=months_list)

    async def get_accident_statistic_group_by_class(
            self,
            start_date: Optional[str] = None,
            end_date: Optional[str] = None,
            list_object: Optional[List[str]] = None,
            sort_by: Optional[str] = "claim_count",
            sort_order: Optional[str] = "desc"
    ) -> GetClassBrakeStatistic:
        """
        Статистика заявок по объектам, сгруппированная по ClassBrake.
        """
        from typing import Literal

        start_date_dt = None
        end_date_dt = None
        list_object_uuid = None

        if start_date is not None:
            start_date_dt = datetime.strptime(start_date, "%Y-%m-%d")

        if end_date is not None:
            end_date_dt = datetime.strptime(end_date, "%Y-%m-%d")

        if list_object is not None and len(list_object) > 0:
            list_object_uuid = [UUID(obj_uuid) for obj_uuid in list_object]

        valid_sort_by = ["claim_count", "object_name"]
        valid_sort_order = ["asc", "desc"]

        sort_by_value: Literal["claim_count", "object_name"] = (
            sort_by if sort_by in valid_sort_by else "claim_count"
        )
        sort_order_value: Literal["asc", "desc"] = (
            sort_order if sort_order in valid_sort_order else "desc"
        )

        statistics = await self.__statistic_repo.get_statistic_group_by_class(
            start_date=start_date_dt,
            end_date=end_date_dt,
            list_object=list_object_uuid,
            sort_by=sort_by_value,
            sort_order=sort_order_value,
        )

        items = [
            ClassBrakeStatisticItem(
                object_uuid=str(stat.object_uuid),
                object_name=stat.object_name or "",
                class_brake_id=stat.class_brake_id,
                class_brake_name=stat.class_brake_name or "",
                claim_count=stat.claim_count,
            )
            for stat in statistics
        ]

        return GetClassBrakeStatistic(items=items)

    async def get_accident_statistic_group_by_type(
            self,
            start_date: Optional[str] = None,
            end_date: Optional[str] = None,
            list_object: Optional[List[str]] = None,
            sort_by: Optional[str] = "claim_count",
            sort_order: Optional[str] = "desc"
    ) -> GetTypeBrakeStatistic:
        """
        Статистика заявок по объектам, сгруппированная по TypeBrake.
        """
        from typing import Literal

        start_date_dt = None
        end_date_dt = None
        list_object_uuid = None

        if start_date is not None:
            start_date_dt = datetime.strptime(start_date, "%Y-%m-%d")

        if end_date is not None:
            end_date_dt = datetime.strptime(end_date, "%Y-%m-%d")

        if list_object is not None and len(list_object) > 0:
            list_object_uuid = [UUID(obj_uuid) for obj_uuid in list_object]

        valid_sort_by = ["claim_count", "object_name"]
        valid_sort_order = ["asc", "desc"]

        sort_by_value: Literal["claim_count", "object_name"] = (
            sort_by if sort_by in valid_sort_by else "claim_count"
        )
        sort_order_value: Literal["asc", "desc"] = (
            sort_order if sort_order in valid_sort_order else "desc"
        )

        statistics = await self.__statistic_repo.get_statistic_group_by_type(
            start_date=start_date_dt,
            end_date=end_date_dt,
            list_object=list_object_uuid,
            sort_by=sort_by_value,
            sort_order=sort_order_value,
        )

        items = [
            TypeBrakeStatisticItem(
                object_uuid=str(stat.object_uuid),
                object_name=stat.object_name or "",
                type_brake_id=stat.type_brake_id,
                type_brake_name=stat.type_brake_name or "",
                class_brake_id=stat.class_brake_id,
                class_brake_name=stat.class_brake_name or "",
                claim_count=stat.claim_count,
            )
            for stat in statistics
        ]

        return GetTypeBrakeStatistic(items=items)

    async def get_accident_statistic_by_month_and_class(
            self,
            start_date: Optional[str] = None,
            end_date: Optional[str] = None,
            list_object: Optional[List[str]] = None,
            sort_by: Optional[str] = "claim_count",
            sort_order: Optional[str] = "desc"
    ) -> GetMonthlyClassBrakeStatistic:
        """
        Статистика заявок по объектам, сгруппированная по месяцам и ClassBrake.
        """
        from typing import Literal

        start_date_dt = None
        end_date_dt = None
        list_object_uuid = None

        if start_date is not None:
            start_date_dt = datetime.strptime(start_date, "%Y-%m-%d")

        if end_date is not None:
            end_date_dt = datetime.strptime(end_date, "%Y-%m-%d")

        if list_object is not None and len(list_object) > 0:
            list_object_uuid = [UUID(obj_uuid) for obj_uuid in list_object]

        valid_sort_by = ["claim_count", "object_name"]
        valid_sort_order = ["asc", "desc"]

        sort_by_value: Literal["claim_count", "object_name"] = (
            sort_by if sort_by in valid_sort_by else "claim_count"
        )
        sort_order_value: Literal["asc", "desc"] = (
            sort_order if sort_order in valid_sort_order else "desc"
        )

        statistics = await self.__statistic_repo.get_statistic_by_month_and_class(
            start_date=start_date_dt,
            end_date=end_date_dt,
            list_object=list_object_uuid,
            sort_by=sort_by_value,
            sort_order=sort_order_value,
        )

        items = [
            MonthClassBrakeStatisticItem(
                month=stat.month,
                object_uuid=str(stat.object_uuid),
                object_name=stat.object_name or "",
                class_brake_id=stat.class_brake_id,
                class_brake_name=stat.class_brake_name or "",
                claim_count=stat.claim_count,
            )
            for stat in statistics
        ]

        return GetMonthlyClassBrakeStatistic(items=items)

    async def get_accident_statistic_group_by_class_for_object(
            self,
            uuid_object: str,
            start_date: Optional[str] = None,
            end_date: Optional[str] = None,
            sort_by: Optional[str] = "claim_count",
            sort_order: Optional[str] = "desc"
    ) -> GetClassBrakeStatistic:
        """
        Статистика заявок по конкретному объекту, сгруппированная по ClassBrake.
        """
        return await self.get_accident_statistic_group_by_class(
            start_date=start_date,
            end_date=end_date,
            list_object=[uuid_object],
            sort_by=sort_by,
            sort_order=sort_order,
        )

    async def get_accident_statistic_group_by_type_for_object(
            self,
            uuid_object: str,
            start_date: Optional[str] = None,
            end_date: Optional[str] = None,
            sort_by: Optional[str] = "claim_count",
            sort_order: Optional[str] = "desc"
    ) -> GetTypeBrakeStatistic:
        """
        Статистика заявок по конкретному объекту, сгруппированная по TypeBrake.
        """
        return await self.get_accident_statistic_group_by_type(
            start_date=start_date,
            end_date=end_date,
            list_object=[uuid_object],
            sort_by=sort_by,
            sort_order=sort_order,
        )

    async def get_accident_statistic_by_month_and_class_for_object(
            self,
            uuid_object: str,
            start_date: Optional[str] = None,
            end_date: Optional[str] = None,
            sort_by: Optional[str] = "claim_count",
            sort_order: Optional[str] = "desc"
    ) -> GetMonthlyClassBrakeStatistic:
        """
        Статистика заявок по конкретному объекту, сгруппированная по месяцам и ClassBrake.
        """
        return await self.get_accident_statistic_by_month_and_class(
            start_date=start_date,
            end_date=end_date,
            list_object=[uuid_object],
            sort_by=sort_by,
            sort_order=sort_order,
        )

    async def get_accident_statistic(self, year: int) -> GetAllStatistic:
        statistics = await self.__statistic_repo.get_statistic_state_group_by(year)

        stat = GetAllStatistic()

        table = await self.__get_table_accident_all()
        for i in statistics:
            try:
                table[str(i.object_uuid)]["type_count"][i.class_brake_id]["count"] = i.accident_count
            except KeyError:
                continue

        stat.obj = table
        return stat

    async def get_accident_statistic_slice_date(self, start_date: str, end_date: str) -> GetAllStatistic:
        start_date = datetime.strptime(start_date, "%Y-%m-%d")
        end_date = datetime.strptime(end_date, "%Y-%m-%d")

        table = await self.__get_table_accident_all()
        statistics = await self.__statistic_repo.get_statistic_state_group_by_slice(start_date, end_date)
        stat = GetAllStatistic()

        for i in statistics:
            try:
                table[str(i.object_uuid)]["type_count"][i.class_brake_id]["count"] = i.accident_count
            except KeyError:
                continue

        stat.obj = table
        return stat

    async def get_object_statistic(self, uuid_object: str, type_filter: str, param: str) -> ObjectDetailStatistic:
        if type_filter == "all":
            statistics = await self.__statistic_repo.get_statistic_object_all(uuid_object)
        elif type_filter == "type":
            statistics = await self.__statistic_repo.get_statistic_object_by_type(uuid_object, int(param))

        table = await self.__get_table_object(type_filter, param)

        for i in statistics:
            try:
                table[i.type_brake_id]["count"] = i.accident_count
            except KeyError:
                continue

        return ObjectDetailStatistic(obj=table)

    async def get_list_class_brake(self) -> list[ClassBrake]:
        list_class = await self.__type_brake_repo.get_all_class_brake()
        return [ClassBrake.model_validate(i, from_attributes=True) for i in list_class]

    async def export_to_csv(
            self,
            start_date: Optional[str] = None,
            end_date: Optional[str] = None,
            list_object: Optional[List[str]] = None,
    ) -> str:
        """
        Экспорт данных в CSV формат с русскими заголовками.
        """
        from typing import Literal

        start_date_dt = None
        end_date_dt = None
        list_object_uuid = None

        if start_date is not None:
            start_date_dt = datetime.strptime(start_date, "%Y-%m-%d")

        if end_date is not None:
            end_date_dt = datetime.strptime(end_date, "%Y-%m-%d")

        if list_object is not None and len(list_object) > 0:
            list_object_uuid = [UUID(obj_uuid) for obj_uuid in list_object]

        # Получаем данные из репозитория
        export_data = await self.__statistic_repo.get_export_data(
            start_date=start_date_dt,
            end_date=end_date_dt,
            list_object=list_object_uuid,
        )

        # Словарь для кэширования equipment и signs по accident_id
        equipment_cache = {}
        signs_cache = {}
        processed_accident_ids = set()

        # Создаем CSV в памяти
        output = io.StringIO()
        writer = csv.writer(output, delimiter=';', quoting=csv.QUOTE_ALL)

        # Заголовки на русском
        headers = [
            # Claim
            "Дата и время заявки",
            "ФИО пользователя",
            "Email пользователя",
            # Accident
            "Дата и время начала",
            "Дата и время окончания",
            "Причины аварии",
            "Поврежденное оборудование (материал)",
            "Дополнительные материалы",
            "Удалено",
            # Object
            "Название объекта",
            # TypeBrake
            "Код типа отказа",
            "Название типа отказа",
            # ClassBrake
            "Описание класса отказа",
            # Many-to-many
            "Оборудование",
            "Признаки аварии",
        ]

        writer.writerow(headers)

        # Обрабатываем каждую строку данных
        for row in export_data:
            accident_id = row.accident_id

            # Получаем equipment и signs для аварии (кэшируем)
            if accident_id not in processed_accident_ids:
                equipment_list = await self.__statistic_repo.get_accident_equipment(accident_id)
                signs_list = await self.__statistic_repo.get_accident_signs(accident_id)
                equipment_cache[accident_id] = ", ".join(equipment_list) if equipment_list else ""
                signs_cache[accident_id] = ", ".join(signs_list) if signs_list else ""
                processed_accident_ids.add(accident_id)

            # Формируем ФИО пользователя
            fio_parts = []
            if row.user_surname:
                fio_parts.append(row.user_surname)
            if row.user_name:
                fio_parts.append(row.user_name)
            if row.user_patronymic:
                fio_parts.append(row.user_patronymic)
            user_fio = " ".join(fio_parts) if fio_parts else ""

            # Формируем строку CSV
            csv_row = [
                # Claim
                row.claim_datetime.strftime("%Y-%m-%d %H:%M:%S") if row.claim_datetime else "",
                user_fio,
                row.user_email or "",
                # Accident
                row.accident_datetime_start.strftime("%Y-%m-%d %H:%M:%S") if row.accident_datetime_start else "",
                row.accident_datetime_end.strftime("%Y-%m-%d %H:%M:%S") if row.accident_datetime_end else "",
                row.accident_causes or "",
                row.accident_damaged_equipment or "",
                row.accident_additional_material or "",
                "Да" if row.accident_is_deleted else "Нет",
                # Object
                row.object_name or "",
                # TypeBrake
                row.type_brake_code or "",
                row.type_brake_name or "",
                # ClassBrake
                row.class_brake_description or "",
                # Many-to-many
                equipment_cache.get(accident_id, ""),
                signs_cache.get(accident_id, ""),
            ]

            writer.writerow(csv_row)

        output.seek(0)
        return output.getvalue()