from fastapi import APIRouter, Depends, status, Request, Response, UploadFile, File
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
                    current_user: UserGet = Depends(get_current_user),
                    service: FileService = Depends()):
    await service.upload_file(file)
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
