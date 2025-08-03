from fastapi import APIRouter, Depends, status, Response, UploadFile, File
from fastapi.responses import JSONResponse

from ..models.Object import *
from ..models.Equipment import *
from ..models.Message import Message

from ..services import ObjectService, get_current_user, EquipmentService
from ..models.User import UserGet
from ..functions import access_control

router = APIRouter(prefix="/object", tags=["object"])


message_error = {
    status.HTTP_406_NOT_ACCEPTABLE: JSONResponse(content={"message": "отказ в доступе"},
                                                 status_code=status.HTTP_406_NOT_ACCEPTABLE)
}


@router.post("", responses={
    status.HTTP_406_NOT_ACCEPTABLE: {"model": Message},
    status.HTTP_201_CREATED: {"model": Message},
    status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message}
})
@access_control(["admin", "super_admin"])
async def add_object(object_target: PostObject,
                     service: ObjectService = Depends(),
                     current_user: UserGet = Depends(get_current_user)):
    try:
        await service.create_object(object_target)
        return JSONResponse(content={"message": "добавлено"},
                            status_code=status.HTTP_201_CREATED)
    except Exception:
        return JSONResponse(content={"message": "ошибка добавления"},
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.get("/page", response_model=list[GetObject],
            responses={
                status.HTTP_406_NOT_ACCEPTABLE: {"model": Message},
                status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message},
                status.HTTP_200_OK: {"model": Message}
            })
@access_control(["admin", "super_admin"])
async def get_page(response: Response,
                   page: int = 1,
                   per_item_page: int = 20,
                   state_object: str | None = None,
                   current_user: UserGet = Depends(get_current_user),
                   service: ObjectService = Depends()):
    service.count_item = per_item_page
    count_page = await service.get_count_page()
    response.headers["X-Count-Page"] = str(count_page)
    response.headers["X-Count-Item"] = str(service.count_item)
    return await service.get_page_object(page)


@router.get("/list", response_model=list[GetObject],
            responses={
                status.HTTP_406_NOT_ACCEPTABLE: {"model": Message},
                status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message},
                status.HTTP_200_OK: {"model": Message}
            })
@access_control(["admin", "super_admin", "user"])
async def get_all_object(current_user: UserGet = Depends(get_current_user),
                         service: ObjectService = Depends()):

    return await service.get_all_object(current_user)


@router.delete("/{uuid}", responses={
    status.HTTP_406_NOT_ACCEPTABLE: {"model": Message},
    status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message},
    status.HTTP_200_OK: {"model": Message},
})
@access_control(["admin", "super_admin"])
async def delete_object(uuid: str,
                        service: ObjectService = Depends(),
                        current_user: UserGet = Depends(get_current_user)):
    try:
        await service.delete_object(uuid)
        return JSONResponse(content={"message": "Удалено"},
                            status_code=status.HTTP_200_OK)
    except Exception:
        return JSONResponse(content={"message": "ошибка удаления"},
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.put("/{uuid}", responses={
    status.HTTP_406_NOT_ACCEPTABLE: {"model": Message},
    status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message},
    status.HTTP_200_OK: {"model": Message},
})
@access_control(["admin", "super_admin"])
async def update_object(uuid: str,
                        target_obj: UpdateObject,
                        service: ObjectService = Depends(),
                        current_user: UserGet = Depends(get_current_user)
                        ):
    try:
        await service.update_object(uuid, target_obj)
        return JSONResponse(content={"message": "Обновленно"},
                            status_code=status.HTTP_200_OK)
    except Exception:
        return JSONResponse(content={"message": "ошибка обновления"},
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.get("/one/{uuid}", response_model=GetObject,
            responses={
                status.HTTP_406_NOT_ACCEPTABLE: {"model": Message},
                status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message},
                status.HTTP_200_OK: {"model": Message},
                status.HTTP_404_NOT_FOUND: {"model": Message}
            })
