"""Small helpers for building valid, randomized test data with Faker.

Kept separate from conftest.py so both fixtures and individual test modules
can import them directly (e.g. inside a parametrized test) without importing
a conftest module.
"""
from __future__ import annotations

from faker import Faker

from chatroom.auth import hash_password
from chatroom.models import User


def make_username(fake: Faker) -> str:
    """UserRegisterSchema only accepts alphanumeric usernames (3-50 chars).

    Faker's built-in `user_name()` can contain dots/underscores which the API
    rejects, so we build something guaranteed to pass validation instead.
    """
    raw = f"{fake.first_name()}{fake.random_number(digits=6, fix_len=True)}"
    cleaned = "".join(ch for ch in raw if ch.isalnum())
    return cleaned[:50]


def make_password(fake: Faker) -> str:
    """UserRegisterSchema requires a 4-100 character password."""
    return fake.password(length=12)


def build_user(
    db_session,
    fake: Faker,
    *,
    username: str | None = None,
    password: str | None = None,
    age: int | None = None,
) -> tuple[User, str]:
    """Insert a User straight into the database (bypassing the API) and
    return (user, plain_text_password) so a test can log in as that user.
    """
    username = username or make_username(fake)
    password = password or make_password(fake)
    user = User(username=username, hashed_password=hash_password(password), age=age)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user, password
