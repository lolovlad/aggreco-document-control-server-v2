from fastapi import APIRouter, Depends, status, Request, Response, UploadFile, File
from fastapi.responses import JSONResponse, RedirectResponse

from ..services import AccidentService, get_current_user
from ..models.Accident import GetTypeBrake, GetLightweightAccident, PostAccident, GetAccident, UpdateAccident, TimeLine
from ..models.Message import Message
from ..models.User import UserGet
from ..models.Event import GetEvent, PostEvent, UpdateEvent, StateEvent, TypeEvent


router = APIRouter(prefix="/accident", tags=["accident"])


message_error = {
    status.HTTP_406_NOT_ACCEPTABLE: JSONResponse(content={"message": "отказ в доступе"},
                                                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
}


@router.get("/type_brake_mechanical/{class_brake}", response_model=list[GetTypeBrake], responses={
    status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message},
    status.HTTP_404_NOT_FOUND: {"model": Message},
})
async def get_type_brake(class_brake: str,
                         service: AccidentService = Depends()):
    type_brake = await service.get_all_type_brake(class_brake)
    if type_brake is not None:
        return type_brake
    else:
        JSONResponse(content={"message": "Не найдено"},
                     status_code=status.HTTP_404_NOT_FOUND)


@router.post("/type_brake/{class_brake}/import_file", responses={
    status.HTTP_406_NOT_ACCEPTABLE: {"model": Message},
    status.HTTP_201_CREATED: {"model": Message},
    status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message}
})
async def import_type_brake(class_brake: str,
                            file: UploadFile = File(...),
                            service: AccidentService = Depends(),
                            current_user: UserGet = Depends(get_current_user)):
    if current_user.type.name == "admin":
        try:
            if file.content_type == "text/csv":
                await service.import_type_brake_file(class_brake, file)
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


@router.get("/page", response_model=list[GetLightweightAccident],
            responses={
                status.HTTP_406_NOT_ACCEPTABLE: {"model": Message},
                status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message},
                status.HTTP_200_OK: {"model": Message}
            })
async def get_page_accident(
        response: Response,
        page: int = 1,
        uuid_object: str | None = None,
        current_user: UserGet = Depends(get_current_user),
        service: AccidentService = Depends()):

    if current_user.type.name == "admin":
        count_page = await service.get_count_page(uuid_object)
        response.headers["X-Count-Page"] = str(count_page)
        response.headers["X-Count-Item"] = str(service.count_item)
        return await service.get_page_accident(uuid_object, page)
    else:
        return message_error[status.HTTP_406_NOT_ACCEPTABLE]


@router.post("/", responses={
    status.HTTP_406_NOT_ACCEPTABLE: {"model": Message},
    status.HTTP_201_CREATED: {"model": Message},
    status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message}
})
async def add_accident(accident: PostAccident,
                       current_user: UserGet = Depends(get_current_user),
                       service: AccidentService = Depends()):
    if current_user.type.name == "admin":
        try:
            await service.add_accident(accident)
            return JSONResponse(content={"message": "добавлено"},
                                status_code=status.HTTP_201_CREATED)
        except Exception:
            return JSONResponse(content={"message": "ошибка добавления"},
                                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        return message_error[status.HTTP_406_NOT_ACCEPTABLE]


@router.get("/{uuid}", response_model=GetAccident,
            responses={
                status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message},
                status.HTTP_200_OK: {"model": Message},
                status.HTTP_404_NOT_FOUND: {"model": Message}
            })
async def get_one_accident(uuid: str,
                           service: AccidentService = Depends(),
):
    obj = await service.get_one(uuid)
    if obj is not None:
        return obj
    else:
        return JSONResponse(content={"message": " не существует"},
                            status_code=status.HTTP_404_NOT_FOUND)


@router.put("/{uuid}", responses={
    status.HTTP_406_NOT_ACCEPTABLE: {"model": Message},
    status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message},
    status.HTTP_200_OK: {"model": Message},
})
async def update_equipment(uuid: str,
                           target_accident: UpdateAccident,
                           service: AccidentService = Depends(),
                           current_user: UserGet = Depends(get_current_user)):
    if current_user.type.name == "admin":
        try:
            await service.update_accident(uuid, target_accident)
            return JSONResponse(content={"message": "Обновленно"},
                                status_code=status.HTTP_200_OK)
        except Exception:
            return JSONResponse(content={"message": "ошибка обновления"},
                                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        return message_error[status.HTTP_406_NOT_ACCEPTABLE]


@router.post("/{uuid}/time_line", responses={
    status.HTTP_406_NOT_ACCEPTABLE: {"model": Message},
    status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message}
}, response_model=list[TimeLine])
async def add_time_line_item(uuid: str,
                             target: TimeLine,
                             service: AccidentService = Depends(),
                             current_user: UserGet = Depends(get_current_user)):
    if current_user.type.name == "admin":
        try:
            time_line_series = await service.add_time_line(uuid, target)
            return time_line_series
        except Exception:
            return JSONResponse(content={"message": "ошибка обновления"},
                                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        return message_error[status.HTTP_406_NOT_ACCEPTABLE]


@router.get("/{uuid}/time_line", responses={
                status.HTTP_406_NOT_ACCEPTABLE: {"model": Message},
                status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message},
                status.HTTP_404_NOT_FOUND: {"model": Message}
            }, response_model=list[TimeLine])
