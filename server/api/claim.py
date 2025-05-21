from fastapi import APIRouter, Depends, status, Request, Response, UploadFile, File
from fastapi.responses import JSONResponse, StreamingResponse

from ..services import ClaimServices, get_current_user, AccidentService
from ..models.Claim import (
    GetClaim,
    PostClaim,
    UpdateClaim,
    StateClaimModel
)
from ..models.Message import Message
from ..models.User import UserGet
from ..repositories import FileBucketRepository
from ..functions import access_control


router = APIRouter(prefix="/claim", tags=["claim"])


message_error = {
    status.HTTP_406_NOT_ACCEPTABLE: JSONResponse(content={"message": "отказ в доступе"},
                                                 status_code=status.HTTP_406_NOT_ACCEPTABLE)
}


@router.get("/page", response_model=list[GetClaim], responses={
                status.HTTP_406_NOT_ACCEPTABLE: {"model": Message},
                status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message},
                status.HTTP_200_OK: {"model": Message}
})
async def get_page_claim(
        response: Response,
        page: int = 1,
        per_item_page: int = 20,
        id_state_claim: int = 0,
        uuid_object: str = "all",
        current_user: UserGet = Depends(get_current_user),
        service: ClaimServices = Depends()):

    service.count_item = per_item_page
    if current_user.type.name == "user":
        count_page = await service.get_count_page(current_user.uuid, uuid_object, id_state_claim)
    else:
        count_page = await service.get_count_page(None, uuid_object, id_state_claim)
    claims = await service.get_page_claim(page, current_user, uuid_object, id_state_claim)

    response.headers["X-Count-Page"] = str(count_page)
    response.headers["X-Count-Item"] = str(service.count_item)
    return claims


@router.post("", responses={
    status.HTTP_406_NOT_ACCEPTABLE: {"model": Message},
    status.HTTP_201_CREATED: {"model": Message},
    status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message}
})
async def add_claim(request: Request,
                    claim: PostClaim,
                    current_user: UserGet = Depends(get_current_user),
                    claim_service: ClaimServices = Depends(),
                    accident_service: AccidentService = Depends()):

    client_timezone = request.headers.get("X-Timezone", "Unknown")
    try:
        accident = await accident_service.add_accident(claim.accident, client_timezone)

        await claim_service.add_claim(current_user.uuid, accident.id, claim)
        return JSONResponse(content={"message": "добавлено"},
                            status_code=status.HTTP_201_CREATED)
    except Exception:
        return JSONResponse(content={"message": "ошибка добавления"},
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.get("/get/{uuid}", responses={
    status.HTTP_406_NOT_ACCEPTABLE: {"model": Message},
    status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message}
}, response_model=GetClaim)
async def get_one_claim(uuid: str,
                        service: ClaimServices = Depends()):
    obj = await service.get_claim(uuid)
    if obj is not None:
        return obj
    else:
        return JSONResponse(content={"message": " не существует"},
                            status_code=status.HTTP_404_NOT_FOUND)


@router.post("/file/{type_file}/{uuid}", responses={
    status.HTTP_406_NOT_ACCEPTABLE: {"model": Message},
    status.HTTP_201_CREATED: {"model": Message},
    status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message}
})
async def save_file(type_file: str,
                    uuid: str,
                    file: UploadFile,
                    current_user: UserGet = Depends(get_current_user),
                    service: ClaimServices = Depends()):
    await service.upload_file(type_file, uuid, file)
    return {"filenames": file.filename}


@router.get("/file/{type_file}/{uuid}")
async def get_file(type_file: str,
                   uuid: str,
                   service: ClaimServices = Depends(),
                   ):
    try:
        file, file_path = await service.get_file(type_file, uuid)
    except Exception:
        return JSONResponse(content={"message": "не существует"},
                            status_code=status.HTTP_404_NOT_FOUND)

    file_name = file_path.split("/")[-1]

    if file is None:
        return JSONResponse(content={"message": "не существует"},
                            status_code=status.HTTP_404_NOT_FOUND)

    media_type = "application/octet-stream"

    file_repo = FileBucketRepository('document')

    headers = {"Content-Disposition": f'inline; filename="{file_name}"'}

    try:
        info = await file_repo.get_sate(file_path)

        return StreamingResponse(
            file_repo.get_file_stream(file_path, info.size),
            media_type=media_type,
            headers=headers,
        )
    except Exception:
        return JSONResponse(content={"message": "не существует"},
                            status_code=status.HTTP_404_NOT_FOUND)


@router.delete("/{uuid}", responses={
    status.HTTP_406_NOT_ACCEPTABLE: {"model": Message},
    status.HTTP_200_OK: {"model": Message},
    status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message}
})
async def delete_claim(uuid: str,
                       current_user: UserGet = Depends(get_current_user),
                       service: ClaimServices = Depends()):
    try:
        await service.delete_claim(uuid, current_user)
        return JSONResponse(content={"message": "Удалено"},
                            status_code=status.HTTP_200_OK)
    except Exception:
        return JSONResponse(content={"message": "ошибка обновления"},
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.put("/update/state/{uuid_claim}/{state_claim}", responses={
    status.HTTP_406_NOT_ACCEPTABLE: {"model": Message},
    status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message},
    status.HTTP_200_OK: {"model": Message},
})
async def update_claim_state(uuid_claim: str,
                             state_claim: str,
                             current_user: UserGet = Depends(get_current_user),
                             service: ClaimServices = Depends()
                             ):
    try:
        await service.update_state_claim(uuid_claim, state_claim, current_user)
    except Exception:
        return JSONResponse(content={"message": "ошибка обновления состояния"},
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.put("/{uuid_claim}", responses={
    status.HTTP_406_NOT_ACCEPTABLE: {"model": Message},
    status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message},
    status.HTTP_200_OK: {"model": Message},
})
@access_control(["admin", "super_admin"])
async def update_claim(uuid_claim: str,
                       claim_model: UpdateClaim,
                       current_user: UserGet = Depends(get_current_user),
                       service: ClaimServices = Depends()
                       ):
    try:
        await service.update_claim(uuid_claim, claim_model)
    except Exception:
        return JSONResponse(content={"message": "ошибка обновления"},
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
