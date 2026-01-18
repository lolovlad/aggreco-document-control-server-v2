from fastapi import APIRouter, Depends, status, Query
from fastapi.responses import JSONResponse
from typing import Optional

from ..models.Summarize import AnalyzeLogsResponse, GetSummarize
from ..models.Message import Message
from ..services.LogAnalysisService import LogAnalysisService
from ..services.SummarizeService import SummarizeService
from ..repositories.LogMessageErrorRepository import LogMessageErrorRepository
from ..repositories.SummarizeRepository import SummarizeRepository
from ..repositories.EquipmentRepository import EquipmentRepository
from ..repositories.ObjectRepository import ObjectRepository
from ..models.User import UserGet
from ..functions import access_control
from ..services.LoginService import get_current_user

router = APIRouter(prefix="/log-analysis", tags=["log-analysis"])


message_error = {
    status.HTTP_406_NOT_ACCEPTABLE: JSONResponse(content={"message": "отказ в доступе"},
                                                 status_code=status.HTTP_406_NOT_ACCEPTABLE)
}


@router.post("/object/{uuid_object}/analyze",
            response_model=dict,
            responses={
                status.HTTP_406_NOT_ACCEPTABLE: {"model": Message},
                status.HTTP_404_NOT_FOUND: {"model": Message},
                status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message},
                status.HTTP_200_OK: {"model": Message}
            })
@access_control(["admin", "super_admin", "user"])
async def analyze_logs_for_object(
    uuid_object: str,
    current_user: UserGet = Depends(get_current_user),
    log_repository: LogMessageErrorRepository = Depends(),
    summarize_repository: SummarizeRepository = Depends(),
    equipment_repository: EquipmentRepository = Depends(),
    object_repository: ObjectRepository = Depends(),
):
    """
    Анализирует логи для выбранного объекта
    
    Логи собираются в событие для каждой машины отдельно.
    Для каждой машины из settings объекта берутся логи со значением is_processed = False.
    После обработки флаг is_processed ставится на True.
    
    LLM анализирует логи и выделяет проблемные места оборудования,
    что происходит постоянно, в каких узлах проблемы.
    
    Если есть Summarize месячной свежести, он передается в LLM для контекста.
    Если Summarize просрочен, он удаляется и создается новый.
    
    Ответ содержит:
    - text: ответ LLM в формате Markdown
    - metadata: структурированные данные в JSON формате (для отображения тегов, частых ошибок)
    """
    try:
        service = LogAnalysisService(
            log_repository=log_repository,
            summarize_repository=summarize_repository,
            equipment_repository=equipment_repository,
            object_repository=object_repository
        )
        
        results = await service.analyze_logs_for_object(uuid_object)
        
        return JSONResponse(
            content=results,
            status_code=status.HTTP_200_OK
        )
    except ValueError as e:
        return JSONResponse(
            content={"message": str(e)},
            status_code=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return JSONResponse(
            content={"message": f"Ошибка при анализе логов: {str(e)}"},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.get("/object/{uuid_object}/summarize",
            response_model=list[GetSummarize],
            responses={
                status.HTTP_406_NOT_ACCEPTABLE: {"model": Message},
                status.HTTP_404_NOT_FOUND: {"model": Message},
                status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message},
                status.HTTP_200_OK: {"model": Message}
            })
@access_control(["admin", "super_admin", "user"])
async def get_summarize_by_object(
    uuid_object: str,
    start_date: Optional[str] = Query(None, description="Начальная дата в формате YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="Конечная дата в формате YYYY-MM-DD"),
    current_user: UserGet = Depends(get_current_user),
    summarize_repository: SummarizeRepository = Depends(),
    equipment_repository: EquipmentRepository = Depends(),
    object_repository: ObjectRepository = Depends(),
):
    """
    Получить все Summarize для объекта с фильтрацией по датам
    
    Возвращает список Summarize с информацией об оборудовании.
    Фильтрация по датам опциональна - можно указать start_date, end_date или оба.
    """
    try:
        service = SummarizeService(
            summarize_repository=summarize_repository,
            equipment_repository=equipment_repository,
            object_repository=object_repository
        )
        
        result = await service.get_summarize_by_object(
            uuid_object=uuid_object,
            start_date=start_date,
            end_date=end_date
        )
        
        return result
    except ValueError as e:
        return JSONResponse(
            content={"message": str(e)},
            status_code=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return JSONResponse(
            content={"message": f"Ошибка при получении Summarize: {str(e)}"},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.get("/object/{uuid_object}/equipment/{uuid_equipment}/summarize",
            response_model=list[GetSummarize],
            responses={
                status.HTTP_406_NOT_ACCEPTABLE: {"model": Message},
                status.HTTP_404_NOT_FOUND: {"model": Message},
                status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message},
                status.HTTP_200_OK: {"model": Message}
            })
@access_control(["admin", "super_admin", "user"])
async def get_summarize_by_object_and_equipment(
    uuid_object: str,
    uuid_equipment: str,
    start_date: Optional[str] = Query(None, description="Начальная дата в формате YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="Конечная дата в формате YYYY-MM-DD"),
    current_user: UserGet = Depends(get_current_user),
    summarize_repository: SummarizeRepository = Depends(),
    equipment_repository: EquipmentRepository = Depends(),
    object_repository: ObjectRepository = Depends(),
):
    """
    Получить все Summarize для объекта и оборудования с фильтрацией по датам
    
    Возвращает список Summarize с информацией об оборудовании.
    Фильтрация по датам опциональна - можно указать start_date, end_date или оба.
    """
    try:
        service = SummarizeService(
            summarize_repository=summarize_repository,
            equipment_repository=equipment_repository,
            object_repository=object_repository
        )
        
        result = await service.get_summarize_by_object_and_equipment(
            uuid_object=uuid_object,
            uuid_equipment=uuid_equipment,
            start_date=start_date,
            end_date=end_date
        )
        
        return result
    except ValueError as e:
        return JSONResponse(
            content={"message": str(e)},
            status_code=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return JSONResponse(
            content={"message": f"Ошибка при получении Summarize: {str(e)}"},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
