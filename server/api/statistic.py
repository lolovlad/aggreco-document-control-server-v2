from fastapi import APIRouter, Depends, status, Request, Response, Query
from fastapi.responses import JSONResponse, StreamingResponse
from typing import Optional, List
import io

from ..models.User import UserGet
from ..models.Statistic import (
    GetAllStatistic,
    ObjectDetailStatistic,
    GetMonthlyStatistic,
    GetClassBrakeStatistic,
    GetTypeBrakeStatistic,
    GetMonthlyClassBrakeStatistic,
)
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


@router.get("/accident", response_model=GetAllStatistic)
@access_control(["super_admin", "admin"])
async def get_accident_statistic_universal(
        start_date: Optional[str] = Query(None, description="Начальная дата в формате YYYY-MM-DD"),
        end_date: Optional[str] = Query(None, description="Конечная дата в формате YYYY-MM-DD"),
        list_object: Optional[List[str]] = Query(None, description="Список UUID объектов для фильтрации"),
        sort_by: Optional[str] = Query("claim_count", description="Поле для сортировки: 'claim_count' или 'object_name'"),
        sort_order: Optional[str] = Query("desc", description="Порядок сортировки: 'asc' или 'desc'"),
        current_user: UserGet = Depends(get_current_user),
        service: StatisticService = Depends()
):
    """
    Универсальный endpoint для получения статистики заявок с поддержкой фильтров и сортировки.
    Все параметры опциональны.
    """
    return await service.get_accident_statistic_universal(
        start_date=start_date,
        end_date=end_date,
        list_object=list_object,
        sort_by=sort_by,
        sort_order=sort_order
    )


@router.get("/accident/monthly", response_model=GetMonthlyStatistic)
@access_control(["super_admin", "admin"])
async def get_accident_statistic_by_month(
        start_date: Optional[str] = Query(None, description="Начальная дата в формате YYYY-MM-DD"),
        end_date: Optional[str] = Query(None, description="Конечная дата в формате YYYY-MM-DD"),
        list_object: Optional[List[str]] = Query(None, description="Список UUID объектов для фильтрации"),
        sort_by: Optional[str] = Query("claim_count", description="Поле для сортировки: 'claim_count' или 'object_name'"),
        sort_order: Optional[str] = Query("desc", description="Порядок сортировки: 'asc' или 'desc'"),
        current_user: UserGet = Depends(get_current_user),
        service: StatisticService = Depends()
):
    """
    Endpoint для получения статистики заявок, сгруппированной по месяцам и объектам.
    Все параметры опциональны.
    """
    return await service.get_accident_statistic_by_month(
        start_date=start_date,
        end_date=end_date,
        list_object=list_object,
        sort_by=sort_by,
        sort_order=sort_order
    )


@router.get("/accident/class", response_model=GetClassBrakeStatistic)
@access_control(["super_admin", "admin"])
async def get_accident_statistic_group_by_class(
        start_date: Optional[str] = Query(None, description="Начальная дата в формате YYYY-MM-DD"),
        end_date: Optional[str] = Query(None, description="Конечная дата в формате YYYY-MM-DD"),
        list_object: Optional[List[str]] = Query(None, description="Список UUID объектов для фильтрации"),
        sort_by: Optional[str] = Query("claim_count", description="Поле для сортировки: 'claim_count' или 'object_name'"),
        sort_order: Optional[str] = Query("desc", description="Порядок сортировки: 'asc' или 'desc'"),
        current_user: UserGet = Depends(get_current_user),
        service: StatisticService = Depends()
):
    """
    Статистика заявок по объектам, сгруппированная по классам отказов (ClassBrake).
    """
    return await service.get_accident_statistic_group_by_class(
        start_date=start_date,
        end_date=end_date,
        list_object=list_object,
        sort_by=sort_by,
        sort_order=sort_order,
    )


@router.get("/accident/type", response_model=GetTypeBrakeStatistic)
@access_control(["super_admin", "admin"])
async def get_accident_statistic_group_by_type(
        start_date: Optional[str] = Query(None, description="Начальная дата в формате YYYY-MM-DD"),
        end_date: Optional[str] = Query(None, description="Конечная дата в формате YYYY-MM-DD"),
        list_object: Optional[List[str]] = Query(None, description="Список UUID объектов для фильтрации"),
        sort_by: Optional[str] = Query("claim_count", description="Поле для сортировки: 'claim_count' или 'object_name'"),
        sort_order: Optional[str] = Query("desc", description="Порядок сортировки: 'asc' или 'desc'"),
        current_user: UserGet = Depends(get_current_user),
        service: StatisticService = Depends()
):
    """
    Статистика заявок по объектам, сгруппированная по типам отказов (TypeBrake).
    """
    return await service.get_accident_statistic_group_by_type(
        start_date=start_date,
        end_date=end_date,
        list_object=list_object,
        sort_by=sort_by,
        sort_order=sort_order,
    )


@router.get("/accident/monthly/class", response_model=GetMonthlyClassBrakeStatistic)
@access_control(["super_admin", "admin"])
async def get_accident_statistic_by_month_and_class(
        start_date: Optional[str] = Query(None, description="Начальная дата в формате YYYY-MM-DD"),
        end_date: Optional[str] = Query(None, description="Конечная дата в формате YYYY-MM-DD"),
        list_object: Optional[List[str]] = Query(None, description="Список UUID объектов для фильтрации"),
        sort_by: Optional[str] = Query("claim_count", description="Поле для сортировки: 'claim_count' или 'object_name'"),
        sort_order: Optional[str] = Query("desc", description="Порядок сортировки: 'asc' или 'desc'"),
        current_user: UserGet = Depends(get_current_user),
        service: StatisticService = Depends()
):
    """
    Статистика заявок по объектам, сгруппированная по месяцам и классам отказов (ClassBrake).
    """
    return await service.get_accident_statistic_by_month_and_class(
        start_date=start_date,
        end_date=end_date,
        list_object=list_object,
        sort_by=sort_by,
        sort_order=sort_order,
    )


