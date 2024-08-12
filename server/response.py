from httpx import AsyncClient


async def get_client() -> AsyncClient:
    async with AsyncClient() as client:
        try:
            yield client
        except Exception:
            pass