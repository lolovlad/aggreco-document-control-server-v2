from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from fastapi import Depends

from ..tables import FileDocument
from ..database import get_session


class FileRepository:
    def __init__(self, session: AsyncSession = Depends(get_session)):
        self.__session: AsyncSession = session

    async def add(self, entity: FileDocument):
        try:
            self.__session.add(entity)
            await self.__session.commit()
        except:
            await self.__session.rollback()
            raise Exception

    async def get(self, id_file: int) -> FileDocument | None:
        file_document = await self.__session.get(FileDocument, id_file)
        return file_document

    async def get_all(self) -> list[FileDocument]:
        response = select(FileDocument)
        result = await self.__session.execute(response)
        return result.scalars().all()
