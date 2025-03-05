from fastapi import APIRouter, Depends, status, Request, Response
from fastapi.responses import JSONResponse

from ..models.User import UserGet
from ..models.Statistic import GetAllStatistic
from ..models.Accident import ClassBrake
from ..services import StatisticService, get_current_user
from ..functions import access_control


router = APIRouter(prefix="/statistic", tags=["statistic"])


message_error = {
    status.HTTP_406_NOT_ACCEPTABLE: JSONResponse(content={"message": "отказ в доступе"},
                                                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
}


@router.get("/type_brake/class", response_model=list[ClassBrake])
async def get_list_class_brake(
        service: StatisticService = Depends()
):
    list_class_brake = await service.get_list_class_brake()
    return list_class_brake


@router.get("/accident/type_brake", response_model=GetAllStatistic)
@access_control(["super_admin", "admin"])
async def get_accident_statistic(
        year: int,
        current_user: UserGet = Depends(get_current_user),
        service: StatisticService = Depends()
):
    return await service.get_accident_statistic(year)


@router.get("/accident/date_slice", response_model=GetAllStatistic)
@access_control(["super_admin", "admin"])
async def get_accident_statistic(
        start_date: str,
        end_date: str,
        current_user: UserGet = Depends(get_current_user),
        service: StatisticService = Depends()
):
    return await service.get_accident_statistic_slice_date(start_date, end_date)


@router.get("/object/{uuid_object}", response_model=GetAllStatistic)
@access_control(["super_admin", "admin"])
async def get_object_statistic(
        uuid_object: str,
        type_filter: str,
        param: str,
        current_user: UserGet = Depends(get_current_user),
        service: StatisticService = Depends()
):
    return await service.get_object_statistic(uuid_object, type_filter, param)
