from fastapi import Depends, UploadFile

from ..models.User import GetTypeUser, Profession
from ..models.Equipment import TypeEquipment, PostTypeEquipment
from ..models.Object import StateObject, Region
from ..models.Accident import GetTypeBrake, SignsAccident
from ..models.Event import TypeEvent, StateEvent
from ..models.Claim import StateClaimModel

from ..tables import (TypeBrake as TypeBrakeORM,
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
