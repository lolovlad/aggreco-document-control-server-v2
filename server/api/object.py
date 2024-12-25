from fastapi import APIRouter, Depends, status, Response, UploadFile, File
from fastapi.responses import JSONResponse

from ..models.Object import *
from ..models.Equipment import *
from ..models.Message import Message

from ..services import ObjectService, get_current_user, EquipmentService
from ..models.User import UserGet

router = APIRouter(prefix="/object", tags=["object"])


message_error = {
    status.HTTP_406_NOT_ACCEPTABLE: JSONResponse(content={"message": "отказ в доступе"},
                                                 status_code=status.HTTP_406_NOT_ACCEPTABLE)
}


@router.get("/state_object", response_model=list[StateObject], responses={
    status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message},
})
async def get_state_object(service: ObjectService = Depends()):
    state = await service.get_all_state_object()
    return state


@router.post("", responses={
    status.HTTP_406_NOT_ACCEPTABLE: {"model": Message},
    status.HTTP_201_CREATED: {"model": Message},
    status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message}
})
async def add_object(object_target: PostObject,
                     service: ObjectService = Depends(),
                     current_user: UserGet = Depends(get_current_user)):
    if current_user.type.name == "admin":
        try:
            await service.create_object(object_target)
            return JSONResponse(content={"message": "добавлено"},
                                status_code=status.HTTP_201_CREATED)
        except Exception:
            return JSONResponse(content={"message": "ошибка добавления"},
                                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        return message_error[status.HTTP_406_NOT_ACCEPTABLE]


@router.get("/page", response_model=list[GetObject],
            responses={
                status.HTTP_406_NOT_ACCEPTABLE: {"model": Message},
                status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message},
                status.HTTP_200_OK: {"model": Message}
            })
async def get_page(response: Response,
                   page: int = 1,
                   state_object: str | None = None,
                   current_user: UserGet = Depends(get_current_user),
                   service: ObjectService = Depends()):
    if current_user.type.name == "admin":
        count_page = await service.get_count_page()
        response.headers["X-Count-Page"] = str(count_page)
        response.headers["X-Count-Item"] = str(service.count_item)
        return await service.get_page_object(page)
    else:
        return message_error[status.HTTP_406_NOT_ACCEPTABLE]


@router.get("/list", response_model=list[GetObject],
            responses={
                status.HTTP_406_NOT_ACCEPTABLE: {"model": Message},
                status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message},
                status.HTTP_200_OK: {"model": Message}
            })
async def get_all_object(current_user: UserGet = Depends(get_current_user),
                         service: ObjectService = Depends()):
    if current_user.type.name in ("admin", "user"):
        return await service.get_all_object(current_user)
    else:
        return message_error[status.HTTP_406_NOT_ACCEPTABLE]


@router.delete("/{uuid}", responses={
    status.HTTP_406_NOT_ACCEPTABLE: {"model": Message},
    status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message},
    status.HTTP_200_OK: {"model": Message},
})
async def delete_object(uuid: str,
                        service: ObjectService = Depends(),
                        current_user: UserGet = Depends(get_current_user)):
    if current_user.type.name == "admin":
        try:
            await service.delete_object(uuid)
            return JSONResponse(content={"message": "Удалено"},
                                status_code=status.HTTP_200_OK)
        except Exception:
            return JSONResponse(content={"message": "ошибка удаления"},
                                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        return message_error[status.HTTP_406_NOT_ACCEPTABLE]


@router.put("/{uuid}", responses={
    status.HTTP_406_NOT_ACCEPTABLE: {"model": Message},
    status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message},
    status.HTTP_200_OK: {"model": Message},
})
async def update_object(uuid: str,
                        target_obj: UpdateObject,
                        service: ObjectService = Depends(),
                        current_user: UserGet = Depends(get_current_user)
                        ):
    if current_user.type.name == "admin":
        try:
            await service.update_object(uuid, target_obj)
            return JSONResponse(content={"message": "Обновленно"},
                                status_code=status.HTTP_200_OK)
        except Exception:
            return JSONResponse(content={"message": "ошибка обновления"},
                                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        return message_error[status.HTTP_406_NOT_ACCEPTABLE]


@router.get("/one/{uuid}", response_model=GetObject,
            responses={
                status.HTTP_406_NOT_ACCEPTABLE: {"model": Message},
                status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message},
                status.HTTP_200_OK: {"model": Message},
                status.HTTP_404_NOT_FOUND: {"model": Message}
            })
