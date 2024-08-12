from fastapi import APIRouter
from .login import router as login_router
from .document import router as document_router
from .user import router as user_router
from .object import router as object_router
from .accident import router as accident_router


router = APIRouter(prefix="/v1")
router.include_router(login_router)
router.include_router(document_router)
router.include_router(user_router)
router.include_router(object_router)
router.include_router(accident_router)


