from fastapi import Depends, UploadFile, HTTPException, status

from ..tables import FileDocument

from ..models.Files import *

from ..repositories import FileBucketRepository, FileRepository
from .ClaimService import ClaimServices

from random import randint
from functools import partial
from docxtpl import DocxTemplate, InlineImage
from io import BytesIO


class FileService:
    def __init__(self,
                 file: FileRepository = Depends(),
                 claim: ClaimServices = Depends()):
        self.__file_bucket_repo: FileBucketRepository = FileBucketRepository("document")
        self.__file_repo: FileRepository = file
        self.__claim_service: ClaimServices = claim

    async def get_all_files(self) -> list[GetFile]:
        files = await self.__file_repo.get_all()
        return [GetFile.model_validate(i, from_attributes=True) for i in files]

    async def upload_file(self, file: UploadFile):
        ext = file.filename.split(".")[-1]
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

    async def generate_document(self, uuid_claim: str, data_generate: FileGenerate) -> dict:
        claim = await self.__claim_service.get_claim(uuid_claim)
        file = await self.__file_repo.get(data_generate.id_blueprint)
        file_streem = await self.__file_bucket_repo.get_file(file.file_key)

        try:
            blueprint = DocxTemplate(BytesIO(file_streem))
            template_file = BytesIO()
        except Exception:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

        dump = claim.model_dump()

        blueprint.render(dump)
        blueprint.save(template_file)
        template_file.seek(0)

        await self.__claim_service.upload_file("main", claim.uuid, UploadFile(
            file=template_file,
            filename="blueprint.docx"
        ))

        return {"state_file": "upload", "uuid_token": None}





