from pydantic import BaseModel
from typing import List, Dict, Any


class ObjectStatistic(BaseModel):
    """Статистика по одному объекту"""
    object_uuid: str
    object_name: str
    claim_count: int


class GetAllStatistic(BaseModel):
    """Список статистики по объектам"""
    objects: List[ObjectStatistic] = []


class ObjectDetailStatistic(BaseModel):
    """Детальная статистика по объекту (для совместимости со старыми методами)"""
    obj: Dict[str, Any] = {}


class MonthStatistic(BaseModel):
    """Статистика по одному месяцу"""
    month: str  # Формат: "YYYY-MM"
    objects: List[ObjectStatistic] = []


class GetMonthlyStatistic(BaseModel):
    """Статистика, сгруппированная по месяцам"""
    months: List[MonthStatistic] = []


class ClassBrakeStatisticItem(BaseModel):
    """Одна запись статистики по классу отказа и объекту"""
    object_uuid: str
    object_name: str
    class_brake_id: int
    class_brake_name: str
    claim_count: int


class GetClassBrakeStatistic(BaseModel):
    """Статистика, сгруппированная по ClassBrake"""
    items: List[ClassBrakeStatisticItem] = []


class TypeBrakeStatisticItem(BaseModel):
    """Одна запись статистики по типу отказа и объекту"""
    object_uuid: str
    object_name: str
    type_brake_id: int
    type_brake_name: str
    class_brake_id: int
    class_brake_name: str
    claim_count: int


class GetTypeBrakeStatistic(BaseModel):
    """Статистика, сгруппированная по TypeBrake"""
    items: List[TypeBrakeStatisticItem] = []


class MonthClassBrakeStatisticItem(BaseModel):
    """Одна запись статистики по месяцу, объекту и классу отказа"""
    month: str  # Формат: "YYYY-MM"
    object_uuid: str
    object_name: str
    class_brake_id: int
    class_brake_name: str
    claim_count: int


class GetMonthlyClassBrakeStatistic(BaseModel):
    """Статистика, сгруппированная по месяцам и ClassBrake"""
    items: List[MonthClassBrakeStatisticItem] = []