@access_control(["admin", "super_admin", "user"])
async def get_one_object(uuid: str,
                         service: ObjectService = Depends(),
                         current_user: UserGet = Depends(get_current_user)
):
    obj = await service.get_one(uuid)
    if obj is not None:
        return obj
    else:
        return JSONResponse(content={"message": " не существует"},
                            status_code=status.HTTP_404_NOT_FOUND)


@router.get("/{uuid}/equipment/page", response_model=list[GetEquipment],
            responses={
                status.HTTP_406_NOT_ACCEPTABLE: {"model": Message},
                status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message},
                status.HTTP_200_OK: {"model": Message}
            })
@access_control(["admin", "super_admin", "user"])
async def get_page_equipment(
        uuid: str,
        response: Response,
        page: int = 1,
        per_item_page: int = 20,
        type_equip: str | None = None,
        current_user: UserGet = Depends(get_current_user),
        service: EquipmentService = Depends()):
    service.count_item = per_item_page
    count_page = await service.get_count_page(uuid)
    response.headers["X-Count-Page"] = str(count_page)
    response.headers["X-Count-Item"] = str(service.count_item)
    t = await service.get_page_equip(uuid, page)
    return t


@router.get("/{uuid}/equipment/search",
            response_model=list[GetEquipment],
            responses={
                status.HTTP_406_NOT_ACCEPTABLE: {"model": Message},
                status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message},
                status.HTTP_200_OK: {"model": Message}
            })
async def search_equipment(
        uuid: str,
        search_field: str,
        service: EquipmentService = Depends(),
        current_user: UserGet = Depends(get_current_user)
):
    equipment = await service.get_equipment_by_search_field(uuid, search_field)
    return equipment


@router.get("/{uuid}/equipment/list", response_model=list[GetEquipment],
            responses={
                status.HTTP_406_NOT_ACCEPTABLE: {"model": Message},
                status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message},
                status.HTTP_200_OK: {"model": Message}
            })
@access_control(["admin", "super_admin", "user"])
async def get_all_equipment(
        uuid: str,
        current_user: UserGet = Depends(get_current_user),
        service: EquipmentService = Depends()):
    return await service.get_all_equip(uuid)


@router.get("/equipment/{uuid}", response_model=GetEquipment,
            responses={
                status.HTTP_406_NOT_ACCEPTABLE: {"model": Message},
                status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message},
                status.HTTP_200_OK: {"model": Message},
                status.HTTP_404_NOT_FOUND: {"model": Message}
            })
@access_control(["admin", "super_admin", "user"])
async def get_one_equipment(uuid: str,
                            service: EquipmentService = Depends(),
                            current_user: UserGet = Depends(get_current_user)
):
    obj = await service.get_one(uuid)
    if obj is not None:
        return obj
    else:
        return JSONResponse(content={"message": " не существует"},
                            status_code=status.HTTP_404_NOT_FOUND)


