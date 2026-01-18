from pydantic import BaseModel, UUID4, field_serializer
from datetime import datetime


class BaseLogMessageError(BaseModel):
    message: str
    class_log_text: str
    class_log_int: int
    entity_equipment: str | None
    number_equipment: int | None
    create_at: datetime


class GetLogMessageError(BaseLogMessageError):
    uuid: UUID4
    id_object: int
    id_equipment: int | None
    is_processed: bool

    @field_serializer("uuid")
    def serialize_uuid(self, uuid: UUID4, _info):
        return str(uuid)


class PostLogMessageError(BaseLogMessageError):
    id_object: int
    id_equipment: int | None
    is_processed: bool = False
