from fastapi import APIRouter
from .login import router as login_router
from .document import router as document_router
from .user import router as user_router
from .object import router as object_router
from .accident import router as accident_router
from .statistic import router as statistic_router
from .claim import router as claim_router
from .file import router as file_router
from .env import router as env_router
from .proposals import router as proposals_router
from .log_analysis import router as log_analysis_router


router = APIRouter(prefix="/v1")
router.include_router(login_router)
router.include_router(document_router)
router.include_router(user_router)
router.include_router(object_router)
router.include_router(accident_router)
router.include_router(statistic_router)
router.include_router(claim_router)
router.include_router(file_router)
router.include_router(env_router)
router.include_router(proposals_router)
router.include_router(log_analysis_router)



