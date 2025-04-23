from pydantic import BaseModel, UUID4, field_serializer

from .User import UserGet


class PostTypeEquipment(BaseModel):
    name: str
    code: str
    description: str | None


class TypeEquipment(BaseModel):
    id: int
    name: str
    code: str
    description: str | None


class BaseEquipment(BaseModel):
    name: str
    id_type: int
    code: str | None
    description: str | None


class GetEquipment(BaseEquipment):
    uuid: UUID4
    type: TypeEquipment

    @field_serializer("uuid")
    def serialize_uuid(self, uuid: UUID4, _info):
        return str(uuid)


class PostEquipment(BaseEquipment):
    pass


class UpdateEquipment(BaseEquipment):
    pass
