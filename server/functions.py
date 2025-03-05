from functools import wraps
from fastapi import HTTPException, Depends
from typing import List, Callable, Any
from starlette import status
from .services import get_current_user


def access_control(allowed_roles: List[str]):
    def decorator(func: Callable[..., Any]):
        @wraps(func)
        async def wrapper(*args, current_user=Depends(get_current_user), **kwargs):
            if current_user.type.name not in allowed_roles:
                raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail="Access Denied")
            return await func(*args, current_user=current_user, **kwargs)
        return wrapper
    return decorator