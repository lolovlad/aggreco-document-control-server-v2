from fastapi import APIRouter, Depends, status, Request, Response, UploadFile, File
from fastapi.responses import JSONResponse, StreamingResponse

from ..services import EnvService, get_current_user
from ..models.User import GetTypeUser, Profession


from ..models.Message import Message
from ..models.User import UserGet
from ..models.Equipment import TypeEquipment, PostTypeEquipment
from ..models.Object import StateObject, Region, PostRegion
from ..models.Accident import SignsAccident, GetTypeBrake
from ..models.Event import StateEvent, TypeEvent
from ..models.Claim import StateClaimModel

from ..repositories import FileBucketRepository
from ..functions import access_control


router = APIRouter(prefix="/env", tags=["env"])


message_error = {
    status.HTTP_406_NOT_ACCEPTABLE: JSONResponse(content={"message": "отказ в доступе"},
                                                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
}


@router.get("/type_user", responses={
    status.HTTP_406_NOT_ACCEPTABLE: {"model": Message},
    status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message}
}, response_model=list[GetTypeUser])
async def get_type_user(service: EnvService = Depends(),
                        current_user: UserGet = Depends(get_current_user)):
    type_users = await service.get_type_users()
    return type_users


@router.get("/profession", responses={
    status.HTTP_406_NOT_ACCEPTABLE: {"model": Message},
    status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message}
}, response_model=list[Profession])
async def get_user_profession(service: EnvService = Depends(),
                              current_user: UserGet = Depends(get_current_user)):
    prof_users = await service.get_profession_user()
    return prof_users


@router.post("/profession", responses={
    status.HTTP_406_NOT_ACCEPTABLE: {"model": Message},
    status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message}
})
@access_control(["super_admin"])
async def add_profession(prof: Profession,
                         service: EnvService = Depends(),
                         current_user: UserGet = Depends(get_current_user)):
    prof_users = await service.add_profession(prof.name, prof.description)
    return JSONResponse(content={"message": "добавлено"},
                        status_code=status.HTTP_201_CREATED)


@router.delete("/profession/{id_prof}", responses={
    status.HTTP_406_NOT_ACCEPTABLE: {"model": Message},
    status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message}
})
@access_control(["super_admin"])
async def delete_profession(id_prof: int,
                            service: EnvService = Depends(),
                            current_user: UserGet = Depends(get_current_user)):
    prof = await service.delete_prof(id_prof)
    if prof:
        return JSONResponse(status_code=status.HTTP_200_OK,
                            content={"message": "Удалено"})
    else:
        return JSONResponse(content={"message": "ошибка удаление"},
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.get("/type_equip", response_model=list[TypeEquipment], responses={
    status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message},
})
async def get_type_equipment(service: EnvService = Depends()):
    state = await service.get_all_type_equip()
    return state


@router.post("/type_equip", responses={
    status.HTTP_406_NOT_ACCEPTABLE: {"model": Message},
    status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message}
})
@access_control(["super_admin"])
async def add_type_equipment(type_equipment: PostTypeEquipment,
                             service: EnvService = Depends(),
                             current_user: UserGet = Depends(get_current_user)):
    type_equipment = await service.add_type_equipment(type_equipment)
    return JSONResponse(content={"message": "добавлено"},
                        status_code=status.HTTP_201_CREATED)


@router.delete("/type_equip/{id_type_equipment}", responses={
    status.HTTP_406_NOT_ACCEPTABLE: {"model": Message},
    status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message}
})
@access_control(["super_admin"])
async def delete_type_equipment(id_type_equipment: int,
                                service: EnvService = Depends(),
                                current_user: UserGet = Depends(get_current_user)):
    type_equip = await service.delete_type_equipment(id_type_equipment)
    if type_equip:
        return JSONResponse(status_code=status.HTTP_200_OK,
                            content={"message": "Удалено"})
    else:
        return JSONResponse(content={"message": "ошибка удаление"},
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.post("/type_equip/import_file", responses={
    status.HTTP_406_NOT_ACCEPTABLE: {"model": Message},
    status.HTTP_201_CREATED: {"model": Message},
    status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message}
})
@access_control(["super_admin"])
async def import_type_equip(file: UploadFile = File(...),
                            service: EnvService = Depends(),
                            current_user: UserGet = Depends(get_current_user)):
    try:
        if file.content_type == "text/csv" or file.content_type == "application/vnd.ms-excel":
            await service.import_type_equip_file(file)
        else:
            return JSONResponse(content={"message": "файл не того типа"},
                                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return JSONResponse(content={"message": "добавлено"},
                            status_code=status.HTTP_201_CREATED)
    except Exception:
        return JSONResponse(content={"message": "ошибка добавления"},
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.get("/state_object", response_model=list[StateObject], responses={
    status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message},
})
async def get_state_object(service: EnvService = Depends()):
    state = await service.get_all_state_object()
    return state


@router.get("/region/get_all", response_model=list[Region], responses={
    status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message},
})
async def get_region(service: EnvService = Depends()):
    region = await service.get_all_region()
    return region


