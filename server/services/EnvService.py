from fastapi import Depends, UploadFile

from ..models.User import GetTypeUser, Profession
from ..models.Equipment import TypeEquipment, PostTypeEquipment
from ..models.Object import StateObject, Region
from ..models.Accident import GetTypeBrake, SignsAccident
from ..models.Event import TypeEvent, StateEvent
from ..models.Claim import StateClaimModel

from ..tables import (Profession as ProfessionORM,
                      TypeEquipment as TypeEquipmentORM,
                      Region as RegionORM,
                      TypeBrake as TypeBrakeORM,
                      SignsAccident as SignsAccidentORM)

from ..repositories import EnvRepository, TypeBrakeRepository

from io import StringIO
import csv


class EnvService:
    def __init__(self,
                 env_repo: EnvRepository = Depends(),
                 type_brake: TypeBrakeRepository = Depends()):
        self.__env_repo: EnvRepository = env_repo
        self.__type_brake_repo: TypeBrakeRepository = type_brake

    async def get_type_users(self) -> list[GetTypeUser]:
        type_users = await self.__env_repo.get_all_type_user()
        return [GetTypeUser.model_validate(obj, from_attributes=True) for obj in type_users]

    async def add_profession(self, name: str, description: str) -> ProfessionORM:
        entity = ProfessionORM(name=name, description=description)
        prof = await self.__env_repo.add_prof_user(entity)
        if prof is None:
            prof = await self.__env_repo.get_prof_by_name(name)
        return prof

    async def get_profession_user(self) -> list[Profession]:
        prof_users = await self.__env_repo.get_all_prof_user()
        return [Profession.model_validate(obj, from_attributes=True) for obj in prof_users]

    async def delete_prof(self, id_prof: int) -> bool:
        is_del = await self.__env_repo.delete_prof(id_prof)
        return is_del

    async def delete_type_equipment(self, id_type_equipment: int) -> bool:
        is_del = await self.__env_repo.delete_type_equipment(id_type_equipment)
        return is_del

    async def import_type_equip_file(self, file: UploadFile):
        try:
            type_equipments = []
            while contents := await file.read(1024 * 1024):
                buffer = StringIO(contents.decode('utf-8-sig'))
                csv_reader = csv.DictReader(buffer, delimiter=';')

                for rows in csv_reader:

                    type_equipment = TypeEquipmentORM(
                        code=rows["code"],
                        name=rows["name"],
                    )
                    type_equipments.append(type_equipment)

                await self.__env_repo.add_list_type_equipment(type_equipments)

        except Exception:
            raise Exception()
        finally:
            await file.close()

    async def get_all_type_equip(self) -> list[TypeEquipment]:
        entity = await self.__env_repo.get_all_type_equip()
        return [TypeEquipment.model_validate(i, from_attributes=True) for i in entity]

    async def add_type_equipment(self, type_equipment: PostTypeEquipment) -> ProfessionORM:
        entity = TypeEquipmentORM(
            name=type_equipment.name,
            code=type_equipment.code,
            description=type_equipment.description)
        type_equipment = await self.__env_repo.add_type_equipment(entity)
        return type_equipment

    async def get_all_state_object(self) -> list[StateObject]:
        entity = await self.__env_repo.get_all_state_object()
        return [StateObject.model_validate(i, from_attributes=True) for i in entity]

    async def get_all_region(self) -> list[Region]:
        entity = await self.__env_repo.get_all_region()
        return [Region.model_validate(i, from_attributes=True) for i in entity]

    async def import_region_file(self, file: UploadFile):
        try:
            regions = []
            while contents := await file.read(1024 * 1024):
                buffer = StringIO(contents.decode('utf-8-sig'))
                csv_reader = csv.DictReader(buffer, delimiter=';')

                for rows in csv_reader:

                    region = RegionORM(
                        code=rows["code"],
                        name=rows["name"],
                    )
                    regions.append(region)

                await self.__env_repo.add_list_region(regions)

        except Exception:
            raise Exception()
        finally:
            await file.close()

    async def add_region(self, name: str, code: str):
        entity = RegionORM(name=name, code=code)
        entity = await self.__env_repo.add(entity)

    async def get_all_type_brake(self, class_brake: str) -> list[GetTypeBrake] | None:
        entity = await self.__type_brake_repo.get_all_type_brake_by_class(class_brake)
        if entity is None:
            return None
        type_brake = [GetTypeBrake.model_validate(entity, from_attributes=True) for entity in entity]
        return type_brake

    async def import_type_brake_file(self, file: UploadFile):
        try:
            type_brakes = []
            while contents := await file.read(1024 * 1024):
                buffer = StringIO(contents.decode('utf-8-sig'))
                csv_reader = csv.DictReader(buffer, delimiter=';')

                for rows in csv_reader:
                    type_brake = TypeBrakeORM(
                        code=rows["code"],
                        name=rows["name"],
                        id_type=int(rows["class"])
                    )
                    type_brakes.append(type_brake)

                await self.__type_brake_repo.add_list_type_brake(type_brakes)

        except Exception:
            raise Exception()
        finally:
            await file.close()

    async def get_all_signs_accident(self) -> list[SignsAccident] | None:
        entity = await self.__env_repo.get_all_signs_accident()
        if entity is None:
            return None
        signs_accident = [SignsAccident.model_validate(entity, from_attributes=True) for entity in entity]
        return signs_accident

    async def import_signs_accident(self, file: UploadFile):
        try:
            signs_accident_list = []
            while contents := await file.read(1024 * 1024):
                buffer = StringIO(contents.decode('utf-8-sig'))
                csv_reader = csv.DictReader(buffer, delimiter=';')

                for rows in csv_reader:
                    signs_accident = SignsAccidentORM(
                        code=rows["code"],
                        name=rows["name"],
                    )
                    signs_accident_list.append(signs_accident)
                await self.__env_repo.add_list_signs_accident(signs_accident_list)

        except Exception:
            raise Exception()
        finally:
            await file.close()

    async def get_list_type_event(self) -> list[TypeEvent]:
        lists = await self.__env_repo.get_all_type_event()
        return [TypeEvent.model_validate(i, from_attributes=True) for i in lists]

    async def get_list_state_event(self) -> list[StateEvent]:
        lists = await self.__env_repo.get_all_state_event()
        return [StateEvent.model_validate(i, from_attributes=True) for i in lists]

    async def get_state_claim(self) -> list[StateClaimModel]:
        entity = await self.__env_repo.get_state_claim()
        state_claim = [StateClaimModel.model_validate(i, from_attributes=True) for i in entity]
        return state_claim