@router.post("/{uuid}/equipment", responses={
    status.HTTP_406_NOT_ACCEPTABLE: {"model": Message},
    status.HTTP_201_CREATED: {"model": Message},
    status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message}
})
async def add_equipment(
        uuid: str,
        equipment_target: PostEquipment,
        service: EquipmentService = Depends(),
        service_object: ObjectService = Depends(),
        current_user: UserGet = Depends(get_current_user)):
    is_edit = await service_object.is_user_in_object(current_user, uuid)
    try:
        await service.create_equip(uuid, equipment_target)
        return JSONResponse(content={"message": "добавлено"},
                            status_code=status.HTTP_201_CREATED)
    except Exception:
        return JSONResponse(content={"message": "ошибка добавления"},
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.delete("/equipment/{uuid_equipment}", responses={
    status.HTTP_406_NOT_ACCEPTABLE: {"model": Message},
    status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message},
    status.HTTP_200_OK: {"model": Message},
})
async def delete_equipment(
        uuid_equipment: str,
        service: EquipmentService = Depends(),
        service_object: ObjectService = Depends(),
        current_user: UserGet = Depends(get_current_user)):
    is_edit = await service_object.is_user_in_object_by_uuid_equipment(current_user, uuid_equipment)
    try:
        await service.delete_equip(uuid_equipment)
        return JSONResponse(content={"message": "Удалено"},
                            status_code=status.HTTP_200_OK)
    except Exception:
        return JSONResponse(content={"message": "ошибка удаления"},
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.put("/equipment/{uuid_equipment}", responses={
    status.HTTP_406_NOT_ACCEPTABLE: {"model": Message},
    status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message},
    status.HTTP_200_OK: {"model": Message},
})
async def update_equipment(uuid_equipment: str,
                           target_equipment: UpdateEquipment,
                           service: EquipmentService = Depends(),
                           service_object: ObjectService = Depends(),
                           current_user: UserGet = Depends(get_current_user)):
    is_edit = await service_object.is_user_in_object_by_uuid_equipment(current_user, uuid_equipment)

    try:
        await service.update_equip(uuid_equipment, target_equipment)
        return JSONResponse(content={"message": "Обновленно"},
                            status_code=status.HTTP_200_OK)
    except Exception:
        return JSONResponse(content={"message": "ошибка обновления"},
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.get("/{uuid}/users", response_model=list[UserGet],
            responses={
                status.HTTP_406_NOT_ACCEPTABLE: {"model": Message},
                status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message},
                status.HTTP_200_OK: {"model": Message}
            })
@access_control(["admin", "super_admin"])
async def get_users_to_object(
        uuid: str,
        current_user: UserGet = Depends(get_current_user),
        service: ObjectService = Depends()):
    return await service.get_users_object(uuid)


@router.post("/{uuid_object}/user/{uuid_user}", responses={
    status.HTTP_406_NOT_ACCEPTABLE: {"model": Message},
    status.HTTP_201_CREATED: {"model": Message},
    status.HTTP_200_OK: {"model": Message},
    status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message}
})
@access_control(["admin", "super_admin"])
async def registrate_user_to_object(uuid_object: str,
                                    uuid_user: str,
                                    service: ObjectService = Depends(),
                                    current_user: UserGet = Depends(get_current_user)):
    try:
        is_add = await service.registrate_user(uuid_object, uuid_user)
        if is_add:
            return JSONResponse(content={"message": "добавлено"},
                                status_code=status.HTTP_201_CREATED)
        else:
            return JSONResponse(content={"message": "уже существует или прикреплен к другому объекту"},
                                status_code=status.HTTP_200_OK)
    except Exception:
        return JSONResponse(content={"message": "ошибка добавления"},
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.delete("/{uuid_object}/user/{uuid_user}", responses={
    status.HTTP_406_NOT_ACCEPTABLE: {"model": Message},
    status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message},
    status.HTTP_200_OK: {"model": Message},
})
@access_control(["admin", "super_admin"])
async def delete_user_to_object(uuid_object: str,
                                uuid_user: str,
                                service: ObjectService = Depends(),
                                current_user: UserGet = Depends(get_current_user)):
    try:
        await service.delete_user_in_object(uuid_object, uuid_user)
        return JSONResponse(content={"message": "Удалено"},
                            status_code=status.HTTP_200_OK)
    except Exception:
        return JSONResponse(content={"message": "ошибка удаления"},
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.get("/get_object_to_user", responses={
    status.HTTP_406_NOT_ACCEPTABLE: {"model": Message},
    status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message},
    status.HTTP_200_OK: {"model": Message},
}, response_model=list[GetObject])
@access_control(["user"])
async def get_object_to_user(service: ObjectService = Depends(),
                             current_user: UserGet = Depends(get_current_user)):
    obj = await service.get_object_to_user(current_user.uuid)
    if obj is not None:
        return obj
    else:
        return JSONResponse(content={"message": " не существует"},
                            status_code=status.HTTP_404_NOT_FOUND)