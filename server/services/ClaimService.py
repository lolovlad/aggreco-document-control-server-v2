from fastapi import Depends, UploadFile
from ..models.Claim import *

from ..tables import StateClaim, Claim

from ..repositories import ClaimRepository, FileBucketRepository, UserRepository, AccidentRepository

from functools import partial

from datetime import datetime, timezone


class ClaimServices:
    def __init__(self,
                 claim_repo: ClaimRepository = Depends(),
                 user_repo: UserRepository = Depends(),
                 accident_repo: AccidentRepository = Depends()):
        self.__claim_repo: ClaimRepository = claim_repo
        self.__user_repo: UserRepository = user_repo
        self.__accident_repo: AccidentRepository = accident_repo
        self.__file_repo: FileBucketRepository = FileBucketRepository("document")

        self.__count_item: int = 20

    @property
    def count_item(self) -> int:
        return self.__count_item

    @count_item.setter
    def count_item(self, item):
        self.__count_item = item

    async def get_count_page(self,
                             uuid_user: str | None,
                             uuid_object: str,
                             id_state_claim: int) -> int:
        id_user = None
        if uuid_user:
            user = await self.__user_repo.get_user_by_uuid(uuid_user)
            id_user = user.id

        count_row = await self.__claim_repo.count_row(id_user, uuid_object, id_state_claim)
        sub_page = 0
        if count_row % self.__count_item > 0:
            sub_page += 1
        return count_row // self.__count_item + sub_page

    async def get_page_claim(self,
                             num_page: int,
                             user: UserGet,
                             uuid_object: str,
                             id_state_claim: int) -> list[GetClaim]:
        start = (num_page - 1) * self.__count_item

        if user.type.name == "user":
            user = await self.__user_repo.get_user_by_uuid(user.uuid)
            entity = await self.__claim_repo.get_limit_claim(user.id, uuid_object, id_state_claim, start, self.__count_item)
        else:
            entity = await self.__claim_repo.get_limit_claim_admin(uuid_object, id_state_claim, start, self.__count_item)
        claim = [GetClaim.model_validate(entity, from_attributes=True) for entity in entity]
        return claim

    async def add_claim(self,
                        uuid_user: str,
                        id_accident: int,
                        claim_model: PostClaim):

        state_claim = await self.__claim_repo.get_state_claim_by_name("draft")

        user = await self.__user_repo.get_user_by_uuid(uuid_user)

        entity = Claim(
            datetime=claim_model.datetime,
            id_state_claim=state_claim.id,
            id_user=user.id,
            main_document="Не представлен",
            edit_document="Не представлен",
            id_accident=id_accident
        )
        await self.__claim_repo.add(entity)

    async def get_claim(self, uuid_claim: str) -> GetClaim | None:
        entity = await self.__claim_repo.get_by_uuid(uuid_claim)
        if entity is None:
            return None
        return GetClaim.model_validate(entity, from_attributes=True)

    async def upload_file(self, type_file: str, uuid: str, file: UploadFile):
        ext = file.filename.split(".")[1]
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

    async def update_claim(self, uuid: str, claim_model: UpdateClaim):
        claim = await self.__claim_repo.get_by_uuid(uuid)

        claim.comment = claim_model.comment

        await self.__claim_repo.update(claim)