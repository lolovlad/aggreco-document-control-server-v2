from pydantic import BaseModel, UUID4, field_serializer, field_validator
from typing import Dict, Optional

from .User import UserGet


class Region(BaseModel):
    id: int
    name: str
    code: str


class PostRegion(BaseModel):
    name: str
    code: str


class StateObject(BaseModel):
    id: int
    name: str
    description: str


class BaseObject(BaseModel):
    name: str
    address: str
    cx: float | None = 0.0
    cy: float | None = 0.0
    counterparty: str
    id_state: int
    id_region: int | None
    description: str | None


class GetObject(BaseObject):
    uuid: UUID4
    state: StateObject
    region: Region | None

    @field_serializer("uuid")
    def serialize_uuid(self, uuid: UUID4, _info):
        return str(uuid)


class PostObject(BaseObject):
    pass


class UpdateObject(BaseObject):
    pass


class KeyIdNameMapping(BaseModel):
    """Структура для одного сопоставления из keys_id_name"""
    equipment_id: Optional[str] = None  # UUID equipment из БД, если найдено
    field2: Optional[str] = None  # Второе поле (зарезервировано для будущего использования)
    orig_name: str  # Третье поле: оригинальное название из файла


class ObjectSettings(BaseModel):
    db_host: str
    db_port: int
    db_name: str
    db_user: str
    db_password: str
    keys_id_name: Dict[str, KeyIdNameMapping]

    @field_validator('db_port')
    @classmethod
    def validate_port(cls, v: int) -> int:
        if not (1 <= v <= 65535):
            raise ValueError('Порт должен быть в диапазоне от 1 до 65535')
        return v


class GetObjectSettings(BaseModel):
    """Модель для GET запроса - все поля опциональные для обработки пустых settings"""
    db_host: Optional[str] = None
    db_port: Optional[int] = None
    db_name: Optional[str] = None
    db_user: Optional[str] = None
    db_password: Optional[str] = None
    keys_id_name: Optional[Dict[str, KeyIdNameMapping]] = None

    @field_validator('db_port')
    @classmethod
    def validate_port(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and not (1 <= v <= 65535):
            raise ValueError('Порт должен быть в диапазоне от 1 до 65535')
        return v


class ObjectSettingsUpdate(BaseModel):
    db_host: Optional[str] = None
    db_port: Optional[int] = None
    db_name: Optional[str] = None
    db_user: Optional[str] = None
    db_password: Optional[str] = None
    keys_id_name: Optional[Dict[str, KeyIdNameMapping]] = None

    @field_validator('db_port')
    @classmethod
    def validate_port(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and not (1 <= v <= 65535):
            raise ValueError('Порт должен быть в диапазоне от 1 до 65535')
        return v


class ObjectSettingsPost(BaseModel):
    db_host: str
    db_port: int
    db_name: str
    db_user: str
    db_password: str

    @field_validator('db_port')
    @classmethod
    def validate_port(cls, v: int) -> int:
        if not (1 <= v <= 65535):
            raise ValueError('Порт должен быть в диапазоне от 1 до 65535')
        return v
