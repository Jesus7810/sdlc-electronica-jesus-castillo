from fastapi import FastAPI

from app.routers import router

app = FastAPI(
    title="SensorHub API",
    version="0.2.0",
)
app.include_router(router)