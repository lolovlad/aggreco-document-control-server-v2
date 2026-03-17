from fastapi import Depends, UploadFile
from ..models.Claim import GetClaim, PostClaim, UpdateClaim, StateClaimModel
from ..models.Accident import GetAccident, StateAccidentModel, TimeLine, CodeErrorAccidentModel
from ..models.User import UserGet
from ..models.Event import GetEvent

from ..tables import StateClaim, Claim

from ..repositories import (
    ClaimRepository,
    FileBucketRepository,
    UserRepository,
    AccidentRepository,
    ObjectRepository,
    EquipmentRepository,
)

from functools import partial

from datetime import datetime, timezone


class ClaimServices:
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
        self.__file_repo: FileBucketRepository = FileBucketRepository("document")

        self.__count_item: int = 20

    async def _accident_orm_to_get_accident(self, accident_orm):
        """Собирает GetAccident из ORM-аварии, подгружая object и damaged_equipment из микросервиса."""
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
            from ..models.Accident import SignsAccident as SignsAccidentModel
            signs_accident = [
                SignsAccidentModel(id=s.id, name=s.name, code=s.code)
                for s in accident_orm.signs_accident
            ]

        type_brakes = []
        if accident_orm.type_brakes:
            from ..models.Accident import GetTypeBrake, ClassBrake
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

        return GetAccident(
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

    @property
    def count_item(self) -> int:
        return self.__count_item

    @count_item.setter
    def count_item(self, item):
        self.__count_item = item

    async def get_count_page(
        self,
        uuid_user: str | None,
        uuid_object: str,
        id_state_claim: int,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> int:
        count_row = await self.__claim_repo.count_row(
            uuid_user,
            uuid_object,
            id_state_claim,
            date_from,
            date_to,
        )
        sub_page = 0
        if count_row % self.__count_item > 0:
            sub_page += 1
        return count_row // self.__count_item + sub_page

    async def get_page_claim(self,
                             num_page: int,
                             user: UserGet,
                             uuid_object: str,
                             id_state_claim: int,
                             date_from: datetime | None = None,
                             date_to: datetime | None = None
                             ) -> list[GetClaim]:
        start = (num_page - 1) * self.__count_item

        if user.type.name == "user":
            entities = await self.__claim_repo.get_limit_claim(
                str(user.uuid),
                uuid_object,
                id_state_claim,
                start,
                self.__count_item,
                date_from,
                date_to,
            )
        else:
            entities = await self.__claim_repo.get_limit_claim_admin(
                uuid_object,
                id_state_claim,
                start,
                self.__count_item,
                date_from,
                date_to,
            )

        # Собираем UUID пользователей из заявок и подгружаем их из микросервиса
        user_uuid_set: set[str] = set()
        for entity in entities:
            if entity.user_uuid is not None:
                user_uuid_set.add(str(entity.user_uuid))

        users = await self.__user_repo.get_users_by_uuids(list(user_uuid_set))
        users_by_uuid = {str(u.uuid): u for u in users}

        claims: list[GetClaim] = []
        for entity in entities:
            user_uuid_str = str(entity.user_uuid) if entity.user_uuid is not None else None
            user_model = users_by_uuid.get(user_uuid_str) if user_uuid_str is not None else None

            if user_model is None:
                # Если пользователя не нашли в микросервисе – считаем это ошибкой данных
                raise ValueError(f"Пользователь с UUID {user_uuid_str} не найден в микросервисе")

            state_claim_model = StateClaimModel(
                id=entity.state_claim.id,
                name=entity.state_claim.name,
                description=entity.state_claim.description,
            )

            accident_model = await self._accident_orm_to_get_accident(entity.accident)

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

        return claims

    async def add_claim(self,
                        uuid_user: str,
                        id_accident: int,
                        claim_model: PostClaim):

        state_claim = await self.__claim_repo.get_state_claim_by_name("draft")

        entity = Claim(
            datetime=claim_model.datetime,
            id_state_claim=state_claim.id,
            user_uuid=uuid_user,
            main_document="Не представлен",
            edit_document="Не представлен",
            id_accident=id_accident
        )
        await self.__claim_repo.add(entity)

    async def get_claim(self, uuid_claim: str) -> GetClaim | None:
        entity = await self.__claim_repo.get_by_uuid(uuid_claim)
        if entity is None:
            return None

        # Подгружаем пользователя по UUID из микросервиса
        user_uuid_str = str(entity.user_uuid) if entity.user_uuid is not None else None
        user_model = await self.__user_repo.get_user_by_uuid(user_uuid_str) if user_uuid_str is not None else None
        if user_model is None:
            raise ValueError(f"Пользователь с UUID {user_uuid_str} не найден в микросервисе")

        state_claim_model = StateClaimModel(
            id=entity.state_claim.id,
            name=entity.state_claim.name,
            description=entity.state_claim.description,
        )

        accident_model = await self._accident_orm_to_get_accident(entity.accident)

        return GetClaim(
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

    async def upload_file(self, type_file: str, uuid: str, file: UploadFile):
        ext = file.filename.split(".")[-1]
        dir_name = f"{uuid}"

        file_key = f"{dir_name}/{type_file}_file.{ext}"

        try:
            await self.__file_repo.delete_file(file_key)
        except Exception:
            pass

        claim = await self.__claim_repo.get_by_uuid(uuid)
        if type_file == "main":
            claim.main_document = file_key
        else:
            claim.edit_document = file_key

        content = await file.read()
        await self.__file_repo.upload_file(file_key,
                                           content,
                                           file.content_type)

        await self.__claim_repo.update(claim)

    async def get_file(self, type_file, uuid: str):
        claim = await self.__claim_repo.get_by_uuid(uuid)
        if type_file == "main":
            file_path = claim.main_document
        else:
            file_path = claim.edit_document

        if file_path is not None:
            file_name = file_path.split("/")[-1]

            info = await self.__file_repo.get_sate(file_path)

            file = partial(self.__file_repo.get_file_stream,file_name, info)
            return file, file_path
        else:
            return None, None

    async def delete_claim(self, uuid: str, user: UserGet):
        claim = await self.__claim_repo.get_by_uuid(uuid)
        if (user.type.name in ("admin", "super_admin")) or (user.type.name == "user" and claim.state_claim.name == "draft"):
            if claim.edit_document is not None:
                await self.__file_repo.delete_object(claim.edit_document)

            if claim.main_document is not None:
                await self.__file_repo.delete_object(claim.main_document)

            await self.__claim_repo.delete(claim)
        else:
            raise Exception

    async def update_state_claim(self,
                                 uuid_claim: str,
                                 state_claim: str,
                                 user: UserGet):
        claim = await self.__claim_repo.get_by_uuid(uuid_claim)
        accident = await self.__accident_repo.get_by_uuid(claim.accident.uuid)
        if user.type.name == "user":
            if claim.state_claim.name in ("draft", "under_development"):
                state_claim_model = await self.__claim_repo.get_state_claim_by_name("under_consideration")
                state_accident = await self.__accident_repo.get_state_accident_by_name("pending")
                claim.id_state_claim = state_claim_model.id
                accident.id_state_accident = state_accident.id
            elif claim.state_claim.name == "under_consideration":
                time_delta = datetime.now(timezone.utc) - claim.datetime
                if time_delta.seconds <= 24 * 60 * 60:
                    state_claim_model = await self.__claim_repo.get_state_claim_by_name("draft")
                    claim.id_state_claim = state_claim_model.id
                else:
                    raise Exception

        elif user.type.name in ("admin", "super_admin"):
            if claim.state_claim.name == "under_consideration":
                if state_claim == "accepted":
                    state_claim_model = await self.__claim_repo.get_state_claim_by_name("accepted")
                    state_accident = await self.__accident_repo.get_state_accident_by_name("accepted")
                    accident.id_state_accident = state_accident.id
                else:
                    state_claim_model = await self.__claim_repo.get_state_claim_by_name("under_development")
                claim.id_state_claim = state_claim_model.id

        await self.__claim_repo.update(claim)
        await self.__accident_repo.update(accident)
        return claim

    async def update_claim(self, uuid: str, claim_model: UpdateClaim):
        claim = await self.__claim_repo.get_by_uuid(uuid)

        claim.comment = claim_model.comment

        await self.__claim_repo.update(claim)