from pydantic import BaseModel, UUID4, field_serializer
from datetime import datetime


class StateEvent(BaseModel):
    id: int
    name: str
    description: str | None


class TypeEvent(BaseModel):
    id: int
    name: str
    description: str | None


class BaseEvent(BaseModel):
    description: str
    date_finish: datetime
    id_state_event: int
    id_type_event: int


class GetEvent(BaseEvent):
    uuid: UUID4
    state_event: StateEvent
    type_event: TypeEvent

    @field_serializer("uuid")
    def serialize_uuid(self, uuid: UUID4, _info):
        return str(uuid)


class PostEvent(BaseEvent):
    pass


class UpdateEvent(BaseEvent):
    uuid: str
