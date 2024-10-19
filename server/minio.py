from miniopy_async import Minio
from .settings import settings


async_session = Minio(endpoint=f"{settings.minio_host}:{settings.minio_port}",
                      access_key=settings.minio_access_key,
                      secret_key=settings.minio_secret_key,
                      secure=False)



