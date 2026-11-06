from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.notifications import router as notifications_router
from app.core.config import settings
from app.db.database import Base, engine
from app.services.consumer import start_consumer


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    start_consumer()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

app.include_router(notifications_router)


@app.get("/")
def root():
    return {
        "service": "notification-service",
        "status": "running",
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "notification-service",
    }
