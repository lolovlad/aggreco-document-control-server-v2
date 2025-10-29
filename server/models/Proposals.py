from pydantic import BaseModel, UUID4, field_serializer

from datetime import datetime

from .User import UserGet
from .Claim import StateClaimModel
from .Object import GetObject


class BaseTechnicalProposals(BaseModel):
    name: str | None
    offer: str | None
    additional_material: str | None
    comment: str | None


class GetTechnicalProposals(BaseTechnicalProposals):
    uuid: UUID4

    id_state_claim: int
    state_claim: StateClaimModel
    user: UserGet
    expert: UserGet | None
    object: GetObject

    @field_serializer("uuid")
    def serialize_uuid(self, uuid: UUID4, _info):
        return str(uuid)


class PostTechnicalProposals(BaseTechnicalProposals):
    uuid_object: str


class UpdateTechnicalProposals(BaseTechnicalProposals):
    is_agree: bool

