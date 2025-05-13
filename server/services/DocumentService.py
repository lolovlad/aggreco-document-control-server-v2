from fastapi import Depends

from httpx import AsyncClient

from ..repositories import DocumentRepository, UserRepository
from ..models.Document import DocumentPost, DocumentGetView, DocumentUpdate
from ..models.YandexToken import YandexToken, YandexUser
from ..models.User import UserDocument
from ..tables import Document
from ..response import get_client
from ..settings import settings


class DocumentService:
    def __init__(self,
                 doc_repo: DocumentRepository = Depends(),
                 user_repo: UserRepository = Depends(),
                 client: AsyncClient = Depends(get_client)):
        self.__doc_repo: DocumentRepository = doc_repo
        self.__user_repo: UserRepository = user_repo
        self.__client: AsyncClient = client
        self.__count_item: int = 20

    @property
    def count_item(self) -> int:
        return self.__count_item

    @count_item.setter
    def count_item(self, item):
        self.__count_item = item

    async def get_url_document(self, uuid: str):
        url_document = f"http://{settings.host_server}:{settings.port_server}/v1/document/view_document/{uuid}"
        return url_document

    async def get_count_page(self) -> int:
        count_row = await self.__doc_repo.count_row()
        sub_page = 0
        if count_row % self.__count_item > 0:
            sub_page += 1
        return count_row // self.__count_item + sub_page

    async def get_document_page(self, num_page: int) -> list[DocumentGetView]:
        start = (num_page - 1) * self.__count_item
        document_entity = await self.__doc_repo.get_limit_user(start, self.__count_item)
        documents = [DocumentGetView.model_validate(entity, from_attributes=True) for entity in document_entity]
        return documents

    async def add(self, document: DocumentPost):
        document = Document(
            name=document.name,
            description=document.description,
            url_document=document.url_document
        )
        await self.__doc_repo.add(document)

    async def get_token_user_from_yandex(self, code: str) -> YandexToken | None:
        result = await self.__client.post("https://oauth.yandex.ru/token", data={
            "grant_type": "authorization_code",
            "code": code,
            "client_id": settings.client_id,
            "client_secret": settings.client_secret
        })

        if result.status_code < 400:
            token = YandexToken.model_validate_json(result.text)
            return token
        else:
            return None

    async def get_user_from_yandex(self, token: YandexToken) -> YandexUser:
        header = {
            "Authorization": f"OAuth {token.access_token}"
        }
        result = await self.__client.post("https://login.yandex.ru/info", headers=header)
        return YandexUser.model_validate_json(result.text)

    async def registrate_user_to_document(self, user_email: str, document_id: int) -> bool:
        user = await self.__user_repo.get_user_by_email(user_email)
        count = await self.__doc_repo.get_registrate_by_doc_id_and_user_id(document_id, user.id)
        if count == 0:
            await self.__doc_repo.registrate_user_to_document(user.id, document_id)
            return True
        return False

    async def redirect_file(self, user: YandexUser, uuid_document: str) -> Document:
        document = await self.__doc_repo.get_by_uuid(uuid_document)

        is_registrate = await self.registrate_user_to_document(user.default_email, document.id)
        if is_registrate:
            return document
        else:
            raise Exception

    async def delete_document(self, uuid: str):
        try:
            entity = await self.__doc_repo.get_by_uuid(uuid)
            await self.__doc_repo.delete(entity)
        except Exception:
            raise Exception

    async def get_document_by_uuid(self, uuid: str) -> DocumentGetView | None:
        document = await self.__doc_repo.get_by_uuid(uuid)
        return DocumentGetView.model_validate(document, from_attributes=True)

    async def update_document(self, document: DocumentUpdate):
        entity = await self.__doc_repo.get_by_uuid(document.uuid)
        entity.name = document.name
        entity.url_document = document.url_document
        entity.description = document.description
        try:
            await self.__doc_repo.update(entity)
        except Exception:
            raise Exception

    async def get_users_to_document(self, uuid: str) -> list[UserDocument]:
        doc = await self.__doc_repo.get_by_uuid(uuid)
        return [UserDocument.model_validate(entity, from_attributes=True) for entity in doc.users_document]
