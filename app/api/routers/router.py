from app.api.routers.auth import router as auth_router
from app.api.routers.file import router as file_router
from app.api.routers.stats import router as stats_router
from fastapi import APIRouter

router = APIRouter()

router.include_router(auth_router)