async def get_one_object(uuid: str,
                         service: ObjectService = Depends(),
                         current_user: UserGet = Depends(get_current_user)
):
    if current_user.type.name in ("admin", "user"):
        obj = await service.get_one(uuid)
        if obj is not None:
            return obj
        else:
            return JSONResponse(content={"message": " не существует"},
                                status_code=status.HTTP_404_NOT_FOUND)


@router.get("/equipment/type_equip", response_model=list[TypeEquipment], responses={
    status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message},
})
async def get_type_equipment(service: EquipmentService = Depends()):
    state = await service.get_all_type_equip()
    return state


@router.post("/equipment/type_equip/import_file", responses={
    status.HTTP_406_NOT_ACCEPTABLE: {"model": Message},
    status.HTTP_201_CREATED: {"model": Message},
    status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message}
})
async def import_type_equip(file: UploadFile = File(...),
                            service: EquipmentService = Depends(),
                            current_user: UserGet = Depends(get_current_user)):
    if current_user.type.name == "admin":
        try:
            if file.content_type == "text/csv":
                await service.import_type_equip_file(file)
            else:
                return JSONResponse(content={"message": "файл не того типа"},
                                   status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

            return JSONResponse(content={"message": "добавлено"},
                                status_code=status.HTTP_201_CREATED)
        except Exception:
            return JSONResponse(content={"message": "ошибка добавления"},
                                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        return message_error[status.HTTP_406_NOT_ACCEPTABLE]


@router.get("/{uuid}/equipment/page", response_model=list[GetEquipment],
            responses={
                status.HTTP_406_NOT_ACCEPTABLE: {"model": Message},
                status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message},
                status.HTTP_200_OK: {"model": Message}
            })
async def get_page_equipment(
        uuid: str,
        response: Response,
        page: int = 1,
        type_equip: str | None = None,
        current_user: UserGet = Depends(get_current_user),
        service: EquipmentService = Depends()):
    if current_user.type.name in ("admin", "user"):
        count_page = await service.get_count_page(uuid)
        response.headers["X-Count-Page"] = str(count_page)
        response.headers["X-Count-Item"] = str(service.count_item)
        return await service.get_page_equip(uuid, page)
    else:
        return message_error[status.HTTP_406_NOT_ACCEPTABLE]


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
        count: int = 5,
        service: EquipmentService = Depends(),
        current_user: UserGet = Depends(get_current_user)
):
    equipment = await service.get_equipment_by_search_field(uuid, search_field, count)
    return equipment


@router.get("/{uuid}/equipment/list", response_model=list[GetEquipment],
            responses={
                status.HTTP_406_NOT_ACCEPTABLE: {"model": Message},
                status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message},
                status.HTTP_200_OK: {"model": Message}
            })
async def get_all_equipment(
        uuid: str,
        current_user: UserGet = Depends(get_current_user),
        service: EquipmentService = Depends()):
    if current_user.type.name in ("admin", "user"):
        return await service.get_all_equip(uuid)
    else:
        return message_error[status.HTTP_406_NOT_ACCEPTABLE]


@router.get("/equipment/{uuid}", response_model=GetEquipment,
            responses={
                status.HTTP_406_NOT_ACCEPTABLE: {"model": Message},
                status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message},
                status.HTTP_200_OK: {"model": Message},
                status.HTTP_404_NOT_FOUND: {"model": Message}
            })
