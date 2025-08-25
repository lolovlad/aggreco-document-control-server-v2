from fastapi import Depends, UploadFile, HTTPException, status

from ..tables import FileDocument

from ..models.Files import *

from ..repositories import FileBucketRepository, FileRepository
from .ClaimService import ClaimServices

from random import randint
from functools import partial
from docxtpl import DocxTemplate, InlineImage
from io import BytesIO
from datetime import datetime, timedelta, timezone


class FileService:
    def __init__(self,
                 file: FileRepository = Depends(),
                 claim: ClaimServices = Depends()):
        self.__file_bucket_repo: FileBucketRepository = FileBucketRepository("document")
        self.__file_repo: FileRepository = file
        self.__claim_service: ClaimServices = claim

    def __get_date_split(self, datetime: datetime) -> dict:
        date = datetime.strftime("%d.%m.%Y.%H.%M.%S")
        date_split = date.split('.')
        return {
            "date": ".".join(date_split[:3]),
            "d": date_split[0],
            "mm": date_split[1],
            "y": date_split[2],
            "h": date_split[3],
            "m": date_split[4],
            "s": date_split[5]
        }

    def __get_moscov_datetime(self, datetime: datetime, time_zone: str):
        sign = 1 if time_zone[0] == "+" else -1
        hours, minutes = map(int, time_zone[1:].split(":"))
        offset = timedelta(hours=hours, minutes=minutes) * sign

        aware_datetime = datetime.replace(tzinfo=timezone(offset))

        utc_datetime = aware_datetime.astimezone(timezone.utc)

        moscow_timezone = timezone(timedelta(hours=3))
        moscow_datetime = utc_datetime.astimezone(moscow_timezone)

        return moscow_datetime

    async def get_all_files(self) -> list[GetFile]:
        files = await self.__file_repo.get_all()
        return [GetFile.model_validate(i, from_attributes=True) for i in files]

    async def upload_file(self, file: UploadFile, file_name: str):
        ext = file.filename.split(".")[-1]
        file_name_key = f"{randint(1000, 10000)}_шаблон_генерации_file.{ext}"

        file_key = f"blueprint/{file_name_key}"

        file_doc = FileDocument(
            file_key="Нет",
            file_name=file_key,
            name=file_name,
            size=float(round(file.size / 1024, 2))
        )

        content = await file.read()
        await self.__file_bucket_repo.upload_file(file_key,
                                                  content,
                                                  file.content_type)

        await self.__file_repo.add(file_doc)

    async def get_file(self, id_file: int):
        file_model = await self.__file_repo.get(id_file)

        if file_model is not None:
            file_name = file_model.file_key

            info = await self.__file_bucket_repo.get_sate(file_name)

            ext = file_name.split(".")[-1]

            return file_name, ext, info
        else:
            return None, None

    async def generate_document(self, uuid_claim: str, data_generate: FileGenerate) -> dict:
        claim = await self.__claim_service.get_claim(uuid_claim)
        file = await self.__file_repo.get(data_generate.id_blueprint)
        file_streem = await self.__file_bucket_repo.get_file(file.file_name)

        try:
            blueprint = DocxTemplate(BytesIO(file_streem))
            template_file = BytesIO()
        except Exception:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

        dump = claim.model_dump()

        dump["castome"] = {
            "date": {
                "start_local": self.__get_date_split(claim.accident.datetime_start),
                "end_local": self.__get_date_split(claim.accident.datetime_end),
                "start_msc": self.__get_date_split(self.__get_moscov_datetime(claim.accident.datetime_start, claim.accident.time_zone)),
                "end_msc": self.__get_date_split(self.__get_moscov_datetime(claim.accident.datetime_end, claim.accident.time_zone)),
            },
            "unique_type_damage_equipment": [i.model_dump() for i in claim.accident.get_unique_type_damaged_equipment()]
        }

        dump["accident"]["time_line"] = [
            {
                "time": i["time"].strftime("%d.%m.%Y %H:%M:%S"),
                "val": i["description"]
            } for i in sorted(dump["accident"]["time_line"], key=lambda i: i["time"])
        ]

        dump["accident"]["event"] = [
            {
                "date_finish": i["date_finish"].strftime("%d.%m.%Y %H:%M"),
                "description": i["description"],
                "type_event": i["type_event"]
            } for i in sorted(dump["accident"]["event"], key=lambda i: i["date_finish"])
        ]

        blueprint.render(dump)
        blueprint.save(template_file)
        template_file.seek(0)

        await self.__claim_service.upload_file("main", claim.uuid, UploadFile(
            file=template_file,
            filename="blueprint.docx"
        ))

        return {"state_file": "upload", "uuid_token": None}

    async def delete_file(self, id_file: int):
        file = await self.__file_repo.delete(id_file)
        await self.__file_bucket_repo.delete_file(file.file_name)

    async def get_file_metadata(self, id_blueprint: int) -> GetFile:
        file = await self.__file_repo.get(id_blueprint)
        return GetFile.model_validate(file, from_attributes=True)

    async def update_file(self, id_blueprint: int, file: UploadFile | None, file_name: str | None):
        file_entity = await self.__file_repo.get(id_blueprint)
        file_entity.name = file_name
        if file is not None:
            file_entity.size = float(round(file.size / 1024, 2))

            await self.__file_bucket_repo.delete_file(file_entity.file_name)

            content = await file.read()
            await self.__file_bucket_repo.upload_file(file_entity.file_name,
                                                      content,
                                                      file.content_type)

        await self.__file_repo.update(file_entity)

