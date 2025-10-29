from fastapi import (APIRouter, Depends,
                     status, Request,
                     Response, UploadFile,
                     BackgroundTasks, Query)
from fastapi.responses import JSONResponse

from ..services import ProposalsService, get_current_user, EmailService
from ..models.Proposals import (
    GetTechnicalProposals,
    PostTechnicalProposals,
    UpdateTechnicalProposals,
    StateClaimModel
)
from ..models.Message import Message
from ..models.User import UserGet
from ..functions import access_control

from datetime import date


router = APIRouter(prefix="/proposals", tags=["proposals"])


message_error = {
    status.HTTP_406_NOT_ACCEPTABLE: JSONResponse(content={"message": "отказ в доступе"},
                                                 status_code=status.HTTP_406_NOT_ACCEPTABLE)
}


@router.get("/page", response_model=list[GetTechnicalProposals], responses={
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
        service: ProposalsService = Depends()):

    service.count_item = per_item_page
    if current_user.type.name == "user":
        count_page = await service.get_count_page(current_user.uuid,
                                                  uuid_object,
                                                  id_state_claim)
    else:
        count_page = await service.get_count_page(None,
                                                  uuid_object,
                                                  id_state_claim)
    claims = await service.get_page(page,
                                    current_user,
                                    uuid_object,
                                    id_state_claim)

    response.headers["X-Count-Page"] = str(count_page)
    response.headers["X-Count-Item"] = str(service.count_item)
    return claims


@router.post("", responses={
    status.HTTP_406_NOT_ACCEPTABLE: {"model": Message},
    status.HTTP_201_CREATED: {"model": Message},
    status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message}
})
async def add_proposals(proposals: PostTechnicalProposals,
                        background_tasks: BackgroundTasks,
                        current_user: UserGet = Depends(get_current_user),
                        service: ProposalsService = Depends(),
                        notify: EmailService = Depends()):

    try:
        entity = await service.add(current_user, proposals)
        await notify.send_by_context(
            background_tasks,
            "proposals_add",
            "Добавление нового предложения",
            "proposals_edit.html",
            True,
            email_context={"proposal": entity},
            options_user=[]
        )
        return JSONResponse(content={"message": "добавлено"},
                            status_code=status.HTTP_201_CREATED)
    except Exception:
        return JSONResponse(content={"message": "ошибка добавления"},
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.get("/get/{uuid}", responses={
    status.HTTP_406_NOT_ACCEPTABLE: {"model": Message},
    status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message}
}, response_model=GetTechnicalProposals)
async def get_one_proposals(uuid: str,
                            service: ProposalsService = Depends()):
    obj = await service.get(uuid)
    if obj is not None:
        return obj
    else:
        return JSONResponse(content={"message": " не существует"},
                            status_code=status.HTTP_404_NOT_FOUND)


@router.delete("/{uuid}", responses={
    status.HTTP_406_NOT_ACCEPTABLE: {"model": Message},
    status.HTTP_200_OK: {"model": Message},
    status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message}
})
@access_control(["super_admin", "user"])
async def delete_proposals(uuid: str,
                           current_user: UserGet = Depends(get_current_user),
                           service: ProposalsService = Depends()):
    try:
        await service.delete(uuid)
        return JSONResponse(content={"message": "Удалено"},
                            status_code=status.HTTP_200_OK)
    except Exception:
        return JSONResponse(content={"message": "ошибка обновления"},
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.put("/{uuid_proposals}", responses={
    status.HTTP_406_NOT_ACCEPTABLE: {"model": Message},
    status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message},
    status.HTTP_200_OK: {"model": Message},
})
@access_control(["admin", "super_admin"])
async def update_claim(uuid_proposals: str,
                       proposals_model: UpdateTechnicalProposals,
                       background_tasks: BackgroundTasks,
                       current_user: UserGet = Depends(get_current_user),
                       service: ProposalsService = Depends(),
                       notify: EmailService = Depends()
                       ):

    try:
        entity = await service.update(current_user.uuid, uuid_proposals, proposals_model)
        await notify.send_by_context(
            background_tasks,
            "proposals_add",
            "Предложение было рассмотрено",
            "proposals_edit.html",
            True,
            email_context={"proposal": entity},
            options_user=[entity.user]
        )
    except Exception:
        return JSONResponse(content={"message": "ошибка обновления"},
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
