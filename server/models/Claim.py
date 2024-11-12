from pydantic import BaseModel, UUID4, field_serializer

from datetime import datetime

from .Accident import PostAccident, GetAccident
from .User import UserGet


class StateClaimModel(BaseModel):
    id: int
    name: str
    description: str | None


class BaseClaim(BaseModel):
    datetime: datetime
    main_document: str | None
    edit_document: str | None
    comment: str | None


class GetClaim(BaseClaim):
    uuid: UUID4

    id_state_claim: int
    state_claim: StateClaimModel
    user: UserGet
    accident: GetAccident

    @field_serializer("uuid")
    def serialize_uuid(self, uuid: UUID4, _info):
        return str(uuid)


class PostClaim(BaseClaim):
    accident: PostAccident


class UpdateClaim(BaseModel):
    comment: str | None
