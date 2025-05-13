from fastapi import Depends, UploadFile
from ..models.Accident import *
from ..models.Event import *
from ..models.User import UserGet
from ..tables import Accident, Event

from ..repositories import AccidentRepository, TypeBrakeRepository, ObjectRepository, EquipmentRepository, EventRepository

from uuid import uuid4

from urllib.parse import urlparse
from ..settings import settings

from pathlib import Path
from os import listdir, path, mkdir, remove
import aiofiles


class AccidentService:
    def __init__(self,
                 accident_repo: AccidentRepository = Depends(),
                 type_brake_repo: TypeBrakeRepository = Depends(),
                 object_repo: ObjectRepository = Depends(),
                 equipment_repo: EquipmentRepository = Depends(),
                 event_repo: EventRepository = Depends()):
        self.__accident_repo: AccidentRepository = accident_repo
        self.__type_brake_repo: TypeBrakeRepository = type_brake_repo
        self.__object_repo: ObjectRepository = object_repo
        self.__equipment_repo: EquipmentRepository = equipment_repo
        self.__event_repo: EventRepository = event_repo
        self.__count_item: int = 20

    @property
    def count_item(self) -> int:
        return self.__count_item

    @count_item.setter
    def count_item(self, item):
        self.__count_item = item

    async def get_count_page(self, uuid_object: str) -> int:
        count_row = await self.__accident_repo.count_row(uuid_object)
        sub_page = 0
        if count_row % self.__count_item > 0:
            sub_page += 1
        return count_row // self.__count_item + sub_page

    async def get_page_accident(self, uuid_object: str, num_page: int) -> list[GetLightweightAccident]:
        start = (num_page - 1) * self.__count_item
        entity = await self.__accident_repo.get_limit_accident(uuid_object, start, self.__count_item)
        accident = [GetLightweightAccident.model_validate(entity, from_attributes=True) for entity in entity]
        return accident

    async def add_accident(self, accident: PostAccident, time_zone: str) -> Accident:
        obj = await self.__object_repo.get_by_uuid(accident.object)
        equipments = await self.__equipment_repo.get_equipment_by_uuid_set(accident.equipments)

        state_accident = await self.__accident_repo.get_state_accident_by_name("empty")

        entity = Accident(
            id_object=obj.id,
            datetime_start=accident.datetime_start.replace(tzinfo=None),
            datetime_end=accident.datetime_end.replace(tzinfo=None) if accident.datetime_end is not None else None,
            time_line={},
            causes_of_the_emergency="Нет",
            damaged_equipment_material="Нет",
            additional_material="Нет",
            id_state_accident=state_accident.id,
            time_zone=time_zone
        )
        entity.damaged_equipment.extend(equipments)

        await self.__accident_repo.add(entity)
        return entity

    async def get_one(self, uuid_accident: str) -> GetAccident | None:
        entity = await self.__accident_repo.get_by_uuid(uuid_accident)
        if entity is None:
            return None
        return GetAccident.model_validate(entity, from_attributes=True)

    async def update_accident(self,
                              uuid_accident: str,
                              target: UpdateAccident,
                              user: UserGet,
                              state_accident: str | None = "empty"):

        entity = await self.__accident_repo.get_by_uuid(uuid_accident)
        entity.damaged_equipment = []
        entity.type_brakes = []
        entity.signs_accident = []
        await self.__accident_repo.update(entity)

        object = await self.__object_repo.get_by_uuid(target.uuid_object)
        equipments = await self.__equipment_repo.get_equipment_by_uuid_set(target.equipments)
        types_brake = await self.__type_brake_repo.get_brakes_by_uuid_set(target.type_brakes)
        signs_accident = await self.__accident_repo.get_signs_accident_by_id_set(target.signs_accident)

        if user.type.name == "admin":
            state_accident_obj = await self.__accident_repo.get_state_accident_by_name("empty")
            if len(types_brake) > 0:
                state_accident_obj = await self.__accident_repo.get_state_accident_by_name("accepted")
        else:
            state_accident_obj = await self.__accident_repo.get_state_accident_by_name("empty")

        entity.id_object = object.id
        entity.damaged_equipment = equipments
        entity.datetime_start = target.datetime_start.replace(tzinfo=None)
        entity.datetime_end = target.datetime_end.replace(tzinfo=None) if target.datetime_end is not None else None
        entity.type_brakes = types_brake
        entity.causes_of_the_emergency = target.causes_of_the_emergency
        entity.damaged_equipment_material = target.damaged_equipment_material
        entity.additional_material = target.additional_material
        entity.id_state_accident = state_accident_obj.id
        entity.signs_accident = signs_accident

        await self.__accident_repo.update(entity)

    def __convert_time_line(self, target: dict) -> list[TimeLine]:
        time_line_series = [
            TimeLine.model_validate({
                "uuid": i[0],
                "time": i[1]["time"],
                "description": i[1]["description"]
            }) for i in target.items()
        ]

        time_line_series = list(sorted(time_line_series, key=lambda x: x.time))

        return time_line_series

    async def add_time_line(self, uuid_accident: str, target: TimeLine) -> list[TimeLine]:
        accident = await self.__accident_repo.get_by_uuid(uuid_accident)

        target.time = target.time.replace(tzinfo=None)

        tm = accident.time_line

        tm[str(uuid4())] = {
            "time": target.time.isoformat(),
            "description": target.description
        }

        accident.time_line = tm

        await self.__accident_repo.update(accident)

        time_line_series = self.__convert_time_line(accident.time_line)

        return time_line_series

    async def get_time_line(self, uuid_accident) -> list[TimeLine] | None:
        accident = await self.__accident_repo.get_by_uuid(uuid_accident)
        if accident is None:
            return None
        time_line_series = self.__convert_time_line(accident.time_line)
        return time_line_series

    async def update_time_line(self, uuid: str, target: TimeLine) -> list[TimeLine]:
        accident = await self.__accident_repo.get_by_uuid(uuid)
        target.time = target.time.replace(tzinfo=None)
        tm = accident.time_line

        tm[target.uuid] = {
            "time": target.time.isoformat(),
            "description": target.description
        }

        accident.time_line = tm

        await self.__accident_repo.update(accident)

        time_line_series = self.__convert_time_line(accident.time_line)

        return time_line_series

    async def delete_time_line(self, uuid: str, uuid_time_line: str) -> list[TimeLine]:
        accident = await self.__accident_repo.get_by_uuid(uuid)

        tm = accident.time_line

        del tm[uuid_time_line]

        accident.time_line = tm

        await self.__accident_repo.update(accident)
        time_line_series = self.__convert_time_line(accident.time_line)
        return time_line_series

    async def get_list_event(self, uuid: str) -> list[GetEvent] | None:
        entities = await self.__event_repo.get_all_event_by_uuid_accident(uuid)
        if entities is not None:
            return [GetEvent.model_validate(i, from_attributes=True) for i in entities]
        return entities

    async def get_one_event(self, uuid_event: str) -> GetEvent | None:
        entity = await self.__event_repo.get_by_uuid(uuid_event)
        if entity is not None:
            return GetEvent.model_validate(entity, from_attributes=True)
        return None

    async def add_event(self, uuid: str, target: PostEvent) -> list[GetEvent]:
        accident = await self.__accident_repo.get_by_uuid(uuid)
        entity = Event(
            description=target.description,
            date_finish=target.date_finish,
            id_accident=accident.id,
            id_state_event=target.id_state_event,
            id_type_event=target.id_type_event,
            responsible=target.responsible
        )

        await self.__event_repo.add(entity)

        list_event = await self.get_list_event(uuid)

        return list_event

    async def update_event(self, uuid: str, target: UpdateEvent) -> list[GetEvent]:
        entity = await self.__event_repo.get_by_uuid(target.uuid)

        dict_target = target.model_dump()

        for i in dict_target:
            setattr(entity, i, dict_target[i])

        await self.__event_repo.update(entity)

        list_event = await self.get_list_event(uuid)

        return list_event

    async def delete_event(self, uuid: str, uuid_event: str) -> list[GetEvent]:
        await self.__event_repo.delete(uuid_event)
        list_event = await self.get_list_event(uuid)

        return list_event

    async def get_file_accident(self, uuid_accident: str) -> list[FileAccident] | None:
        accident = await self.__accident_repo.get_by_uuid(uuid_accident)
        url_host = f"{settings.host_server}:{settings.port_server}"

        parsed_uri = urlparse(accident.additional_material)

        if url_host != parsed_uri.netloc:
            return None

        path_files = Path(settings.static_file, parsed_uri.path.split('/')[-1])

        files = listdir(path_files)

        return [FileAccident(path=str(path_files), name=i) for i in files]

    async def add_file_accident(self, uuid_accident: str, file: UploadFile):

        accident = await self.__accident_repo.get_by_uuid(uuid_accident)

        start_path = Path(Path(__path__).absolute(), settings.static_file, accident.object.name)
        if not path.isdir(Path(start_path)):
            mkdir(start_path)

        start_path = Path(start_path, uuid_accident)
        if not path.isdir(Path(start_path)):
            mkdir(start_path)

        start_path = Path(start_path, file.filename)
        async with aiofiles.open(start_path, 'wb') as out_file:
            while content := await file.read(1024):
                await out_file.write(content)

        accident.additional_material = f"https://{settings.host_server}:{settings.port_server}/accident/files/{uuid_accident}/download"

        await self.__accident_repo.update(accident)

    async def delete_file(self, uuid_accident: str, name_file: str):
        accident = await self.__accident_repo.get_by_uuid(uuid_accident)

        remove(Path(Path(__path__), settings.static_file, accident.object.name, uuid_accident, name_file))

    async def delete_accident(self, uuid_accident: str):
        accident = await self.__accident_repo.get_by_uuid(uuid_accident)
        accident.is_delite = True
        await self.__accident_repo.update(accident)