@router.post("/region/import_file", responses={
    status.HTTP_406_NOT_ACCEPTABLE: {"model": Message},
    status.HTTP_201_CREATED: {"model": Message},
    status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message}
})
@access_control(["super_admin"])
async def import_region(file: UploadFile = File(...),
                        service: EnvService = Depends(),
                        current_user: UserGet = Depends(get_current_user)):
    try:
        if file.content_type == "text/csv" or file.content_type == "application/vnd.ms-excel":
            await service.import_region_file(file)
        else:
            return JSONResponse(content={"message": "файл не того типа"},
                                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return JSONResponse(content={"message": "добавлено"},
                            status_code=status.HTTP_201_CREATED)
    except Exception:
        return JSONResponse(content={"message": "ошибка добавления"},
                                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.post("/region", responses={
    status.HTTP_406_NOT_ACCEPTABLE: {"model": Message},
    status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message}
})
@access_control(["super_admin"])
async def add_region(region: PostRegion,
                     service: EnvService = Depends(),
                     current_user: UserGet = Depends(get_current_user)):
    await service.add_region(region.name, region.code)
    return JSONResponse(content={"message": "добавлено"},
                        status_code=status.HTTP_201_CREATED)


@router.get("/signs_accident/get_all", response_model=list[SignsAccident], responses={
    status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message},
    status.HTTP_404_NOT_FOUND: {"model": Message},
})
async def get_signs_accident(service: EnvService = Depends()):
    signs_accident = await service.get_all_signs_accident()
    return signs_accident


@router.post("/signs_accident/import_file", responses={
    status.HTTP_406_NOT_ACCEPTABLE: {"model": Message},
    status.HTTP_201_CREATED: {"model": Message},
    status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message}
})
@access_control(["super_admin"])
async def import_signs_accident(file: UploadFile = File(...),
                                service: EnvService = Depends(),
                                current_user: UserGet = Depends(get_current_user)):

    try:
        if file.content_type == "text/csv" or file.content_type == "application/vnd.ms-excel":
            await service.import_signs_accident(file)
        else:
            return JSONResponse(content={"message": "файл не того типа"},
                                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return JSONResponse(content={"message": "добавлено"},
                            status_code=status.HTTP_201_CREATED)
    except Exception:
        return JSONResponse(content={"message": "ошибка добавления"},
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.get("/type_brake_mechanical/{class_brake}", response_model=list[GetTypeBrake], responses={
    status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message},
    status.HTTP_404_NOT_FOUND: {"model": Message},
})
async def get_type_brake(class_brake: str,
                         service: EnvService = Depends()):
    type_brake = await service.get_all_type_brake(class_brake)
    if type_brake is not None:
        return type_brake
    else:
        JSONResponse(content={"message": "Не найдено"},
                     status_code=status.HTTP_404_NOT_FOUND)


@router.post("/type_brake/import_file", responses={
    status.HTTP_406_NOT_ACCEPTABLE: {"model": Message},
    status.HTTP_201_CREATED: {"model": Message},
    status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message}
})
@access_control(["super_admin"])
async def import_type_brake(file: UploadFile = File(...),
                            service: EnvService = Depends(),
                            current_user: UserGet = Depends(get_current_user)):
    try:
        if file.content_type == "text/csv" or file.content_type == "application/vnd.ms-excel":
            await service.import_type_brake_file(file)
        else:
            return JSONResponse(content={"message": "файл не того типа"},
                                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return JSONResponse(content={"message": "добавлено"},
                            status_code=status.HTTP_201_CREATED)
    except Exception:
        return JSONResponse(content={"message": "ошибка добавления"},
                                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.get("/event/state_event", response_model=list[StateEvent], responses={
    status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message},
    status.HTTP_404_NOT_FOUND: {"model": Message},
})
async def get_state_event(service: EnvService = Depends()):
    state_event = await service.get_list_state_event()
    if state_event is not None:
        return state_event
    else:
        JSONResponse(content={"message": "Не найдено"},
                     status_code=status.HTTP_404_NOT_FOUND)


@router.get("/event/type_event", response_model=list[TypeEvent], responses={
    status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message},
    status.HTTP_404_NOT_FOUND: {"model": Message},
})
async def get_type_event(service: EnvService = Depends()):
    type_event = await service.get_list_type_event()
    if type_event is not None:
        return type_event
    else:
        JSONResponse(content={"message": "Не найдено"},
                     status_code=status.HTTP_404_NOT_FOUND)


@router.get("/state_claim", response_model=list[StateClaimModel], responses={
    status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message},
    status.HTTP_404_NOT_FOUND: {"model": Message},
})
async def get_state_claim(service: EnvService = Depends()):
    state_claim = await service.get_state_claim()
    return state_claim