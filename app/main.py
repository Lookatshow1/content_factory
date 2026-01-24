from fastapi import FastAPI

from app.api import router

app = FastAPI(title="short-video-factory")
app.include_router(router)
