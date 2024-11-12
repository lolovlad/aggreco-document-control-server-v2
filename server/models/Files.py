from pydantic import BaseModel

from datetime import datetime


class BaseFile(BaseModel):
    file_name: str
    datetime: datetime


class GetFile(BaseFile):
    id: int
    file_key: str