@router.get("/accident/{uuid_object}/class", response_model=GetClassBrakeStatistic)
@access_control(["super_admin", "admin"])
async def get_accident_statistic_group_by_class_for_object(
        uuid_object: str,
        start_date: Optional[str] = Query(None, description="Начальная дата в формате YYYY-MM-DD"),
        end_date: Optional[str] = Query(None, description="Конечная дата в формате YYYY-MM-DD"),
        sort_by: Optional[str] = Query("claim_count", description="Поле для сортировки: 'claim_count' или 'object_name'"),
        sort_order: Optional[str] = Query("desc", description="Порядок сортировки: 'asc' или 'desc'"),
        current_user: UserGet = Depends(get_current_user),
        service: StatisticService = Depends()
):
    """
    Статистика заявок по одному объекту, сгруппированная по классам отказов (ClassBrake).
    """
    return await service.get_accident_statistic_group_by_class_for_object(
        uuid_object=uuid_object,
        start_date=start_date,
        end_date=end_date,
        sort_by=sort_by,
        sort_order=sort_order,
    )


@router.get("/accident/{uuid_object}/type", response_model=GetTypeBrakeStatistic)
@access_control(["super_admin", "admin"])
async def get_accident_statistic_group_by_type_for_object(
        uuid_object: str,
        start_date: Optional[str] = Query(None, description="Начальная дата в формате YYYY-MM-DD"),
        end_date: Optional[str] = Query(None, description="Конечная дата в формате YYYY-MM-DD"),
        sort_by: Optional[str] = Query("claim_count", description="Поле для сортировки: 'claim_count' или 'object_name'"),
        sort_order: Optional[str] = Query("desc", description="Порядок сортировки: 'asc' или 'desc'"),
        current_user: UserGet = Depends(get_current_user),
        service: StatisticService = Depends()
):
    """
    Статистика заявок по одному объекту, сгруппированная по типам отказов (TypeBrake).
    """
    return await service.get_accident_statistic_group_by_type_for_object(
        uuid_object=uuid_object,
        start_date=start_date,
        end_date=end_date,
        sort_by=sort_by,
        sort_order=sort_order,
    )


@router.get("/accident/{uuid_object}/monthly/class", response_model=GetMonthlyClassBrakeStatistic)
@access_control(["super_admin", "admin"])
async def get_accident_statistic_by_month_and_class_for_object(
        uuid_object: str,
        start_date: Optional[str] = Query(None, description="Начальная дата в формате YYYY-MM-DD"),
        end_date: Optional[str] = Query(None, description="Конечная дата в формате YYYY-MM-DD"),
        sort_by: Optional[str] = Query("claim_count", description="Поле для сортировки: 'claim_count' или 'object_name'"),
        sort_order: Optional[str] = Query("desc", description="Порядок сортировки: 'asc' или 'desc'"),
        current_user: UserGet = Depends(get_current_user),
        service: StatisticService = Depends()
):
    """
    Статистика заявок по одному объекту, сгруппированная по месяцам и классам отказов (ClassBrake).
    """
    return await service.get_accident_statistic_by_month_and_class_for_object(
        uuid_object=uuid_object,
        start_date=start_date,
        end_date=end_date,
        sort_by=sort_by,
        sort_order=sort_order,
    )


@router.get("/object/{uuid_object}", response_model=ObjectDetailStatistic)
@access_control(["super_admin", "admin"])
async def get_object_statistic(
        uuid_object: str,
        type_filter: str,
        param: str,
        current_user: UserGet = Depends(get_current_user),
        service: StatisticService = Depends()
):
    return await service.get_object_statistic(uuid_object, type_filter, param)


@router.get("/export/csv")
@access_control(["super_admin", "admin"])
async def export_statistics_to_csv(
        start_date: Optional[str] = Query(None, description="Начальная дата в формате YYYY-MM-DD"),
        end_date: Optional[str] = Query(None, description="Конечная дата в формате YYYY-MM-DD"),
        list_object: Optional[List[str]] = Query(None, description="Список UUID объектов для фильтрации"),
        current_user: UserGet = Depends(get_current_user),
        service: StatisticService = Depends()
):
    """
    Экспорт статистики в CSV формат.
    Включает данные: ClassBrake, TypeBrake, Accident (без time_line, event, state_accident, time_zone),
    Claim (без state_claim, main_document, edit_document, comment, last_datetime_edit).
    """
    csv_content = await service.export_to_csv(
        start_date=start_date,
        end_date=end_date,
        list_object=list_object,
    )

    # Создаем поток для CSV
    csv_bytes = csv_content.encode('utf-8-sig')  # BOM для правильного отображения кириллицы в Excel
    csv_stream = io.BytesIO(csv_bytes)

    # Формируем имя файла с датой
    from datetime import datetime
    filename = f"statistics_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

    return StreamingResponse(
        iter([csv_stream.getvalue()]),
        media_type="text/csv; charset=utf-8-sig",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Type": "text/csv; charset=utf-8-sig"
        }
    )