async def get_one_equipment(uuid: str,
                            service: EquipmentService = Depends(),
                            current_user: UserGet = Depends(get_current_user)
):
    if current_user.type.name in ("admin", "user"):
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
    if (is_edit and current_user.type.name == "user") or current_user.type.name == "admin":
        try:
            await service.create_equip(uuid, equipment_target)
            return JSONResponse(content={"message": "добавлено"},
                                status_code=status.HTTP_201_CREATED)
        except Exception:
            return JSONResponse(content={"message": "ошибка добавления"},
                                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        return message_error[status.HTTP_406_NOT_ACCEPTABLE]


@router.delete("/equipment/{uuid}", responses={
    status.HTTP_406_NOT_ACCEPTABLE: {"model": Message},
    status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message},
    status.HTTP_200_OK: {"model": Message},
})
async def delete_equipment(
        uuid: str,
        service: EquipmentService = Depends(),
        service_object: ObjectService = Depends(),
        current_user: UserGet = Depends(get_current_user)):
    is_edit = await service_object.is_user_in_object(current_user, uuid)
    if (is_edit and current_user.type.name == "user") or current_user.type.name == "admin":
        try:
            await service.delete_equip(uuid)
            return JSONResponse(content={"message": "Удалено"},
                                status_code=status.HTTP_200_OK)
        except Exception:
            return JSONResponse(content={"message": "ошибка удаления"},
                                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        return message_error[status.HTTP_406_NOT_ACCEPTABLE]


@router.put("/equipment/{uuid}", responses={
    status.HTTP_406_NOT_ACCEPTABLE: {"model": Message},
    status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message},
    status.HTTP_200_OK: {"model": Message},
})
async def update_equipment(uuid: str,
                           target_equipment: UpdateEquipment,
                           service: EquipmentService = Depends(),
                           service_object: ObjectService = Depends(),
                           current_user: UserGet = Depends(get_current_user)):
    is_edit = await service_object.is_user_in_object(current_user, uuid)
    if (is_edit and current_user.type.name == "user") or current_user.type.name == "admin":
        try:
            await service.update_equip(uuid, target_equipment)
            return JSONResponse(content={"message": "Обновленно"},
                                status_code=status.HTTP_200_OK)
        except Exception:
            return JSONResponse(content={"message": "ошибка обновления"},
                                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        return message_error[status.HTTP_406_NOT_ACCEPTABLE]


@router.get("/{uuid}/users", response_model=list[UserGet],
            responses={
                status.HTTP_406_NOT_ACCEPTABLE: {"model": Message},
                status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message},
                status.HTTP_200_OK: {"model": Message}
            })
async def get_users_to_object(
        uuid: str,
        current_user: UserGet = Depends(get_current_user),
        service: ObjectService = Depends()):
    if current_user.type.name == "admin":
        return await service.get_users_object(uuid)
    else:
        return message_error[status.HTTP_406_NOT_ACCEPTABLE]


@router.post("/{uuid_object}/user/{uuid_user}", responses={
    status.HTTP_406_NOT_ACCEPTABLE: {"model": Message},
    status.HTTP_201_CREATED: {"model": Message},
    status.HTTP_200_OK: {"model": Message},
    status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message}
})
async def registrate_user_to_object(uuid_object: str,
                                    uuid_user: str,
                                    service: ObjectService = Depends(),
                                    current_user: UserGet = Depends(get_current_user)):
    if current_user.type.name == "admin":
        try:
            is_add = await service.registrate_user(uuid_object, uuid_user)
            if is_add:
                return JSONResponse(content={"message": "добавлено"},
                                    status_code=status.HTTP_201_CREATED)
            else:
                return JSONResponse(content={"message": "ужу существует или прикреплен к другому объекту"},
                                    status_code=status.HTTP_200_OK)
        except Exception:
            return JSONResponse(content={"message": "ошибка добавления"},
                                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        return message_error[status.HTTP_406_NOT_ACCEPTABLE]


@router.delete("/{uuid_object}/user/{uuid_user}", responses={
    status.HTTP_406_NOT_ACCEPTABLE: {"model": Message},
    status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message},
    status.HTTP_200_OK: {"model": Message},
})
async def delete_user_to_object(uuid_object: str,
                                uuid_user: str,
                                service: ObjectService = Depends(),
                                current_user: UserGet = Depends(get_current_user)):
    if current_user.type.name == "admin":
        try:
            await service.delete_user_in_object(uuid_object, uuid_user)
            return JSONResponse(content={"message": "Удалено"},
                                status_code=status.HTTP_200_OK)
        except Exception:
            return JSONResponse(content={"message": "ошибка удаления"},
                                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        return message_error[status.HTTP_406_NOT_ACCEPTABLE]


@router.get("/get_object_to_user", responses={
    status.HTTP_406_NOT_ACCEPTABLE: {"model": Message},
    status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message},
    status.HTTP_200_OK: {"model": Message},
})
async def get_object_to_user(service: ObjectService = Depends(),
                             current_user: UserGet = Depends(get_current_user)):
    if current_user.type.name == "user":
        obj = await service.get_object_to_user(current_user.uuid)
        if obj is not None:
            return obj
        else:
            return JSONResponse(content={"message": " не существует"},
                                status_code=status.HTTP_404_NOT_FOUND)