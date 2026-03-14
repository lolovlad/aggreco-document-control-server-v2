from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, extract, and_, asc, desc
from typing import Optional, List, Literal
from uuid import UUID
from types import SimpleNamespace

from fastapi import Depends

from ..tables import (
    Claim,
    Accident,
    StateClaim,
    TypeBrake,
    TypeBrakeToAccident,
    ClassBrake,
    SignsAccident,
    EquipmentToAccident,
    SignsAccidentToAccident,
)
from ..database import get_session
from .UserRepository import UserRepository

from datetime import datetime


class StatisticRepository:
    def __init__(
        self,
        session: AsyncSession = Depends(get_session),
        user_repo: UserRepository = Depends(),
    ):
        self.__session: AsyncSession = session
        self.__user_repo: UserRepository = user_repo

    async def get_statistic_state_group_by_universal(
            self,
            start_date: Optional[datetime] = None,
            end_date: Optional[datetime] = None,
            list_object: Optional[List[UUID]] = None,
            sort_by: Optional[Literal["claim_count", "object_name"]] = "claim_count",
            sort_order: Optional[Literal["asc", "desc"]] = "desc"
    ):
        """
        Универсальный метод для получения количества заявок по объектам с поддержкой фильтров:
        - start_date: начальная дата (опционально)
        - end_date: конечная дата (опционально)
        - list_object: список UUID объектов для фильтрации (опционально)
        - sort_by: поле для сортировки ("claim_count" или "object_name"), по умолчанию "claim_count"
        - sort_order: порядок сортировки ("asc" или "desc"), по умолчанию "desc"
        """
        conditions = [StateClaim.name == "accepted"]
        
        if start_date is not None:
            conditions.append(Claim.datetime >= start_date)
        if end_date is not None:
            conditions.append(Claim.datetime <= end_date)
        if list_object:
            conditions.append(Accident.uuid_object.in_(list_object))

        # Запрос через Claim -> Accident, группировка по uuid объекта
        query = (
            select(
                Accident.uuid_object.label("object_uuid"),
                # object_name временно заполняем UUID объекта
                Accident.uuid_object.label("object_name"),
                func.count(Claim.id).label('claim_count')
            )
            .select_from(Claim)
            .join(Accident, Claim.id_accident == Accident.id)
            .join(StateClaim, Claim.id_state_claim == StateClaim.id)
            .where(and_(*conditions))
            .group_by(Accident.uuid_object)
        )

        # Применяем сортировку
        if sort_by == "claim_count":
            if sort_order == "asc":
                query = query.order_by(asc(func.count(Claim.id)))
            else:
                query = query.order_by(desc(func.count(Claim.id)))
        elif sort_by == "object_name":
            if sort_order == "asc":
                query = query.order_by(asc(Accident.uuid_object))
            else:
                query = query.order_by(desc(Accident.uuid_object))

        result = await self.__session.execute(query)
        return result.fetchall()

    async def get_statistic_by_month_and_object(
            self,
            start_date: Optional[datetime] = None,
            end_date: Optional[datetime] = None,
            list_object: Optional[List[UUID]] = None,
            sort_by: Optional[Literal["claim_count", "object_name"]] = "claim_count",
            sort_order: Optional[Literal["asc", "desc"]] = "desc"
    ):
        """
        Метод для получения статистики, сгруппированной по месяцам и объектам:
        - start_date: начальная дата (опционально)
        - end_date: конечная дата (опционально)
        - list_object: список UUID объектов для фильтрации (опционально)
        - sort_by: поле для сортировки ("claim_count" или "object_name"), по умолчанию "claim_count"
        - sort_order: порядок сортировки ("asc" или "desc"), по умолчанию "desc"
        """
        conditions = [StateClaim.name == "accepted"]
        
        if start_date is not None:
            conditions.append(Claim.datetime >= start_date)
        if end_date is not None:
            conditions.append(Claim.datetime <= end_date)
        if list_object:
            conditions.append(Accident.uuid_object.in_(list_object))

        # Группируем по году-месяцу и объекту
        month_expr = func.to_char(Claim.datetime, 'YYYY-MM')
        
        query = (
            select(
                month_expr.label("month"),
                Accident.uuid_object.label("object_uuid"),
                Accident.uuid_object.label("object_name"),
                func.count(Claim.id).label('claim_count')
            )
            .select_from(Claim)
            .join(Accident, Claim.id_accident == Accident.id)
            .join(StateClaim, Claim.id_state_claim == StateClaim.id)
            .where(and_(*conditions))
            .group_by(
                month_expr,
                Accident.uuid_object,
            )
        )

        # Применяем сортировку: сначала по месяцу, потом по выбранному полю
        order_clauses = [month_expr]
        
        if sort_by == "claim_count":
            if sort_order == "asc":
                order_clauses.append(asc(func.count(Claim.id)))
            else:
                order_clauses.append(desc(func.count(Claim.id)))
        elif sort_by == "object_name":
            if sort_order == "asc":
                order_clauses.append(asc(Accident.uuid_object))
            else:
                order_clauses.append(desc(Accident.uuid_object))
        
        query = query.order_by(*order_clauses)

        result = await self.__session.execute(query)
        return result.fetchall()

    async def get_statistic_group_by_class(
            self,
            start_date: Optional[datetime] = None,
            end_date: Optional[datetime] = None,
            list_object: Optional[List[UUID]] = None,
            sort_by: Optional[Literal["claim_count", "object_name"]] = "claim_count",
            sort_order: Optional[Literal["asc", "desc"]] = "desc"
    ):
        """
        Статистика по объектам, сгруппированная по ClassBrake.
        Считаем количество заявок (Claim).
        """
        conditions = [StateClaim.name == "accepted"]

        if start_date is not None:
            conditions.append(Claim.datetime >= start_date)
        if end_date is not None:
            conditions.append(Claim.datetime <= end_date)
        if list_object:
            conditions.append(Accident.uuid_object.in_(list_object))

        query = (
            select(
                Accident.uuid_object.label("object_uuid"),
                Accident.uuid_object.label("object_name"),
                ClassBrake.id.label("class_brake_id"),
                ClassBrake.description.label("class_brake_name"),
                ClassBrake.description.label("class_brake_description"),
                func.count(Claim.id).label("claim_count"),
            )
            .select_from(Claim)
            .join(Accident, Claim.id_accident == Accident.id)
            .join(StateClaim, Claim.id_state_claim == StateClaim.id)
            .join(TypeBrakeToAccident, Accident.id == TypeBrakeToAccident.id_accident)
            .join(TypeBrake, TypeBrake.id == TypeBrakeToAccident.id_type_brake)
            .join(ClassBrake, ClassBrake.id == TypeBrake.id_type)
            .where(and_(*conditions))
            .group_by(
                Accident.uuid_object,
                ClassBrake.id,
                ClassBrake.name,
            )
        )

        # сортировка
        if sort_by == "claim_count":
            if sort_order == "asc":
                query = query.order_by(asc(func.count(Claim.id)))
            else:
                query = query.order_by(desc(func.count(Claim.id)))
        elif sort_by == "object_name":
            if sort_order == "asc":
                query = query.order_by(asc(Accident.uuid_object))
            else:
                query = query.order_by(desc(Accident.uuid_object))

        result = await self.__session.execute(query)
        return result.fetchall()

    async def get_statistic_group_by_type(
            self,
            start_date: Optional[datetime] = None,
            end_date: Optional[datetime] = None,
            list_object: Optional[List[UUID]] = None,
            sort_by: Optional[Literal["claim_count", "object_name"]] = "claim_count",
            sort_order: Optional[Literal["asc", "desc"]] = "desc"
    ):
        """
        Статистика по объектам, сгруппированная по TypeBrake.
        Считаем количество заявок (Claim).
        """
        conditions = [StateClaim.name == "accepted"]

        if start_date is not None:
            conditions.append(Claim.datetime >= start_date)
        if end_date is not None:
            conditions.append(Claim.datetime <= end_date)
        if list_object:
            conditions.append(Accident.uuid_object.in_(list_object))

        query = (
            select(
                Accident.uuid_object.label("object_uuid"),
                Accident.uuid_object.label("object_name"),
                TypeBrake.id.label("type_brake_id"),
                TypeBrake.name.label("type_brake_name"),
                ClassBrake.id.label("class_brake_id"),
                ClassBrake.description.label("class_brake_name"),
                func.count(Claim.id).label("claim_count"),
            )
            .select_from(Claim)
            .join(Accident, Claim.id_accident == Accident.id)
            .join(StateClaim, Claim.id_state_claim == StateClaim.id)
            .join(TypeBrakeToAccident, Accident.id == TypeBrakeToAccident.id_accident)
            .join(TypeBrake, TypeBrake.id == TypeBrakeToAccident.id_type_brake)
            .join(ClassBrake, ClassBrake.id == TypeBrake.id_type)
            .where(and_(*conditions))
            .group_by(
                Accident.uuid_object,
                TypeBrake.id,
                TypeBrake.name,
                ClassBrake.id,
                ClassBrake.description,
            )
        )

        # сортировка
        if sort_by == "claim_count":
            if sort_order == "asc":
                query = query.order_by(asc(func.count(Claim.id)))
            else:
                query = query.order_by(desc(func.count(Claim.id)))
        elif sort_by == "object_name":
            if sort_order == "asc":
                query = query.order_by(asc(Accident.uuid_object))
            else:
                query = query.order_by(desc(Accident.uuid_object))

        result = await self.__session.execute(query)
        return result.fetchall()

    async def get_statistic_by_month_and_class(
            self,
            start_date: Optional[datetime] = None,
            end_date: Optional[datetime] = None,
            list_object: Optional[List[UUID]] = None,
            sort_by: Optional[Literal["claim_count", "object_name"]] = "claim_count",
            sort_order: Optional[Literal["asc", "desc"]] = "desc"
    ):
        """
        Статистика по объектам, сгруппированная по месяцам и ClassBrake.
        Считаем количество заявок (Claim).
        Каждый результат соответствует месяцу, объекту и классу отказа.
        """
        conditions = [StateClaim.name == "accepted"]

        if start_date is not None:
            conditions.append(Claim.datetime >= start_date)
        if end_date is not None:
            conditions.append(Claim.datetime <= end_date)
        if list_object:
            conditions.append(Accident.uuid_object.in_(list_object))

        month_expr = func.to_char(Claim.datetime, 'YYYY-MM')

        query = (
            select(
                month_expr.label("month"),
                Accident.uuid_object.label("object_uuid"),
                Accident.uuid_object.label("object_name"),
                ClassBrake.id.label("class_brake_id"),
                ClassBrake.description.label("class_brake_name"),
                ClassBrake.description.label("class_brake_description"),
                func.count(Claim.id).label("claim_count"),
            )
            .select_from(Claim)
            .join(Accident, Claim.id_accident == Accident.id)
            .join(StateClaim, Claim.id_state_claim == StateClaim.id)
            .join(TypeBrakeToAccident, Accident.id == TypeBrakeToAccident.id_accident)
            .join(TypeBrake, TypeBrake.id == TypeBrakeToAccident.id_type_brake)
            .join(ClassBrake, ClassBrake.id == TypeBrake.id_type)
            .where(and_(*conditions))
            .group_by(
                month_expr,
                Accident.uuid_object,
                ClassBrake.id,
                ClassBrake.name,
            )
        )

        order_clauses = [month_expr]

        if sort_by == "claim_count":
            if sort_order == "asc":
                order_clauses.append(asc(func.count(Claim.id)))
            else:
                order_clauses.append(desc(func.count(Claim.id)))
        elif sort_by == "object_name":
            if sort_order == "asc":
                order_clauses.append(asc(Accident.uuid_object))
            else:
                order_clauses.append(desc(Accident.uuid_object))

        query = query.order_by(*order_clauses)

        result = await self.__session.execute(query)
        return result.fetchall()

    async def get_export_data(
            self,
            start_date: Optional[datetime] = None,
            end_date: Optional[datetime] = None,
            list_object: Optional[List[UUID]] = None,
    ):
        """
        Получение данных для экспорта в CSV.
        Возвращает данные Claim, Accident, TypeBrake, ClassBrake с нужными полями.
        """
        conditions = [StateClaim.name == "accepted"]

        if start_date is not None:
            conditions.append(Claim.datetime >= start_date)
        if end_date is not None:
            conditions.append(Claim.datetime <= end_date)
        if list_object:
            conditions.append(Accident.uuid_object.in_(list_object))

        # Основной запрос для получения Claim, Accident, TypeBrake, ClassBrake.
        # Данные пользователя (ФИО, email) подтягиваем из микросервиса по user_uuid.
        query = (
            select(
                # Accident.id нужен для получения equipment и signs (скрытое поле)
                Accident.id.label("accident_id"),
                # Claim поля (исключаем: state_claim, main_document, edit_document, comment, last_datetime_edit, id, uuid)
                Claim.datetime.label("claim_datetime"),
                Claim.user_uuid.label("user_uuid"),
                # Accident поля (исключаем: time_line, event, state_accident, time_zone, id, uuid)
                Accident.datetime_start.label("accident_datetime_start"),
                Accident.datetime_end.label("accident_datetime_end"),
                Accident.causes_of_the_emergency.label("accident_causes"),
                Accident.damaged_equipment_material.label("accident_damaged_equipment"),
                Accident.additional_material.label("accident_additional_material"),
                Accident.is_delite.label("accident_is_deleted"),
                # Имя объекта теперь недоступно из локной БД, временно используем uuid_object
                Accident.uuid_object.label("object_name"),
                # TypeBrake поля (исключаем: id)
                TypeBrake.code.label("type_brake_code"),
                TypeBrake.name.label("type_brake_name"),
                # ClassBrake поля (исключаем: id, name)
                ClassBrake.description.label("class_brake_description"),
            )
            .select_from(Claim)
            .join(Accident, Claim.id_accident == Accident.id)
            .join(StateClaim, Claim.id_state_claim == StateClaim.id)
            .join(TypeBrakeToAccident, Accident.id == TypeBrakeToAccident.id_accident)
            .join(TypeBrake, TypeBrake.id == TypeBrakeToAccident.id_type_brake)
            .join(ClassBrake, ClassBrake.id == TypeBrake.id_type)
            .where(and_(*conditions))
            .order_by(Claim.datetime.desc())
        )

        db_result = await self.__session.execute(query)
        rows = db_result.fetchall()

        # Собираем все уникальные UUID пользователей из заявок
        user_uuids: list[str] = []
        for row in rows:
            if row.user_uuid is not None:
                uuid_str = str(row.user_uuid)
                if uuid_str not in user_uuids:
                    user_uuids.append(uuid_str)

        # Запрашиваем пользователей в микросервисе
        users = await self.__user_repo.get_users_by_uuids(user_uuids)
        users_by_uuid = {str(user.uuid): user for user in users}

        # Возвращаем данные в том же формате полей, который ожидает сервис экспорта
        enriched_rows: list[SimpleNamespace] = []
        for row in rows:
            user = users_by_uuid.get(str(row.user_uuid)) if row.user_uuid is not None else None

            enriched_rows.append(
                SimpleNamespace(
                    accident_id=row.accident_id,
                    claim_datetime=row.claim_datetime,
                    user_name=getattr(user, "name", None) if user else None,
                    user_surname=getattr(user, "surname", None) if user else None,
                    user_patronymic=getattr(user, "patronymic", None) if user else None,
                    user_email=getattr(user, "email", None) if user else None,
                    accident_datetime_start=row.accident_datetime_start,
                    accident_datetime_end=row.accident_datetime_end,
                    accident_causes=row.accident_causes,
                    accident_damaged_equipment=row.accident_damaged_equipment,
                    accident_additional_material=row.accident_additional_material,
                    accident_is_deleted=row.accident_is_deleted,
                    object_name=row.object_name,
                    type_brake_code=row.type_brake_code,
                    type_brake_name=row.type_brake_name,
                    class_brake_description=row.class_brake_description,
                )
            )

        return enriched_rows

    async def get_accident_equipment(self, accident_id: int):
        """Получение списка оборудования для аварии"""
        query = (
            select(EquipmentToAccident.uuid_equipment.label("equipment_uuid"))
            .select_from(EquipmentToAccident)
            .where(EquipmentToAccident.id_accident == accident_id)
        )
        result = await self.__session.execute(query)
        return [str(row.equipment_uuid) for row in result.fetchall()]

    async def get_accident_signs(self, accident_id: int):
        """Получение списка признаков для аварии"""
        query = (
            select(SignsAccident.name.label("sign_name"))
            .select_from(SignsAccident)
            .join(SignsAccidentToAccident, SignsAccident.id == SignsAccidentToAccident.id_signs_accident)
            .where(SignsAccidentToAccident.id_accident == accident_id)
        )
        result = await self.__session.execute(query)
        return [row.sign_name for row in result.fetchall()]