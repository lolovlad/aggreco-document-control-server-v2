from pydantic import BaseModel


class GetAllStatistic(BaseModel):
    obj: list[dict] = []