from fastapi import Depends

from datetime import datetime
from io import BytesIO

import pandas as pd

from ..repositories import (
    ClaimRepository,
    UserRepository,
    AccidentRepository,
    ObjectRepository,
    EquipmentRepository,
)
from ..models.Claim import StateClaimModel, GetClaim
from ..models.Event import GetEvent
from ..models.Accident import (
    StateAccidentModel,
    CodeErrorAccidentModel,
)


class ReportService:
    """
    Формирование отчёта по авариям в формате Excel по заданному диапазону дат.
    Вся информация берётся из заявок (Claim) и связанных сущностей.
    """

    def __init__(
        self,
        claim_repo: ClaimRepository = Depends(),
        user_repo: UserRepository = Depends(),
        accident_repo: AccidentRepository = Depends(),
        object_repo: ObjectRepository = Depends(),
        equipment_repo: EquipmentRepository = Depends(),
    ):
        self.__claim_repo: ClaimRepository = claim_repo
        self.__user_repo: UserRepository = user_repo
        self.__accident_repo: AccidentRepository = accident_repo
        self.__object_repo: ObjectRepository = object_repo
        self.__equipment_repo: EquipmentRepository = equipment_repo

    async def build_month_report(
        self,
        date_from: datetime,
        date_to: datetime,
    ) -> BytesIO:
        """
        Формирует Excel-отчёт по заявкам/авариям за заданный период.
        """
        # Берём все заявки по всем объектам и любым статусам за период
        entities = await self.__claim_repo.get_limit_claim_admin(
            uuid_object="all",
            id_state_claim=0,
            start=0,
            count=10_000_000,
            date_from=date_from,
            date_to=date_to,
        )

        # Собираем UUID пользователей и подгружаем их
        user_uuid_set: set[str] = set()
        for entity in entities:
            if entity.user_uuid is not None:
                user_uuid_set.add(str(entity.user_uuid))

        users = await self.__user_repo.get_users_by_uuids(list(user_uuid_set))
        users_by_uuid = {str(u.uuid): u for u in users}

        claims: list[GetClaim] = []
        from ..models.Accident import SignsAccident as SignsAccidentModel, GetTypeBrake, ClassBrake, GetAccident

        for entity in entities:
            user_uuid_str = str(entity.user_uuid) if entity.user_uuid is not None else None
            user_model = users_by_uuid.get(user_uuid_str) if user_uuid_str is not None else None
            if user_model is None:
                continue

            state_claim_model = StateClaimModel(
                id=entity.state_claim.id,
                name=entity.state_claim.name,
                description=entity.state_claim.description,
            )

            accident_orm = entity.accident
            uuid_object = str(accident_orm.uuid_object) if accident_orm.uuid_object else ""
            object_model = await self.__object_repo.get_by_uuid(uuid_object) if uuid_object else None

            equipment_uuids = [
                str(e.uuid_equipment)
                for e in (accident_orm.damaged_equipment or [])
                if getattr(e, "uuid_equipment", None)
            ]
            damaged_equipment = (
                await self.__equipment_repo.get_equipment_by_uuid_set(equipment_uuids)
                if equipment_uuids
                else []
            )

            state_accident = None
            if accident_orm.state_accident:
                state_accident = StateAccidentModel(
                    id=accident_orm.state_accident.id,
                    name=accident_orm.state_accident.name,
                    description=accident_orm.state_accident.description,
                )

            signs_accident = None
            if accident_orm.signs_accident:
                signs_accident = [
                    SignsAccidentModel(id=s.id, name=s.name, code=s.code)
                    for s in accident_orm.signs_accident
                ]

            type_brakes = []
            if accident_orm.type_brakes:
                type_brakes = [
                    GetTypeBrake(
                        id=tb.id,
                        name=tb.name,
                        code=tb.code,
                        id_type=tb.id_type,
                        type=ClassBrake(
                            id=tb.type.id,
                            name=tb.type.name,
                            description=tb.type.description,
                        ),
                    )
                    for tb in accident_orm.type_brakes
                ]

            events = []
            if getattr(accident_orm, "event", None):
                events = [GetEvent.model_validate(e, from_attributes=True) for e in accident_orm.event]

            error_code = None
            if getattr(accident_orm, "error_code_accident", None):
                error_code = CodeErrorAccidentModel(
                    id=accident_orm.error_code_accident.id,
                    name=accident_orm.error_code_accident.name,
                    description=accident_orm.error_code_accident.description,
                )

            accident_model = GetAccident(
                uuid=accident_orm.uuid,
                uuid_object=uuid_object,
                object=object_model,
                state_accident=state_accident,
                signs_accident=signs_accident or [],
                damaged_equipment=damaged_equipment,
                type_brakes=type_brakes,
                error_code_accident=error_code,
                time_line=accident_orm.time_line or {},
                causes_of_the_emergency=accident_orm.causes_of_the_emergency or "",
                reason_for_shutdown=accident_orm.reason_for_shutdown,
                damaged_equipment_material=accident_orm.damaged_equipment_material or "",
                event=events,
                id_state_accident=accident_orm.id_state_accident,
                datetime_start=accident_orm.datetime_start,
                datetime_end=accident_orm.datetime_end,
                additional_material=accident_orm.additional_material,
                time_zone=accident_orm.time_zone,
            )

            claims.append(
                GetClaim(
                    uuid=entity.uuid,
                    datetime=entity.datetime,
                    main_document=entity.main_document,
                    edit_document=entity.edit_document,
                    comment=entity.comment,
                    id_state_claim=entity.id_state_claim,
                    state_claim=state_claim_model,
                    user=user_model,
                    accident=accident_model,
                )
            )

        rows = []
        for idx, claim in enumerate(claims, start=1):
            a = claim.accident

            start_dt = a.datetime_start
            end_dt = a.datetime_end

            object_name = a.object.name if a.object is not None else ""

            equipment_names = []
            for eq in a.damaged_equipment or []:
                if getattr(eq, "name", None):
                    equipment_names.append(eq.name)
            equipment_str = ", ".join(sorted(set(equipment_names))) if equipment_names else ""

            # Дата в формате России dd.mm.yyyy
            start_date_str = start_dt.strftime("%d.%m.%Y") if start_dt else ""
            end_date_str = end_dt.strftime("%d.%m.%Y") if end_dt else ""

            # Время отключения/включения и простой в формате Ч:ММ
            if start_dt:
                shutdown_time_str = start_dt.strftime("%H:%M")
            else:
                shutdown_time_str = ""

            if end_dt:
                startup_time_str = end_dt.strftime("%H:%M")
            else:
                startup_time_str = ""

            downtime_str = ""
            if start_dt and end_dt:
                delta = end_dt - start_dt
                total_minutes = int(delta.total_seconds() // 60)
                hours = total_minutes // 60
                minutes = total_minutes % 60
                downtime_str = f"{hours}:{minutes:02d}"

            timezone = a.time_zone

            error_code = a.error_code_accident.name if a.error_code_accident else ""

            protection_system = ""

            reason = a.reason_for_shutdown or ""

            # Ответственный: только ФИО пользователя (email не подставляем)
            fio_parts = [claim.user.surname, claim.user.name, claim.user.patronymic]
            responsible_person = " ".join([p for p in fio_parts if p]) or ""

            loss_costs = None
            penalties = None

            notes = a.additional_material if a.additional_material not in (None, "Нет") else ""

            rows.append(
                {
                    "№ п/п": idx,
                    "Дата начала АО": start_date_str,
                    "Дата окончания АО": end_date_str,
                    "Объект": object_name,
                    "Оборудование": equipment_str,
                    "Наименование отключившегося оборудования, краткое описание аварийной ситуации": "",
                    "Время отключения (ч:мм)": shutdown_time_str,
                    "Время включения (ч:мм)": startup_time_str,
                    "Часовой пояс": timezone,
                    "Время простоя (ч:мм)": downtime_str,
                    "Код ошибки": error_code,
                    "Работа РЗиА": protection_system,
                    "Причина отключения": reason,
                    "Ответственный за предоставление информации по мероприятиям": responsible_person,
                    "Затраты связанные с потерей выработки": loss_costs,
                    "Штрафы": penalties,
                }
            )

        df = pd.DataFrame(
            rows,
            columns=[
                "№ п/п",
                "Дата начала АО",
                "Дата окончания АО",
                "Объект",
                "Оборудование",
                "Наименование отключившегося оборудования, краткое описание аварийной ситуации",
                "Время отключения (ч:мм)",
                "Время включения (ч:мм)",
                "Часовой пояс",
                "Время простоя (ч:мм)",
                "Код ошибки",
                "Работа РЗиА",
                "Причина отключения",
                "Ответственный за предоставление информации по мероприятиям",
                "Затраты связанные с потерей выработки",
                "Штрафы",
            ],
        )

        output = BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False, sheet_name="january_incidents")
        output.seek(0)

        return output

