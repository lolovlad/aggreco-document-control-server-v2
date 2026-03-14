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
            entities = await self.__proposals_repo.get_limit(
                str(user.uuid),
                uuid_object,
                id_state_claim,
                start,
                self.__count_item,
            )
        else:
            entities = await self.__proposals_repo.get_limit_admin(
                uuid_object,
                start,
                self.__count_item,
            )

        # Собираем UUID пользователей и экспертов из заявок
        user_uuid_set: set[str] = set()
        expert_uuid_set: set[str] = set()
        for entity in entities:
            if entity.user_uuid is not None:
                user_uuid_set.add(str(entity.user_uuid))
            if entity.expert_uuid is not None:
                expert_uuid_set.add(str(entity.expert_uuid))

        # Загружаем пользователей и экспертов из микросервиса
        all_uuids = list(user_uuid_set.union(expert_uuid_set))
        users = await self.__user_repo.get_users_by_uuids(all_uuids)
        users_by_uuid = {str(u.uuid): u for u in users}

        result: list[GetTechnicalProposals] = []
        for entity in entities:
            user_uuid_str = str(entity.user_uuid) if entity.user_uuid is not None else None
            expert_uuid_str = str(entity.expert_uuid) if entity.expert_uuid is not None else None

            user_model = users_by_uuid.get(user_uuid_str) if user_uuid_str is not None else None
            expert_model = users_by_uuid.get(expert_uuid_str) if expert_uuid_str is not None else None

            if user_model is None:
                raise ValueError(f"Пользователь с UUID {user_uuid_str} не найден в микросервисе")

            state_claim_model = StateClaimModel(
                id=entity.state_claim.id,
                name=entity.state_claim.name,
                description=entity.state_claim.description,
            )

            object_model = await self.__object_repo.get_by_uuid(str(entity.uuid_object)) if entity.uuid_object else None

            result.append(
                GetTechnicalProposals(
                    uuid=entity.uuid,
                    name=entity.name,
                    offer=entity.offer,
                    additional_material=entity.additional_material,
                    comment=entity.comment,
                    id_state_claim=entity.id_state_claim,
                    state_claim=state_claim_model,
                    user=user_model,
                    expert=expert_model,
                    object=object_model,
                )
            )

        return result

    async def add(self,
                  user: UserGet,
                  model: PostTechnicalProposals):

        state_claim = await self.__claim_repo.get_state_claim_by_name("under_consideration")

        entity = TechnicalProposals(
            id_state_claim=state_claim.id,
            uuid_object=model.uuid_object,
            user_uuid=user.uuid,
            offer=model.offer,
            additional_material=model.additional_material,
            name=model.name,
        )
        await self.__proposals_repo.add(entity)

        user_model = await self.__user_repo.get_user_by_uuid(str(user.uuid))
        if user_model is None:
            raise ValueError(f"Пользователь с UUID {user.uuid} не найден в микросервисе")

        state_claim_model = StateClaimModel(
            id=entity.state_claim.id,
            name=entity.state_claim.name,
            description=entity.state_claim.description,
        )
        object_resp = await self.__object_repo.get_by_uuid(model.uuid_object)

        return GetTechnicalProposals(
            uuid=entity.uuid,
            name=entity.name,
            offer=entity.offer,
            additional_material=entity.additional_material,
            comment=entity.comment,
            id_state_claim=entity.id_state_claim,
            state_claim=state_claim_model,
            user=user_model,
            expert=None,
            object=object_resp,
        )

    async def get(self, uuid_entity: str) -> GetTechnicalProposals | None:
        entity = await self.__proposals_repo.get_by_uuid(uuid_entity)
        if entity is None:
            return None
        # Подгружаем пользователя и эксперта из микросервиса
        user_uuid_str = str(entity.user_uuid) if entity.user_uuid is not None else None
        expert_uuid_str = str(entity.expert_uuid) if entity.expert_uuid is not None else None

        all_uuids = [u for u in [user_uuid_str, expert_uuid_str] if u is not None]
        users = await self.__user_repo.get_users_by_uuids(all_uuids)
        users_by_uuid = {str(u.uuid): u for u in users}

        user_model = users_by_uuid.get(user_uuid_str) if user_uuid_str is not None else None
        expert_model = users_by_uuid.get(expert_uuid_str) if expert_uuid_str is not None else None

        if user_model is None:
            raise ValueError(f"Пользователь с UUID {user_uuid_str} не найден в микросервисе")

        state_claim_model = StateClaimModel(
            id=entity.state_claim.id,
            name=entity.state_claim.name,
            description=entity.state_claim.description,
        )
        object_model = await self.__object_repo.get_by_uuid(str(entity.uuid_object)) if entity.uuid_object else None

        return GetTechnicalProposals(
            uuid=entity.uuid,
            name=entity.name,
            offer=entity.offer,
            additional_material=entity.additional_material,
            comment=entity.comment,
            id_state_claim=entity.id_state_claim,
            state_claim=state_claim_model,
            user=user_model,
            expert=expert_model,
            object=object_model,
        )

    async def delete(self, uuid: str):
        entity = await self.__proposals_repo.get_by_uuid(uuid)
        await self.__proposals_repo.delete(entity)

    async def update(self,
                     uuid_user: str,
                     uuid: str,
                     entity_model: UpdateTechnicalProposals):
        entity = await self.__proposals_repo.get_by_uuid(uuid)

        entity.expert_uuid = uuid_user
        entity.comment = entity_model.comment
        if entity_model.is_agree:
            state_claim_model = await self.__claim_repo.get_state_claim_by_name("accepted")
        else:
            state_claim_model = await self.__claim_repo.get_state_claim_by_name("under_development")
        entity.id_state_claim = state_claim_model.id

        await self.__proposals_repo.add(entity)
        return entity