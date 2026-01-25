from fastapi import FastAPI

from app.api import router
from app.services.logging import setup_logging

setup_logging()

app = FastAPI(title="short-video-factory")
app.include_router(router)
