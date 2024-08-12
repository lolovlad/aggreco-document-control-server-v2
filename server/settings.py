from pydantic_settings import BaseSettings


class Settings(BaseSettings):

    postgres_host: str
    postgres_port: int
    postgres_user: str
    postgres_db: str
    postgres_password: str
    pgport: int

    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_expiration: int = 3600 * 12

    host_server: str
    port_server: int

    cors_host: str
    cors_port: int

    client_id: str
    client_secret: str


settings = Settings(_env_file='./.env', _env_file_encoding='utf-8')