from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, func

from .api import router
from .settings import settings

from .repositories import UserRepository
from .database import async_session
from .tables import User, TypeUser


#origins = [
#    f"http://{settings.cors_host}:{settings.cors_port}",
#    f"http://localhost"
#]

origins = ["*"]

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Count-Page", "X-Count-Item"],
)

app.include_router(router)

