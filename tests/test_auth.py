"""Unit tests for chatroom/auth.py: password hashing + JWT tokens.

These are pure unit tests -- no database, no HTTP client, no fixtures other
than `fake` from conftest.py.
"""
import time

from jose import jwt

from chatroom import auth
from chatroom.auth import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
    decode_refresh_token,
    hash_password,
    verify_password,
)


class TestPasswordHashing:
    def test_hash_password_returns_a_bcrypt_hash(self, fake):
        plain = fake.password(length=12)
        hashed = hash_password(plain)
        assert hashed != plain
        assert hashed.startswith(("$2a$", "$2b$", "$2y$"))

    def test_hash_password_is_salted_differently_each_time(self, fake):
        plain = fake.password(length=12)
        assert hash_password(plain) != hash_password(plain)

    def test_verify_password_accepts_the_correct_password(self, fake):
        plain = fake.password(length=12)
        hashed = hash_password(plain)
        assert verify_password(plain, hashed) is True

    def test_verify_password_rejects_the_wrong_password(self, fake):
        plain = fake.password(length=12)
        hashed = hash_password(plain)
        assert verify_password(plain + "x", hashed) is False

    def test_verify_password_random_roundtrip(self, fake):
        # Run it a handful of times with different randomly generated
        # passwords to catch any edge cases around length/characters.
        for _ in range(10):
            plain = fake.password(length=fake.random_int(min=4, max=64))
            hashed = hash_password(plain)
            assert verify_password(plain, hashed) is True


class TestAccessToken:
    def test_has_the_expected_claims(self, fake):
        username = fake.user_name()
        token = create_access_token(username)
        payload = jwt.decode(token, auth.SECRET_KEY, algorithms=[auth.ALGORITHM])
        assert payload["sub"] == username
        assert payload["type"] == "access"
        assert "exp" in payload

    def test_decode_returns_the_username_for_a_valid_token(self, fake):
        username = fake.user_name()
        token = create_access_token(username)
        assert decode_access_token(token) == username

    def test_decode_returns_none_for_garbage_input(self):
        assert decode_access_token("this-is-not-a-jwt") is None

    def test_decode_rejects_a_refresh_token(self, fake):
        # A refresh token must never be usable as an access token.
        refresh_token = create_refresh_token(fake.user_name())
        assert decode_access_token(refresh_token) is None

    def test_decode_rejects_an_expired_token(self, fake):
        expired_payload = {
            "type": "access",
            "sub": fake.user_name(),
            "exp": int(time.time()) - 60,
        }
        expired_token = jwt.encode(expired_payload, auth.SECRET_KEY, algorithm=auth.ALGORITHM)
        assert decode_access_token(expired_token) is None

    def test_decode_rejects_a_token_signed_with_a_different_secret(self, fake):
        forged_token = jwt.encode(
            {"type": "access", "sub": fake.user_name(), "exp": int(time.time()) + 60},
            "a-totally-different-secret",
            algorithm=auth.ALGORITHM,
        )
        assert decode_access_token(forged_token) is None


class TestRefreshToken:
    def test_has_the_expected_claims(self, fake):
        username = fake.user_name()
        token = create_refresh_token(username)
        payload = jwt.decode(token, auth.SECRET_KEY, algorithms=[auth.ALGORITHM])
        assert payload["sub"] == username
        assert payload["type"] == "refresh"

    def test_decode_returns_the_username_for_a_valid_token(self, fake):
        username = fake.user_name()
        token = create_refresh_token(username)
        assert decode_refresh_token(token) == username

    def test_decode_rejects_an_access_token(self, fake):
        access_token = create_access_token(fake.user_name())
        assert decode_refresh_token(access_token) is None

    def test_decode_rejects_an_expired_token(self, fake):
        expired_payload = {
            "type": "refresh",
            "sub": fake.user_name(),
            "exp": int(time.time()) - 60,
        }
        expired_token = jwt.encode(expired_payload, auth.SECRET_KEY, algorithm=auth.ALGORITHM)
        assert decode_refresh_token(expired_token) is None

    def test_decode_returns_none_for_garbage_input(self):
        assert decode_refresh_token("this-is-not-a-jwt") is None
