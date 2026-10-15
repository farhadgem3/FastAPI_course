"""Shared pytest fixtures for the chatroom test suite.

Every single test gets its own brand-new in-memory SQLite database (tables
are created before the test and dropped after), so tests never leak state
into one another and can run in any order.
"""
from typing import Generator

import pytest
from faker import Faker
from fastapi.testclient import TestClient
from sqlalchemy import StaticPool, create_engine
from sqlalchemy.orm import Session, sessionmaker
from unittest.mock import patch
import fakeredis

from main import app
from config.database import Base, get_db
from chatroom.factories import build_user, make_password, make_username

TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture()
def fake() -> Faker:
    """A fresh Faker instance for every test."""
    return Faker()


@pytest.fixture()
def db_session() -> Generator[Session, None, None]:
    """A clean set of tables plus a session, torn down after each test."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """A TestClient wired to the isolated `db_session`.

    Uses the client as a context manager so the app's `lifespan` actually
    runs (it loads the i18n .mo translation files into memory -- without
    this the Persian-language tests would silently fall back to English).
    """

    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture()
def user_factory(db_session: Session, fake: Faker):
    """user_factory(**kwargs) -> (User, plain_password), inserted directly
    into the database (bypassing the API/registration flow entirely)."""

    def _factory(**kwargs):
        return build_user(db_session, fake, **kwargs)

    return _factory


@pytest.fixture()
def registered_user(client: TestClient, fake: Faker):
    """A user created *through the API* (POST /register).

    Returns (response_json, plain_password).
    """
    username = make_username(fake)
    password = make_password(fake)
    response = client.post("/register", json={"username": username, "password": password})
    assert response.status_code == 201, response.text
    return response.json(), password


@pytest.fixture()
def auth_client(client: TestClient, user_factory):
    """A TestClient that is already logged in as a freshly created user.

    Returns (client, user, plain_password).
    """
    user, password = user_factory()
    response = client.post("/login", json={"username": user.username, "password": password})
    assert response.status_code == 200, response.text
    return client, user, password

@pytest.fixture(autouse=True)
def mock_redis():
    """Automatically replace real Redis with a fake, in‑memory Redis for every test."""
    with patch("chatroom.routes.redis_client", fakeredis.FakeStrictRedis()) as mock:
        yield mock