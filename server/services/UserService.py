from fastapi import Depends, UploadFile

from ..repositories import UserRepository, FileBucketRepository
from .EnvService import EnvService
from ..models.User import *
from ..tables import User, Profession as ProfessionORM
import csv
from io import StringIO
import aiofiles
from uuid import uuid4
import base64


class UserService:
    def __init__(self,
                 user_rep: UserRepository = Depends(),
                 env_service: EnvService = Depends()):
        self.__user_repo: UserRepository = user_rep
        self.__env_service: EnvService = env_service
        self.__file_repo: FileBucketRepository = FileBucketRepository("user")
        self.__count_item: int = 20

    @property
    def count_item(self) -> int:
        return self.__count_item

    @count_item.setter
    def count_item(self, item):
        self.__count_item = item

    async def get_count_page(self) -> int:
        count_row = await self.__user_repo.count_row()
        sub_page = 0
        if count_row % self.__count_item > 0:
            sub_page += 1
        return count_row // self.__count_item + sub_page

    async def get_page_user(self, num_page: int) -> list[UserGet]:
        start = (num_page - 1) * self.__count_item
        users_entity = await self.__user_repo.get_limit_user(start, self.__count_item)
        users = [UserGet.model_validate(entity, from_attributes=True) for entity in users_entity]
        return users

    async def create_user(self, user: UserPost):
        entity = User(
            name=user.name,
            surname=user.surname,
            patronymic=user.patronymic,
            email=user.email,
            id_type=user.id_type,
            id_profession=user.id_profession
        )
        entity.password = user.password
        try:
            await self.__user_repo.add(entity)
        except Exception:
            raise Exception

    async def export_user_from_csv(self, file: UploadFile):
        try:
            set_prof = {}
            users = []
            while contents := await file.read(1024 * 1024):
                buffer = StringIO(contents.decode('utf-8-sig'))
                csv_reader = csv.DictReader(buffer, delimiter=';')

                for rows in csv_reader:
                    prof_name = rows["Профессия"]
                    if prof_name not in set_prof:
                        prof = await self.__env_service.add_profession(prof_name, "")

                        set_prof[prof.name] = prof.id

                    su, name, pat = rows["FIO"].split(" ")

                    user = User(
                        name=name,
                        surname=su,
                        patronymic=pat,
                        id_type=2,
                        id_profession=set_prof[prof_name],
                        uuid=uuid4()
                    )
                    users.append(user)

                await self.__user_repo.add_list(users)

        except Exception:
            raise Exception()
        finally:
            await file.close()

    async def get_user(self, uuid: str) -> UserGet | None:
        user = await self.__user_repo.get_user_by_uuid(uuid)
        if user is None:
            return None
        return UserGet.model_validate(user, from_attributes=True)

    async def get_users_by_search_field(self, search_field: str, count: int):
        data_field = search_field.split(" ")
        surname, name, patronymic = "", "", ""
        if len(data_field) > 0:
            surname = data_field[0]
        if len(data_field) > 1:
            name = data_field[1]
        if len(data_field) > 2:
            patronymic = data_field[2]
        users_entity = await self.__user_repo.get_users_by_search_field(
            surname,
            name,
            patronymic,
            count
        )
        users = [UserGet.model_validate(entity, from_attributes=True) for entity in users_entity]
        return users

    async def update_user(self, uuid: str, user: UserUpdate, current_user: UserGet):
        entity = await self.__user_repo.get_user_by_uuid(uuid)

        if entity.type.name in ("admin", "super_admin") and current_user.type.name == "admin":
            raise Exception

        user_dict = user.model_dump()
        for key in user_dict:
            if key != "password":
                setattr(entity, key, user_dict[key])

        if user.password is not None:
            entity.password = user.password

        try:
            await self.__user_repo.update(entity)
        except Exception:
            raise Exception

    async def delete_user(self, uuid: str, current_user: UserGet):
        entity = await self.__user_repo.get_user_by_uuid(uuid)
        if entity.type.name in ("admin", "super_admin") and current_user.type.name == "admin":
            raise Exception
        await self.__user_repo.delete(uuid)

    async def upload_signature(self, user: UserGet, file: UploadFile):
        ext = file.filename.split(".")[1]
        dir_name = f"{user.surname}_{user.name}_{user.patronymic}_{user.uuid}"

        file_key = f"{dir_name}/signature.{ext}"

        user = await self.__user_repo.get_user_by_uuid(user.uuid)
        user.painting = file_key

        content = await file.read()
        await self.__file_repo.upload_file(file_key,
                                           content,
                                           file.content_type)

        await self.__user_repo.update(user)

    async def get_signature(self, user: UserGet):
        user = await self.__user_repo.get_user_by_uuid(user.uuid)
        if user.painting is not None and len(user.painting) > 0:
            exp = user.painting.split(".")[-1]
            file = await self.__file_repo.get_file(user.painting)
            file_encode = base64.b64encode(file).decode("utf-8")
            return {
                "file": str(file_encode),
                "exp": exp
            }
        return {
            "file": None,
            "exp": None
        }