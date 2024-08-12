from pydantic import BaseModel, UUID4, field_serializer

from .User import UserGet


class StateObject(BaseModel):
    id: int
    name: str
    description: str


class BaseObject(BaseModel):
    name: str
    address: str
    cx: float | None = 0.0
    cy: float | None = 0.0
    counterparty: str
    id_state: int
    description: str | None


class GetObject(BaseObject):
    uuid: UUID4
    state: StateObject

    @field_serializer("uuid")
    def serialize_uuid(self, uuid: UUID4, _info):
        return str(uuid)


class PostObject(BaseObject):
    pass


class UpdateObject(BaseObject):
    pass
