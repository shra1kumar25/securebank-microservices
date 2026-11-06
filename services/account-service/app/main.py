from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.accounts import router as accounts_router
from app.db.database import Base, engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="SecureBank Account Service",
    description="Account management microservice",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(accounts_router)


@app.get("/", tags=["Root"])
def root():
    return {"message": "SecureBank Account Service is running"}


@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "service": "account-service",
    }
