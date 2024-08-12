import datetime

from pydantic import BaseModel, UUID4, field_serializer
from .User import UserGet


class BaseDocument(BaseModel):
    name: str
    description: str = ""
    url_document: str


class DocumentPost(BaseDocument):
    pass


class DocumentUpdate(BaseDocument):
    uuid: UUID4


class DocumentGetView(BaseDocument):
    uuid: UUID4
    data_create: datetime.datetime

    @field_serializer("uuid")
    def serialize_uuid(self, uuid: UUID4, _info):
        return str(uuid)


class DocumentGet(DocumentPost):
    id: int
    users: list[UserGet]
