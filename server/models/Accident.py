from pydantic import BaseModel, UUID4, field_serializer

from datetime import datetime
from .Object import GetObject
from .Equipment import GetEquipment
from .Event import GetEvent


class ClassBrake(BaseModel):
    id: int
    name: str
    description: str | None


class BaseTypeBrake(BaseModel):
    id: int
    name: str
    code: str
    id_type: int


class GetTypeBrake(BaseTypeBrake):
    type: ClassBrake


class PostTypeBrake(BaseTypeBrake):
    pass


class BaseAccident(BaseModel):
    id_object: int
    datetime_start: datetime
    datetime_end: datetime | None
    additional_material: str | None


class GetLightweightAccident(BaseAccident):
    uuid: UUID4
    object: GetObject

    damaged_equipment: list[GetEquipment]

    @field_serializer("uuid")
    def serialize_uuid(self, uuid: UUID4, _info):
        return str(uuid)


class GetAccident(GetLightweightAccident):

    type_brakes: list[GetTypeBrake]

    time_line: dict

    causes_of_the_emergency: str
    damaged_equipment_material: str
    event: list[GetEvent]

    @field_serializer("time_line")
    def serialize_time_line(self, time_line: dict, _info):
        time_line_series = [
            TimeLine.model_validate({
                "uuid": i[0],
                "time": i[1]["time"],
                "description": i[1]["description"]
            }) for i in time_line.items()
        ]

        sorted(time_line_series, key=lambda x: x.time)

        return time_line_series


class PostAccident(BaseModel):
    object: str
    datetime_start: datetime
    datetime_end: datetime | None
    equipments: list[str]


class UpdateAccident(BaseModel):
    uuid_object: str
    datetime_start: datetime
    datetime_end: datetime | None
    equipments: list[str]
    type_brakes: list[int] | None
    causes_of_the_emergency: str
    damaged_equipment_material: str
    additional_material: str


class TimeLine(BaseModel):
    uuid: str | None
    description: str
    time: datetime



