from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, func
from httpx import AsyncClient

from .api import router
from .settings import settings
from .database import async_session as async_db_session
from .minio import async_session as async_minio_session
from .response import get_client


# origins = [
#     f"http://{settings.cors_host}:{settings.cors_port}",
#     f"http://localhost"
# ]

origins = ["*"]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Проверка доступности основных внешних сервисов при старте приложения:
    - база данных
    - MinIO
    - микросервис пользователей
    """
    print("[CHECKAPP] start")

    # Проверка MinIO
    try:
        buckets = await async_minio_session.list_buckets()
        print(f"[CHECKAPP][MinIO] ok, buckets={[b.name for b in buckets]}")
    except Exception as e:
        print(f"[CHECKAPP][MinIO] ERROR: {e}")

    # Проверка микросервиса пользователей
    try:
        async for client in get_client():
            assert isinstance(client, AsyncClient)
            break
        url = f"{settings.user_service_url.rstrip('/')}/v1/user/get/profile"
        # без авторизации ожидаем 401/403, нам важно что сервис отвечает и не падает
        resp = await client.get(url)
        print(f"[CHECKAPP][USER_SERVICE] status={resp.status_code} url={url}")
    except Exception as e:
        print(f"[CHECKAPP][USER_SERVICE] ERROR: {e}")

    print("[CHECKAPP] done")

    # Здесь можно добавить логику graceful shutdown при необходимости
    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Count-Page", "X-Count-Item"],
)

app.include_router(router)

