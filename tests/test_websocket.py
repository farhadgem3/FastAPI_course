"""Tests for the /ws chat WebSocket endpoint."""
import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from chatroom.auth import create_access_token
from chatroom.models import Message


class TestWebSocketAuth:
    def test_rejects_a_connection_with_no_cookie(self, client):
        # The server calls websocket.close() before accept(), so the client
        # sees the rejection as a failure to establish the connection.
        with pytest.raises(WebSocketDisconnect):
            with client.websocket_connect("/ws"):
                pass

    def test_rejects_a_connection_with_an_invalid_token(self, client):
        client.cookies.set("access_token", "garbage")
        with pytest.raises(WebSocketDisconnect):
            with client.websocket_connect("/ws"):
                pass

    def test_rejects_a_valid_token_for_a_deleted_user(self, client, user_factory, db_session):
        user, _password = user_factory()
        token = create_access_token(user.username)
        db_session.delete(user)
        db_session.commit()

        client.cookies.set("access_token", token)
        with pytest.raises(WebSocketDisconnect):
            with client.websocket_connect("/ws"):
                pass


class TestWebSocketChat:
    def test_authenticated_user_receives_join_message_and_can_chat(self, client, user_factory, fake):
        user, password = user_factory()
        client.post("/login", json={"username": user.username, "password": password})

        with client.websocket_connect("/ws") as websocket:
            join_message = websocket.receive_text()
            assert user.username in join_message
            assert "joined" in join_message

            outgoing = fake.sentence()
            websocket.send_text(outgoing)
            echoed = websocket.receive_text()
            assert outgoing in echoed
            assert user.username in echoed

    def test_sent_message_is_persisted_to_the_database(self, client, user_factory, db_session, fake):
        user, password = user_factory()
        client.post("/login", json={"username": user.username, "password": password})
        outgoing = fake.sentence()

        with client.websocket_connect("/ws") as websocket:
            websocket.receive_text()  # own join broadcast
            websocket.send_text(outgoing)
            websocket.receive_text()  # echoed broadcast

        stored = db_session.query(Message).filter(Message.content == outgoing).first()
        assert stored is not None
        assert stored.user_id == user.id

    def test_history_is_replayed_to_a_newly_connected_client(
        self, client, user_factory, db_session, fake
    ):
        user, password = user_factory()
        db_session.add(Message(content="an older message", user_id=user.id))
        db_session.commit()

        client.post("/login", json={"username": user.username, "password": password})

        with client.websocket_connect("/ws") as websocket:
            # The server sends history, then a join broadcast.
            # Read messages until we find the history one.
            found = False
            while True:
                msg = websocket.receive_text()
                if "an older message" in msg:
                    found = True
                    break
                # if we get the join broadcast, continue – it's okay, history will come after
            assert found

    def test_two_users_see_each_others_messages(self, client, user_factory, fake):
        user_a, _ = user_factory()
        user_b, _ = user_factory()

        token_a = create_access_token(user_a.username)
        token_b = create_access_token(user_b.username)

        # Connect as user_a
        client.cookies.clear()
        client.cookies.set("access_token", token_a)
        with client.websocket_connect("/ws") as ws_a:
            # consume user_a's own join message
            ws_a.receive_text()

            # Connect as user_b (same client, different cookie)
            client.cookies.clear()
            client.cookies.set("access_token", token_b)
            with client.websocket_connect("/ws") as ws_b:
                # consume user_b's own join message
                ws_b.receive_text()

                # user_a should see user_b's join broadcast
                join_seen_by_a = ws_a.receive_text()
                assert user_b.username in join_seen_by_a

                # Send a message from user_b, user_a must receive it
                msg = fake.sentence()
                ws_b.send_text(msg)
                received_by_a = ws_a.receive_text()
                assert msg in received_by_a