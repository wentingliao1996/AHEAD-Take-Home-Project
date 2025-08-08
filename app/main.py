from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.routes import router

app = FastAPI(
    title="AHEAD Take Home Project",
    version="1.0.0"
)

app.include_router(router)