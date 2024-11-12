from fastapi import Depends
from ..minio import async_session, session
from miniopy_async import Minio
from miniopy_async.helpers import ObjectWriteResult
from miniopy_async.deleteobjects import DeleteObject
from ..settings import settings
from pathlib import Path
from io import BytesIO
import aiohttp


class FileBucketRepository:
    def __init__(self, name: str):
        self.__client: Minio = async_session
        self.__client_download = session
        self.__name_bucket: str = name

    async def create_bucket(self):
        is_bucket_exist = await self.__client.bucket_exists(self.__name_bucket)
        if is_bucket_exist is False:
            await self.__client.make_bucket(self.__name_bucket)

    async def upload_file(self,
                          file_key: str,
                          file: str | bytes,
                          content_type: str) -> ObjectWriteResult:

        if isinstance(file, bytes):
            buffer = BytesIO(file)
        else:
            buffer = BytesIO(file.encode("utf-8"))

        result = await self.__client.put_object(self.__name_bucket,
                                                file_key,
                                                buffer,
                                                -1,
                                                part_size=10 * 1024 * 1024,
                                                content_type=content_type)
        return result

    async def delete_file(self,
                          file_key: str):
        try:
            await self.__client.remove_object(self.__name_bucket, file_key)
        except Exception:
            pass

    async def get_list_file(self,
                            prefix: str) -> list[str] | None:
        try:
            new_list_file = []
            list_files = await self.__client.list_objects(self.__name_bucket, prefix)
            for file in list_files:
                file_name = file.object_name.split("/")[-1]
                new_list_file.append(file_name)
            return new_list_file
        except Exception:
            return None

    async def delete_object(self, file_key: str):
        try:
            await self.__client.remove_object(self.__name_bucket, file_key)
        except Exception:
            pass

    async def get_file(self, file_key: str) -> bytes:
        async with aiohttp.ClientSession() as session:
            file = await self.__client.get_object(self.__name_bucket, file_key, session)
            content = await file.read()
            return content

    async def get_sate(self, file_key: str):
        info = await self.__client.stat_object(self.__name_bucket, file_key)
        return info

    def get_file_stream(self, file_key: str, size: int):
        offset = 0
        while True:
            response = self.__client_download.get_object(self.__name_bucket, file_key, offset=offset, length=2048)
            yield response.read()
            offset = offset + 2048
            if offset >= size:
                break