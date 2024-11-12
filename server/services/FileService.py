from fastapi import Depends, UploadFile

from ..tables import FileDocument

from ..models.Files import *

from ..repositories import FileBucketRepository, FileRepository

from random import randint
from functools import partial


class FileService:
    def __init__(self, file: FileRepository = Depends()):
        self.__file_bucket_repo: FileBucketRepository = FileBucketRepository("document")
        self.__file_repo: FileRepository = file

    async def get_all_files(self) -> list[GetFile]:
        files = await self.__file_repo.get_all()
        return [GetFile.model_validate(i, from_attributes=True) for i in files]

    async def upload_file(self, file: UploadFile):
        ext = file.filename.split(".")[1]
        file_name = f"{randint(1000, 10000)}_шаблон_генерации_file.{ext}"

        file_key = f"blueprint/{file_name}"

        file_doc = FileDocument(
            file_key=file_key,
            file_name=file_name,
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