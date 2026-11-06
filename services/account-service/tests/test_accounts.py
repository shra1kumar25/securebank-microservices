from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from jose import jwt
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.db.database import Base, get_db
from app.main import app


@pytest.fixture
def client():
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    TestingSessionLocal = sessionmaker(
        bind=test_engine,
        autoflush=False,
        autocommit=False,
    )

    Base.metadata.create_all(bind=test_engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=test_engine)
    test_engine.dispose()


def create_test_token(customer_id: int) -> str:
    payload = {
        "sub": str(customer_id),
        "role": "CUSTOMER",
        "exp": datetime.now(UTC) + timedelta(minutes=5),
    }

    return jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


def auth_headers(customer_id: int) -> dict:
    token = create_test_token(customer_id)
    return {"Authorization": f"Bearer {token}"}


def test_create_account(client):
    response = client.post(
        "/api/v1/accounts",
        json={"account_type": "SAVINGS"},
        headers=auth_headers(101),
    )

    assert response.status_code == 201
    assert response.json()["customer_id"] == 101
    assert response.json()["account_type"] == "SAVINGS"
    assert response.json()["balance"] == "0.00"


def test_list_customer_accounts(client):
    client.post(
        "/api/v1/accounts",
        json={"account_type": "SAVINGS"},
        headers=auth_headers(101),
    )

    response = client.get(
        "/api/v1/accounts",
        headers=auth_headers(101),
    )

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_customer_cannot_access_another_customers_account(client):
    create_response = client.post(
        "/api/v1/accounts",
        json={"account_type": "CURRENT"},
        headers=auth_headers(101),
    )

    account_id = create_response.json()["id"]

    response = client.get(
        f"/api/v1/accounts/{account_id}",
        headers=auth_headers(202),
    )

    assert response.status_code == 404


def test_account_access_requires_authentication(client):
    response = client.get("/api/v1/accounts")

    assert response.status_code == 401
