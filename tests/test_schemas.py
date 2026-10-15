"""Tests for the Pydantic schemas in chatroom/schemas.py, in isolation from
the database and HTTP layer.
"""
import pytest
from pydantic import ValidationError

from chatroom.models import User
from chatroom.schemas import (
    UserLoginSchema,
    UserRegisterSchema,
    UserResponseSchema,
    UserUpdateSchema,
)


class TestUserRegisterSchema:
    def test_accepts_a_valid_payload(self):
        schema = UserRegisterSchema(username="abc123", password="secret")
        assert schema.username == "abc123"
        assert schema.password == "secret"

    def test_username_is_title_cased_when_the_schema_itself_is_serialized(self):
        # NOTE: this @field_serializer lives on UserRegisterSchema (the input
        # schema). The API routes return UserResponseSchema instead, which has
        # no such serializer, so registration/login responses are NOT
        # title-cased -- see test_routes_auth.py. This test only covers
        # UserRegisterSchema's own behavior when dumped directly.
        schema = UserRegisterSchema(username="johndoe1", password="secret")
        assert schema.model_dump()["username"] == "Johndoe1"

    @pytest.mark.parametrize("bad_username", ["ab", "a" * 51])
    def test_username_length_is_enforced(self, bad_username):
        with pytest.raises(ValidationError):
            UserRegisterSchema(username=bad_username, password="secret")

    @pytest.mark.parametrize("bad_password", ["abc", "a" * 101])
    def test_password_length_is_enforced(self, bad_password):
        with pytest.raises(ValidationError):
            UserRegisterSchema(username="abc123", password=bad_password)

    @pytest.mark.parametrize(
        "bad_username", ["john doe", "john-doe", "john_doe", "john.doe", "john!doe"]
    )
    def test_username_must_be_alphanumeric(self, bad_username):
        with pytest.raises(ValidationError):
            UserRegisterSchema(username=bad_username, password="secret")

    def test_random_faker_generated_usernames_that_are_alphanumeric_are_accepted(self, fake):
        for _ in range(20):
            raw = f"{fake.first_name()}{fake.random_number(digits=4, fix_len=True)}"
            username = "".join(ch for ch in raw if ch.isalnum())[:50]
            if len(username) < 3:
                continue
            schema = UserRegisterSchema(username=username, password=fake.password(length=8))
            assert schema.username.isalnum()


class TestUserLoginSchema:
    def test_accepts_any_non_empty_strings(self, fake):
        schema = UserLoginSchema(username=fake.user_name(), password=fake.password())
        assert schema.username
        assert schema.password

    def test_username_is_required(self):
        with pytest.raises(ValidationError):
            UserLoginSchema(password="secret")

    def test_password_is_required(self):
        with pytest.raises(ValidationError):
            UserLoginSchema(username="someone")


class TestUserUpdateSchema:
    def test_all_fields_are_optional_and_default_to_none(self):
        schema = UserUpdateSchema()
        assert schema.username is None
        assert schema.password is None
        assert schema.age is None

    def test_a_single_field_can_be_updated_at_a_time(self):
        schema = UserUpdateSchema(age=30)
        assert schema.age == 30
        assert schema.username is None
        assert schema.password is None

    @pytest.mark.parametrize("bad_age", [0, -5, 100, 999])
    def test_age_must_be_strictly_between_0_and_100(self, bad_age):
        with pytest.raises(ValidationError):
            UserUpdateSchema(age=bad_age)

    @pytest.mark.parametrize("good_age", [1, 30, 99])
    def test_valid_ages_are_accepted(self, good_age):
        schema = UserUpdateSchema(age=good_age)
        assert schema.age == good_age

    @pytest.mark.parametrize("bad_username", ["ab", "a" * 51])
    def test_username_length_is_enforced_when_provided(self, bad_username):
        with pytest.raises(ValidationError):
            UserUpdateSchema(username=bad_username)

    @pytest.mark.parametrize("bad_password", ["abc", "a" * 101])
    def test_password_length_is_enforced_when_provided(self, bad_password):
        with pytest.raises(ValidationError):
            UserUpdateSchema(password=bad_password)


class TestUserResponseSchema:
    def test_builds_from_an_orm_object(self, fake):
        user = User(username=fake.user_name())
        user.id = 42
        schema = UserResponseSchema.model_validate(user)
        assert schema.id == 42
        assert schema.username == user.username

    def test_extra_orm_attributes_are_ignored(self, fake):
        user = User(username=fake.user_name(), hashed_password="secret-hash", age=25)
        user.id = 1
        schema = UserResponseSchema.model_validate(user)
        dumped = schema.model_dump()
        assert "hashed_password" not in dumped
        assert "age" not in dumped
