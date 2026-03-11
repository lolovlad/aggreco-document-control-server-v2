from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select
from fastapi import Depends


from ..tables import Document, UserToDocument
from ..database import get_session


class DocumentRepository:
    def __init__(self, session: AsyncSession = Depends(get_session)):
        self.__session: AsyncSession = session

    async def count_row(self) -> int:
        response = select(func.count(Document.id))
        result = await self.__session.execute(response)
        return result.scalars().first()

    async def get_limit_user(self, start: int, count: int) -> list[Document]:
        response = select(Document).offset(start).fetch(count).order_by(Document.id)
        result = await self.__session.execute(response)
        return result.unique().scalars().all()

    async def get_by_uuid(self, uuid: str) -> Document:
        response = select(Document).where(Document.uuid == uuid)
        result = await self.__session.execute(response)
        return result.scalars().first()

    async def get_registrate_by_doc_id_and_user_uuid(self, doc_id: int, user_uuid: str):
        response = (
            select(func.count(UserToDocument.id_document))
            .where(UserToDocument.user_uuid == user_uuid)
            .where(UserToDocument.id_document == doc_id)
        )
        result = await self.__session.execute(response)
        return result.scalars().first()

    async def add(self, doc: Document):
        try:
            self.__session.add(doc)
            await self.__session.commit()
        except:
            await self.__session.rollback()
            raise Exception

    async def registrate_user_to_document(self, user_uuid: str, id_document: int):
        entity = UserToDocument(
            id_document=id_document,
            user_uuid=user_uuid,
        )
        try:
            self.__session.add(entity)
            await self.__session.commit()
        except:
            await self.__session.rollback()
            raise Exception

    async def delete(self, document: Document):
        try:
            document.users = []
            await self.__session.delete(document)
            await self.__session.commit()
        except:
            await self.__session.rollback()
            raise Exception

    async def update(self, document: Document):
        try:
            self.__session.add(document)
            await self.__session.commit()
        except Exception:
            await self.__session.rollback()
            raise Exception
