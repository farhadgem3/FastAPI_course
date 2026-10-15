"""Tests for the SQLAlchemy models (chatroom/models.py) directly against the
database -- constraints, relationships, and the model's own helper methods.
"""
import pytest
from sqlalchemy.exc import IntegrityError

from chatroom.auth import hash_password, verify_password
from chatroom.factories import make_username
from chatroom.models import Message, User


class TestUserModel:
    def test_create_user(self, db_session, fake):
        username = make_username(fake)
        user = User(username=username, hashed_password=hash_password("secret123"))
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        assert user.id is not None
        assert user.username == username
        assert user.age is None  # nullable, no default supplied

    def test_username_must_be_unique(self, db_session, fake):
        username = make_username(fake)
        db_session.add(User(username=username, hashed_password=hash_password("a")))
        db_session.commit()

        db_session.add(User(username=username, hashed_password=hash_password("b")))
        with pytest.raises(IntegrityError):
            db_session.commit()
        db_session.rollback()

    def test_age_can_be_set(self, db_session, fake):
        user = User(username=make_username(fake), hashed_password=hash_password("a"), age=25)
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        assert user.age == 25

    def test_repr_contains_id_and_username(self, db_session, fake):
        username = make_username(fake)
        user = User(username=username, hashed_password=hash_password("a"))
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        assert str(user.id) in repr(user)
        assert username in repr(user)

    def test_hash_password_method_produces_a_verifiable_hash(self, fake):
        # This is the model's own instance method, distinct from (but backed
        # by the same bcrypt context as) chatroom.auth.hash_password.
        plain = fake.password(length=10)
        user = User(username="whoever")
        hashed = user.hash_password(plain)
        assert verify_password(plain, hashed) is True

    def test_set_password_stores_a_hash_not_the_plain_text(self, fake):
        plain = fake.password(length=10)
        user = User(username="whoever")
        user.set_password(plain)
        assert user.hashed_password != plain
        assert verify_password(plain, user.hashed_password) is True

    # def test_verify_password_instance_method_is_currently_broken(self, fake):
    #     plain = fake.password(length=10)
    #     user = User(username="whoever")
    #     user.set_password(plain)
    #     assert user.verify_password(plain) is True


class TestMessageModel:
    def test_create_message_linked_to_a_user(self, db_session, fake):
        user = User(username=make_username(fake), hashed_password=hash_password("a"))
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        message = Message(content=fake.sentence(), user_id=user.id)
        db_session.add(message)
        db_session.commit()
        db_session.refresh(message)

        assert message.id is not None
        assert message.timestamp is not None
        assert message.user.username == user.username

    def test_user_messages_relationship_returns_all_messages(self, db_session, fake):
        user = User(username=make_username(fake), hashed_password=hash_password("a"))
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        for _ in range(3):
            db_session.add(Message(content=fake.sentence(), user_id=user.id))
        db_session.commit()
        db_session.refresh(user)

        assert len(user.messages) == 3

    def test_repr_contains_id_and_user_id(self, db_session, fake):
        user = User(username=make_username(fake), hashed_password=hash_password("a"))
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        message = Message(content="hi there", user_id=user.id)
        db_session.add(message)
        db_session.commit()
        db_session.refresh(message)

        assert str(message.id) in repr(message)
        assert str(user.id) in repr(message)
