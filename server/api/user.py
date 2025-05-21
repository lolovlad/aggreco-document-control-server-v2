from fastapi import APIRouter, Depends, status, Request, Response, UploadFile, File
from fastapi.responses import JSONResponse, RedirectResponse

from starlette.templating import Jinja2Templates

from ..services import UserService, get_current_user
from ..models.Document import DocumentPost
from ..models.Message import Message
from ..models.User import UserGet, UserPost, GetTypeUser, UserUpdate, Profession
from ..functions import access_control


router = APIRouter(prefix="/user", tags=["user"])


message_error = {
    status.HTTP_406_NOT_ACCEPTABLE: JSONResponse(content={"message": "отказ в доступе"},
                                                 status_code=status.HTTP_406_NOT_ACCEPTABLE)
}


@router.get("/get_one/{uuid}", responses={
    status.HTTP_406_NOT_ACCEPTABLE: {"model": Message},
    status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message}
}, response_model=UserGet)
async def get_one_user(uuid: str,
                       user_service: UserService = Depends(),
                       current_user: UserGet = Depends(get_current_user)
                       ):
    user = await user_service.get_user(uuid)
    if user is not None:
        return user
    else:
        return JSONResponse(content={"message": "Пользователя не существует"},
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.post("", responses={
    status.HTTP_406_NOT_ACCEPTABLE: {"model": Message},
    status.HTTP_201_CREATED: {"model": Message},
    status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message}
})
@access_control(["admin", "super_admin"])
async def create_user(user_target: UserPost,
                      user_service: UserService = Depends(),
                      current_user: UserGet = Depends(get_current_user)):
    try:
        await user_service.create_user(user_target)
        return JSONResponse(content={"message": "добавлено"},
                            status_code=status.HTTP_201_CREATED)
    except Exception:
        return JSONResponse(content={"message": "ошибка добавления"},
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.get("/page_user", response_model=list[UserGet],
            responses={
                status.HTTP_406_NOT_ACCEPTABLE: {"model": Message},
                status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message},
                status.HTTP_200_OK: {"model": Message}
            })
@access_control(["admin", "super_admin"])
async def get_page_user(response: Response,
                        page: int = 1,
                        per_item_page: int = 20,
                        type_user: str | None = None,
                        current_user: UserGet = Depends(get_current_user),
                        user_service: UserService = Depends()):
    user_service.count_item = per_item_page
    count_page = await user_service.get_count_page()
    response.headers["X-Count-Page"] = str(count_page)
    response.headers["X-Count-Item"] = str(per_item_page)
    users = await user_service.get_page_user(page)
    return users


@router.post("/import_file/csv", responses={
    status.HTTP_406_NOT_ACCEPTABLE: {"model": Message},
    status.HTTP_201_CREATED: {"model": Message},
    status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message},
    status.HTTP_400_BAD_REQUEST: {"model": Message}
})
@access_control(["admin", "super_admin"])
async def import_to_file(file: UploadFile = File(...),
                         user_service: UserService = Depends(),
                         current_user: UserGet = Depends(get_current_user)):

    try:
        if file.content_type == "text/csv":
            await user_service.export_user_from_csv(file)
        else:
            return JSONResponse(content={"message": "файл не того типа"},
                                status_code=status.HTTP_400_BAD_REQUEST)

        return JSONResponse(content={"message": "добавлено"},
                            status_code=status.HTTP_201_CREATED)
    except Exception:
        return JSONResponse(content={"message": "ошибка добавления"},
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.get("/search", response_model=list[UserGet],
            responses={
                status.HTTP_406_NOT_ACCEPTABLE: {"model": Message},
                status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message},
                status.HTTP_200_OK: {"model": Message}
            })
async def get_users_by_search(search_field: str,
                              user_service: UserService = Depends(),
                              current_user: UserGet = Depends(get_current_user)
                              ):
    users = await user_service.get_users_by_search_field(search_field)
    return users


@router.put("/{uuid}", responses={
            status.HTTP_406_NOT_ACCEPTABLE: {"model": Message},
            status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message},
            status.HTTP_205_RESET_CONTENT: {}
})
@access_control(["admin", "super_admin"])
async def update_user(uuid: str,
                      user_update: UserUpdate,
                      service: UserService = Depends(),
                      current_user: UserGet = Depends(get_current_user)):
    try:
        await service.update_user(uuid, user_update, current_user)
        return JSONResponse(status_code=status.HTTP_205_RESET_CONTENT, content=None)
    except Exception:
        return JSONResponse(content={"message": "ошибка обновления"},
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.delete("/{uuid}", responses={
            status.HTTP_406_NOT_ACCEPTABLE: {"model": Message},
            status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message},
            status.HTTP_200_OK: {"model": Message}
})
@access_control(["admin", "super_admin"])
async def delete_user(uuid: str,
                      service: UserService = Depends(),
                      current_user: UserGet = Depends(get_current_user)):

    try:
        await service.delete_user(uuid, current_user)
        return JSONResponse(status_code=status.HTTP_200_OK,
                            content={"message": "Удалено"})
    except Exception:
        return JSONResponse(content={"message": "ошибка обновления"},
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.get("/get/profile", response_model=UserGet)
async def get_user_by_token(user_service: UserService = Depends(),
                            current_user: UserGet = Depends(get_current_user)):
    return current_user


@router.get("/file/signature", response_model=dict)
async def get_signature(user_service: UserService = Depends(),
                        current_user: UserGet = Depends(get_current_user)):
    file = await user_service.get_signature(current_user)
    return file


@router.post("/file/signature")
async def add_signature(file: UploadFile,
                        user_service: UserService = Depends(),
                        current_user: UserGet = Depends(get_current_user)):
    await user_service.upload_signature(current_user, file)
    return {"filenames": file.filename}


@router.put("/profile/update/{uuid}",  responses={
            status.HTTP_406_NOT_ACCEPTABLE: {"model": Message},
            status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message},
            status.HTTP_205_RESET_CONTENT: {}
})
async def update_profile_user(uuid: str,
                              user_update: UserUpdate,
                              service: UserService = Depends(),
                              current_user: UserGet = Depends(get_current_user)):
    try:
        if uuid == str(current_user.uuid):
            await service.update_user(uuid, user_update, current_user)
            return JSONResponse(status_code=status.HTTP_205_RESET_CONTENT, content=None)
        else:
            return JSONResponse(content={"message": "отказ в доступе"},
                                status_code=status.HTTP_406_NOT_ACCEPTABLE)
    except Exception:
        return JSONResponse(content={"message": "ошибка обновления"},
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