async def get_time_line(uuid: str,
                        service: AccidentService = Depends(),
                        current_user: UserGet = Depends(get_current_user)
):
    if current_user.type.name == "admin":
        time_line_series = await service.get_time_line(uuid)
        if time_line_series is not None:
            return time_line_series
        else:
            return JSONResponse(content={"message": " не существует"},
                                status_code=status.HTTP_404_NOT_FOUND)


@router.put("/{uuid}/time_line", responses={
    status.HTTP_406_NOT_ACCEPTABLE: {"model": Message},
    status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message},
    status.HTTP_200_OK: {"model": Message},
}, response_model=list[TimeLine])
async def update_time_line(uuid: str,
                           target_time_line: TimeLine,
                           service: AccidentService = Depends(),
                           current_user: UserGet = Depends(get_current_user)):
    if current_user.type.name == "admin":
        try:
            time_line_target = await service.update_time_line(uuid, target_time_line)
            return time_line_target
        except Exception:
            return JSONResponse(content={"message": "ошибка обновления"},
                                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        return message_error[status.HTTP_406_NOT_ACCEPTABLE]


@router.delete("/{uuid}/time_line/{uuid_time_line}", responses={
    status.HTTP_406_NOT_ACCEPTABLE: {"model": Message},
    status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message},
    status.HTTP_200_OK: {"model": Message},
}, response_model=list[TimeLine])
async def delete_time_line(uuid: str,
                           uuid_time_line: str,
                           service: AccidentService = Depends(),
                           current_user: UserGet = Depends(get_current_user)):
    if current_user.type.name == "admin":
        try:
            time_line_target = await service.delete_time_line(uuid, uuid_time_line)
            return time_line_target
        except Exception:
            return JSONResponse(content={"message": "ошибка обновления"},
                                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        return message_error[status.HTTP_406_NOT_ACCEPTABLE]


@router.post("/{uuid}/event", responses={
    status.HTTP_406_NOT_ACCEPTABLE: {"model": Message},
    status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message}
}, response_model=list[GetEvent])
async def add_event(uuid: str,
                    target: PostEvent,
                    service: AccidentService = Depends(),
                    current_user: UserGet = Depends(get_current_user)):
    if current_user.type.name == "admin":
        try:
            event_list = await service.add_event(uuid, target)
            return event_list
        except Exception:
            return JSONResponse(content={"message": "ошибка обновления"},
                                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        return message_error[status.HTTP_406_NOT_ACCEPTABLE]


@router.get("/{uuid}/event", responses={
                status.HTTP_406_NOT_ACCEPTABLE: {"model": Message},
                status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message},
                status.HTTP_404_NOT_FOUND: {"model": Message}
            }, response_model=list[GetEvent])
async def get_events(uuid: str,
                     service: AccidentService = Depends(),
                     current_user: UserGet = Depends(get_current_user)
):
    if current_user.type.name == "admin":
        list_event = await service.get_list_event(uuid)
        if list_event is not None:
            return list_event
        else:
            return JSONResponse(content={"message": " не существует"},
                                status_code=status.HTTP_404_NOT_FOUND)


@router.get("/{uuid}/event/{uuid_event}", responses={
                status.HTTP_406_NOT_ACCEPTABLE: {"model": Message},
                status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message},
                status.HTTP_404_NOT_FOUND: {"model": Message}
            }, response_model=GetEvent)
async def get_one_event(uuid: str,
                        uuid_event: str,
                        service: AccidentService = Depends(),
                        current_user: UserGet = Depends(get_current_user)
):
    if current_user.type.name == "admin":
        event = await service.get_one_event(uuid_event)
        if event is not None:
            return event
        else:
            return JSONResponse(content={"message": " не существует"},
                                status_code=status.HTTP_404_NOT_FOUND)


@router.put("/{uuid}/event", responses={
    status.HTTP_406_NOT_ACCEPTABLE: {"model": Message},
    status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message},
    status.HTTP_200_OK: {"model": Message},
}, response_model=list[GetEvent])
async def update_event(uuid: str,
                       target_event: UpdateEvent,
                       service: AccidentService = Depends(),
                       current_user: UserGet = Depends(get_current_user)):
    if current_user.type.name == "admin":
        try:
            list_event = await service.update_event(uuid, target_event)
            return list_event
        except Exception:
            return JSONResponse(content={"message": "ошибка обновления"},
                                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        return message_error[status.HTTP_406_NOT_ACCEPTABLE]


@router.delete("/{uuid}/event/{uuid_event}", responses={
    status.HTTP_406_NOT_ACCEPTABLE: {"model": Message},
    status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message},
    status.HTTP_200_OK: {"model": Message},
}, response_model=list[GetEvent])
async def delete_time_line(uuid: str,
                           uuid_event: str,
                           service: AccidentService = Depends(),
                           current_user: UserGet = Depends(get_current_user)):
    if current_user.type.name == "admin":
        try:
            list_event = await service.delete_event(uuid, uuid_event)
            return list_event
        except Exception:
            return JSONResponse(content={"message": "ошибка обновления"},
                                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        return message_error[status.HTTP_406_NOT_ACCEPTABLE]


@router.get("/event/state_event", response_model=list[StateEvent], responses={
    status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message},
    status.HTTP_404_NOT_FOUND: {"model": Message},
})
async def get_state_event(service: AccidentService = Depends()):
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
async def get_type_event(service: AccidentService = Depends()):
    type_event = await service.get_list_type_event()
    if type_event is not None:
        return type_event
    else:
        JSONResponse(content={"message": "Не найдено"},
                     status_code=status.HTTP_404_NOT_FOUND)