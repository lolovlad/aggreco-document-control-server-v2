from pydantic import BaseModel, UUID4, field_serializer
from datetime import datetime
from typing import Dict, Any, Optional

from .Equipment import GetEquipment


class BaseSummarize(BaseModel):
    text: str
    metadata_equipment: Dict[str, Any]


class GetSummarize(BaseSummarize):
    uuid: UUID4
    uuid_object: str
    uuid_equipment: str
    datetime_start: datetime
    datetime_end: Optional[datetime] = None
    equipment: Optional[GetEquipment] = None
    equipment_uuid: Optional[str] = None
    equipment_name: Optional[str] = None

    @field_serializer("uuid")
    def serialize_uuid(self, uuid: UUID4, _info):
        return str(uuid)


class PostSummarize(BaseSummarize):
    uuid_object: str
    uuid_equipment: str


class AnalyzeLogsResponse(BaseModel):
    """Ответ от анализа логов"""
    text: str  # Markdown ответ от LLM
    metadata: Dict[str, Any]  # Структурированные данные для отображения
