from pydantic import BaseModel

from datetime import datetime


class BaseFile(BaseModel):
    file_name: str
    datetime: datetime
    name: str | None
    size: float | None


class GetFile(BaseFile):
    id: int
    file_key: str


class FileGenerate(BaseModel):
    id_blueprint: int
    data_blueprint: dict | None
