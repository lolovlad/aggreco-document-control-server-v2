from pydantic import BaseModel, UUID4, field_serializer
from datetime import datetime


class Profession(BaseModel):
    id: int | None = None
    name: str
    description: str | None = ""


class TypeUser(BaseModel):
    name: str
    description: str | None = ""


class GetTypeUser(TypeUser):
    id: int


class UserBase(BaseModel):
    email: str | None
    id_type: int
    name: str | None
    surname: str | None
    patronymic: str | None
    id_profession: int | None


class UserGet(UserBase):
    uuid: UUID4
    type: GetTypeUser
    profession: Profession | None

    @field_serializer('uuid')
    def serialize_uuid(self, uuid: UUID4, _info):
        return str(uuid)


class UserPost(UserBase):
    password: str


class UserUpdate(UserBase):
    password: str | None = None


class UserDocument(BaseModel):
    user: UserGet
    datetime_view: datetime
