from pydantic import BaseModel, UUID4, field_serializer

from datetime import datetime, timedelta, timezone
import pytz
from .Object import GetObject
from .Equipment import GetEquipment, TypeEquipment
from .Event import GetEvent


class StateAccidentModel(BaseModel):
    id: int
    name: str
    description: str | None


class ClassBrake(BaseModel):
    id: int
    name: str
    description: str | None


class SignsAccident(BaseModel):
    id: int
    name: str
    code: str


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
    id_state_accident: int | None
    datetime_start: datetime
    datetime_end: datetime | None
    additional_material: str | None
    time_zone: str | None

    @field_serializer("datetime_start")
    def serialize_datetime_start(self, dt: datetime, _info):

        self.datetime_start = self.datetime_start
        if self.datetime_end is not None:
            self.datetime_end = self.datetime_end

        return self.datetime_start.isoformat()


class GetLightweightAccident(BaseAccident):
    uuid: UUID4
    object: GetObject
    state_accident: StateAccidentModel | None
    signs_accident: list[SignsAccident] | None

    damaged_equipment: list[GetEquipment]

    @field_serializer("uuid")
    def serialize_uuid(self, uuid: UUID4, _info):
        return str(uuid)

    def get_unique_type_damaged_equipment(self) -> list[TypeEquipment]:
        sets = {}
        for i in self.damaged_equipment:
            sets[i.type.code] = i.type
        return list(sets.values())


class GetAccident(GetLightweightAccident):

    type_brakes: list[GetTypeBrake]
    signs_accident: list[SignsAccident]

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
    id_state_accident: int | None = 1


class UpdateAccident(BaseModel):
    uuid_object: str
    datetime_start: datetime
    datetime_end: datetime | None
    equipments: list[str]
    type_brakes: list[int] | None
    signs_accident: list[int] | None

    causes_of_the_emergency: str
    damaged_equipment_material: str
    additional_material: str | None
    id_state_accident: int | None


class TimeLine(BaseModel):
    uuid: str | None
    description: str
    time: datetime


class FileAccident(BaseModel):
    path: str
    name: str
