from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.transactions import router as transactions_router
from app.db.database import Base, engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="SecureBank Transaction Service",
    description="Handles deposits, withdrawals and transfers",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(transactions_router)


@app.get("/")
def root():
    return {"message": "SecureBank Transaction Service is running"}


@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "transaction-service"}
