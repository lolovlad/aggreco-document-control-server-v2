from fastapi import (
    APIRouter,
    Depends,
    status,
    Request,
    Response,
    UploadFile,
    File,
    Form)
from typing import Annotated, Optional
from fastapi.responses import JSONResponse, StreamingResponse

from ..services import get_current_user, FileService

from ..repositories import FileBucketRepository

from ..models.Message import Message
from ..models.User import UserGet
from ..models.Files import GetFile, FileGenerate

router = APIRouter(prefix="/file", tags=["file"])
message_error = {
    status.HTTP_406_NOT_ACCEPTABLE: JSONResponse(content={"message": "отказ в доступе"},
                                                 status_code=status.HTTP_406_NOT_ACCEPTABLE)
}


@router.post("", responses={
    status.HTTP_406_NOT_ACCEPTABLE: {"model": Message},
    status.HTTP_201_CREATED: {"model": Message},
    status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message}
})
async def save_file(file: UploadFile,
                    name_file: Annotated[str, Form()],
                    current_user: UserGet = Depends(get_current_user),
                    service: FileService = Depends()):
    await service.upload_file(file, name_file)
    return {"filenames": file.filename}


@router.get("/all", response_model=list[GetFile])
async def get_all_file(
                    current_user: UserGet = Depends(get_current_user),
                    service: FileService = Depends()):
    files = await service.get_all_files()
    return files


@router.get("/{id_file}")
async def get_file(id_file: int,
                   service: FileService = Depends(),
                   ):
    file_name, ext, info = await service.get_file(id_file)

    if file_name is None:
        return JSONResponse(content={"message": "не существует"},
                            status_code=status.HTTP_404_NOT_FOUND)

    media_type = "application/octet-stream"

    file_repo = FileBucketRepository('document')

    file_name_now = file_name.split("/")

    headers = {"Content-Disposition": f'inline; filename="blueprint.{ext}"'}

    return StreamingResponse(
        file_repo.get_file_stream(file_name, info.size),
        media_type=media_type,
        headers=headers,
    )


@router.post("/generate/{uuid_claim}")
async def generate_file(uuid_claim: str,
                        generate_data: FileGenerate,
                        current_user: UserGet = Depends(get_current_user),
                        service: FileService = Depends()):

    response = await service.generate_document(uuid_claim, generate_data)
    return response


@router.delete("/{id_file}", responses={
    status.HTTP_406_NOT_ACCEPTABLE: {"model": Message},
    status.HTTP_200_OK: {"model": Message},
    status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message}
})
async def delete_file(id_file: int,
                      current_user: UserGet = Depends(get_current_user),
                      service: FileService = Depends()):
    if current_user.type.name == "admin":
        try:
            await service.delete_file(id_file)
            return JSONResponse(content={"message": "Файл удален"},
                                status_code=status.HTTP_200_OK)
        except Exception:
            return JSONResponse(content={"message": "Ошибка удаления"},
                                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        return message_error[status.HTTP_406_NOT_ACCEPTABLE]


@router.get("/metadata/{id_blueprint}", responses={
    status.HTTP_406_NOT_ACCEPTABLE: {"model": Message},
    status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message}
}, response_model=GetFile)
async def get_metadata_file(id_blueprint: int,
                            current_user: UserGet = Depends(get_current_user),
                            service: FileService = Depends()):
    if current_user.type.name == "admin":
        try:
            file = await service.get_file_metadata(id_blueprint)
            return file
        except Exception:
            return JSONResponse(content={"message": "Ошибка удаления"},
                                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        return message_error[status.HTTP_406_NOT_ACCEPTABLE]


@router.put("/{id_blueprint}", responses={
    status.HTTP_406_NOT_ACCEPTABLE: {"model": Message},
    status.HTTP_200_OK: {"model": Message},
    status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message}
})
async def update_file(id_blueprint: int,
                      name_file: Annotated[str, Form(), None],
                      file: Optional[UploadFile] = File(None),
                      current_user: UserGet = Depends(get_current_user),
                      service: FileService = Depends()):
    try:
        await service.update_file(id_blueprint, file, name_file)
        return JSONResponse(content={"message": "Обновлен"},
                                     status_code=status.HTTP_200_OK)
    except Exception:
        return JSONResponse(content={"message": "Ошибка удаления"},
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)