from fastapi import Depends

from ..models.Proposals import *
from ..tables import TechnicalProposals
from ..repositories import (ClaimRepository,
                            ProposalsRepository,
                            UserRepository,
                            ObjectRepository)


class ProposalsService:
    def __init__(self,
                 claim_repo: ClaimRepository = Depends(),
                 proposals_repo: ProposalsRepository = Depends(),
                 user_repo: UserRepository = Depends(),
                 object_repo: ObjectRepository = Depends()):
        self.__claim_repo: ClaimRepository = claim_repo
        self.__proposals_repo: ProposalsRepository = proposals_repo
        self.__user_repo: UserRepository = user_repo
        self.__object_repo: ObjectRepository = object_repo

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
                             id_state_claim: int,
                             ) -> int:
        count_row = await self.__proposals_repo.count_row(uuid_user,
                                                          uuid_object,
                                                          id_state_claim)
        sub_page = 0
        if count_row % self.__count_item > 0:
            sub_page += 1
        return count_row // self.__count_item + sub_page

    async def get_page(self,
                       num_page: int,
                       user: UserGet,
                       uuid_object: str,
                       id_state_claim: int,
                       ) -> list[GetTechnicalProposals]:
        start = (num_page - 1) * self.__count_item

        if user.type.name == "user":
            entity = await self.__proposals_repo.get_limit(user.uuid,
                                                           uuid_object,
                                                           id_state_claim,
                                                           start,
                                                           self.__count_item)
        else:
            entity = await self.__proposals_repo.get_limit_admin(uuid_object,
                                                                 start,
                                                                 self.__count_item,)
        entity_model = [GetTechnicalProposals.model_validate(entity, from_attributes=True) for entity in entity]
        return entity_model

    async def add(self,
                  user: UserGet,
                  model: PostTechnicalProposals):

        state_claim = await self.__claim_repo.get_state_claim_by_name("under_consideration")
        user = await self.__user_repo.get_user_by_uuid(user.uuid)
        object_model = await self.__object_repo.get_by_uuid(model.uuid_object)

        entity = TechnicalProposals(
            id_state_claim=state_claim.id,
            id_object=object_model.id,
            id_user=user.id,
            offer=model.offer,
            additional_material=model.additional_material,
            name=model.name
        )
        await self.__proposals_repo.add(entity)
        return GetTechnicalProposals.model_validate(entity, from_attributes=True)

    async def get(self, uuid_entity: str) -> GetTechnicalProposals | None:
        entity = await self.__proposals_repo.get_by_uuid(uuid_entity)
        if entity is None:
            return None
        return GetTechnicalProposals.model_validate(entity, from_attributes=True)

    async def delete(self, uuid: str):
        entity = await self.__proposals_repo.get_by_uuid(uuid)
        await self.__proposals_repo.delete(entity)

    async def update(self,
                     uuid_user: str,
                     uuid: str,
                     entity_model: UpdateTechnicalProposals):
        entity = await self.__proposals_repo.get_by_uuid(uuid)
        user = await self.__user_repo.get_user_by_uuid(uuid_user)

        entity.id_expert = user.id
        entity.comment = entity_model.comment
        if entity_model.is_agree:
            state_claim_model = await self.__claim_repo.get_state_claim_by_name("accepted")
        else:
            state_claim_model = await self.__claim_repo.get_state_claim_by_name("under_development")
        entity.id_state_claim = state_claim_model.id

        await self.__proposals_repo.add(entity)
        return entity