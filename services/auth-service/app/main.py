from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.auth import router as auth_router
from app.db.database import Base, engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="SecureBank Auth Service",
    description="Authentication and authorization microservice",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(auth_router)


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "healthy", "service": "auth-service"}


@app.get("/", tags=["Root"])
def root():
    return {"message": "SecureBank Auth Service is running"}
