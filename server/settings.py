from pydantic_settings import BaseSettings

import os

class Settings(BaseSettings):

    postgres_host: str
    postgres_port: int
    postgres_user: str
    postgres_db: str
    postgres_password: str
    pgport: int

    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_expiration_access: int = 60 * 15
    jwt_expiration_refresh: int = 60 * 60 * 24 * 30

    host_server: str
    port_server: int

    cors_host: str
    cors_port: int

    client_id: str
    client_secret: str

    minio_root_user: str
    minio_root_password: str
    minio_default_buckets: str
    minio_host: str
    minio_port: int

    minio_access_key: str
    minio_secret_key: str

    root_path: str = os.path.dirname(os.path.abspath(__file__))


settings = Settings(_env_file='./.env', _env_file_encoding='utf-8')