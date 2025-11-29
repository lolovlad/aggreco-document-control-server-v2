from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, extract, and_, asc, desc
from typing import Optional, List, Literal
from uuid import UUID

from fastapi import Depends

from ..tables import Claim, Accident, Object, StateClaim, TypeBrake, TypeBrakeToAccident, StateAccident, ClassBrake, User, Equipment, SignsAccident, EquipmentToAccident, SignsAccidentToAccident
from ..database import get_session

from datetime import datetime


class StatisticRepository:
    def __init__(self, session: AsyncSession = Depends(get_session)):
        self.__session: AsyncSession = session

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
            conditions.append(Object.uuid.in_(list_object))

        # Запрос через Claim -> Accident -> Object
        query = (
            select(
                Object.uuid.label("object_uuid"),
                Object.name.label("object_name"),
                func.count(Claim.id).label('claim_count')
            )
            .select_from(Claim)
            .join(Accident, Claim.id_accident == Accident.id)
            .join(Object, Accident.id_object == Object.id)
            .join(StateClaim, Claim.id_state_claim == StateClaim.id)
            .where(and_(*conditions))
            .group_by(Object.uuid, Object.name)
        )

        # Применяем сортировку
        if sort_by == "claim_count":
            if sort_order == "asc":
                query = query.order_by(asc(func.count(Claim.id)))
            else:
                query = query.order_by(desc(func.count(Claim.id)))
        elif sort_by == "object_name":
            if sort_order == "asc":
                query = query.order_by(asc(Object.name))
            else:
                query = query.order_by(desc(Object.name))

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
            conditions.append(Object.uuid.in_(list_object))

        # Группируем по году-месяцу и объекту
        month_expr = func.to_char(Claim.datetime, 'YYYY-MM')
        
        query = (
            select(
                month_expr.label("month"),
                Object.uuid.label("object_uuid"),
                Object.name.label("object_name"),
                func.count(Claim.id).label('claim_count')
            )
            .select_from(Claim)
            .join(Accident, Claim.id_accident == Accident.id)
            .join(Object, Accident.id_object == Object.id)
            .join(StateClaim, Claim.id_state_claim == StateClaim.id)
            .where(and_(*conditions))
            .group_by(
                month_expr,
                Object.uuid,
                Object.name
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
                order_clauses.append(asc(Object.name))
            else:
                order_clauses.append(desc(Object.name))
        
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
            conditions.append(Object.uuid.in_(list_object))

        query = (
            select(
                Object.uuid.label("object_uuid"),
                Object.name.label("object_name"),
                ClassBrake.id.label("class_brake_id"),
                ClassBrake.description.label("class_brake_name"),
                ClassBrake.description.label("class_brake_description"),
                func.count(Claim.id).label("claim_count"),
            )
            .select_from(Claim)
            .join(Accident, Claim.id_accident == Accident.id)
            .join(Object, Accident.id_object == Object.id)
            .join(StateClaim, Claim.id_state_claim == StateClaim.id)
            .join(TypeBrakeToAccident, Accident.id == TypeBrakeToAccident.id_accident)
            .join(TypeBrake, TypeBrake.id == TypeBrakeToAccident.id_type_brake)
            .join(ClassBrake, ClassBrake.id == TypeBrake.id_type)
            .where(and_(*conditions))
            .group_by(
                Object.uuid,
                Object.name,
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
                query = query.order_by(asc(Object.name))
            else:
                query = query.order_by(desc(Object.name))

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
            conditions.append(Object.uuid.in_(list_object))

        query = (
            select(
                Object.uuid.label("object_uuid"),
                Object.name.label("object_name"),
                TypeBrake.id.label("type_brake_id"),
                TypeBrake.name.label("type_brake_name"),
                ClassBrake.id.label("class_brake_id"),
                ClassBrake.description.label("class_brake_name"),
                func.count(Claim.id).label("claim_count"),
            )
            .select_from(Claim)
            .join(Accident, Claim.id_accident == Accident.id)
            .join(Object, Accident.id_object == Object.id)
            .join(StateClaim, Claim.id_state_claim == StateClaim.id)
            .join(TypeBrakeToAccident, Accident.id == TypeBrakeToAccident.id_accident)
            .join(TypeBrake, TypeBrake.id == TypeBrakeToAccident.id_type_brake)
            .join(ClassBrake, ClassBrake.id == TypeBrake.id_type)
            .where(and_(*conditions))
            .group_by(
                Object.uuid,
                Object.name,
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
                query = query.order_by(asc(Object.name))
            else:
                query = query.order_by(desc(Object.name))

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
            conditions.append(Object.uuid.in_(list_object))

        month_expr = func.to_char(Claim.datetime, 'YYYY-MM')

        query = (
            select(
                month_expr.label("month"),
                Object.uuid.label("object_uuid"),
                Object.name.label("object_name"),
                ClassBrake.id.label("class_brake_id"),
                ClassBrake.description.label("class_brake_name"),
                ClassBrake.description.label("class_brake_description"),
                func.count(Claim.id).label("claim_count"),
            )
            .select_from(Claim)
            .join(Accident, Claim.id_accident == Accident.id)
            .join(Object, Accident.id_object == Object.id)
            .join(StateClaim, Claim.id_state_claim == StateClaim.id)
            .join(TypeBrakeToAccident, Accident.id == TypeBrakeToAccident.id_accident)
            .join(TypeBrake, TypeBrake.id == TypeBrakeToAccident.id_type_brake)
            .join(ClassBrake, ClassBrake.id == TypeBrake.id_type)
            .where(and_(*conditions))
            .group_by(
                month_expr,
                Object.uuid,
                Object.name,
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
                order_clauses.append(asc(Object.name))
            else:
                order_clauses.append(desc(Object.name))

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
            conditions.append(Object.uuid.in_(list_object))

        # Основной запрос для получения Claim, Accident, TypeBrake, ClassBrake
        query = (
            select(
                # Accident.id нужен для получения equipment и signs (скрытое поле)
                Accident.id.label("accident_id"),
                # Claim поля (исключаем: state_claim, main_document, edit_document, comment, last_datetime_edit, id, uuid)
                Claim.datetime.label("claim_datetime"),
                # User из Claim
                User.name.label("user_name"),
                User.surname.label("user_surname"),
                User.patronymic.label("user_patronymic"),
                User.email.label("user_email"),
                # Accident поля (исключаем: time_line, event, state_accident, time_zone, id, uuid)
                Accident.datetime_start.label("accident_datetime_start"),
                Accident.datetime_end.label("accident_datetime_end"),
                Accident.causes_of_the_emergency.label("accident_causes"),
                Accident.damaged_equipment_material.label("accident_damaged_equipment"),
                Accident.additional_material.label("accident_additional_material"),
                Accident.is_delite.label("accident_is_deleted"),
                # Object из Accident (только имя, без uuid)
                Object.name.label("object_name"),
                # TypeBrake поля (исключаем: id)
                TypeBrake.code.label("type_brake_code"),
                TypeBrake.name.label("type_brake_name"),
                # ClassBrake поля (исключаем: id, name)
                ClassBrake.description.label("class_brake_description"),
            )
            .select_from(Claim)
            .join(Accident, Claim.id_accident == Accident.id)
            .join(Object, Accident.id_object == Object.id)
            .join(StateClaim, Claim.id_state_claim == StateClaim.id)
            .join(User, Claim.id_user == User.id)
            .join(TypeBrakeToAccident, Accident.id == TypeBrakeToAccident.id_accident)
            .join(TypeBrake, TypeBrake.id == TypeBrakeToAccident.id_type_brake)
            .join(ClassBrake, ClassBrake.id == TypeBrake.id_type)
            .where(and_(*conditions))
            .order_by(Claim.datetime.desc())
        )

        result = await self.__session.execute(query)
        return result.fetchall()

    async def get_accident_equipment(self, accident_id: int):
        """Получение списка оборудования для аварии"""
        query = (
            select(Equipment.name.label("equipment_name"))
            .select_from(Equipment)
            .join(EquipmentToAccident, Equipment.id == EquipmentToAccident.id_equipment)
            .where(EquipmentToAccident.id_accident == accident_id)
        )
        result = await self.__session.execute(query)
        return [row.equipment_name for row in result.fetchall()]

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