
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.database import Base, get_db
from app.main import app


TEST_DATABASE_URL = "sqlite://"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(
    bind=test_engine,
    autoflush=False,
    autocommit=False,
)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture
def client():
    Base.metadata.create_all(bind=test_engine)

    with TestClient(app) as test_client:
        yield test_client

    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def registered_user(client):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "sravan",
            "email": "sravan@example.com",
            "password": "SecurePass123",
        },
    )

    assert response.status_code == 201
    return response.json()


def test_health_check(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_user_registration(client):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "kumar",
            "email": "kumar@example.com",
            "password": "SecurePass123",
        },
    )

    assert response.status_code == 201
    assert response.json()["username"] == "kumar"
    assert response.json()["role"] == "CUSTOMER"
    assert "hashed_password" not in response.json()


def test_duplicate_registration(client, registered_user):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "sravan",
            "email": "another@example.com",
            "password": "SecurePass123",
        },
    )

    assert response.status_code == 409


def test_login_success(client, registered_user):
    response = client.post(
        "/api/v1/auth/login",
        json={
            "username": "sravan",
            "password": "SecurePass123",
        },
    )

    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"


def test_login_invalid_password(client, registered_user):
    response = client.post(
        "/api/v1/auth/login",
        json={
            "username": "sravan",
            "password": "WrongPassword123",
        },
    )

    assert response.status_code == 401


def test_get_profile(client, registered_user):
    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "username": "sravan",
            "password": "SecurePass123",
        },
    )

    token = login_response.json()["access_token"]

    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["username"] == "sravan"


def test_profile_without_token(client):
    response = client.get("/api/v1/auth/me")

    assert response.status_code == 401


def test_customer_cannot_register_as_admin(client):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "adminuser",
            "email": "admin@example.com",
            "password": "SecurePass123",
            "role": "ADMIN",
        },
    )

    assert response.status_code == 201
    assert response.json()["role"] == "CUSTOMER"

