"""End-to-end tests for the public auth endpoints: /register, /login,
/refresh, /logout. This file replaces the old chatroom/test_api.py -- delete
that file once these are in place.
"""
from chatroom.factories import make_password, make_username


class TestRegister:
    def test_register_returns_201_and_the_new_user(self, client, fake):
        username = make_username(fake)
        password = make_password(fake)

        response = client.post("/register", json={"username": username, "password": password})

        assert response.status_code == 201
        body = response.json()
        assert body["username"] == username  # UserResponseSchema has no serializer
        assert "id" in body
        assert "password" not in body
        assert "hashed_password" not in body

    def test_duplicate_username_is_rejected(self, client, fake):
        username = make_username(fake)
        first = client.post("/register", json={"username": username, "password": make_password(fake)})
        assert first.status_code == 201

        second = client.post("/register", json={"username": username, "password": make_password(fake)})
        assert second.status_code == 400
        assert "already taken" in second.json()["detail"].lower()

    def test_rejects_non_alphanumeric_username(self, client, fake):
        response = client.post(
            "/register", json={"username": "bad name!", "password": make_password(fake)}
        )
        assert response.status_code == 422

    def test_rejects_username_shorter_than_3_chars(self, client, fake):
        response = client.post("/register", json={"username": "ab", "password": make_password(fake)})
        assert response.status_code == 422

    def test_rejects_password_shorter_than_4_chars(self, client, fake):
        response = client.post("/register", json={"username": make_username(fake), "password": "abc"})
        assert response.status_code == 422

    def test_duplicate_username_error_is_localized_to_persian(self, client, fake):
        username = make_username(fake)
        client.post("/register", json={"username": username, "password": make_password(fake)})

        response = client.post(
            "/register?lang=fa", json={"username": username, "password": make_password(fake)}
        )
        assert response.status_code == 400
        assert response.json()["detail"] == "این نام کاربری قبلاً استفاده شده است"
        assert response.headers["content-language"] == "fa"


class TestLogin:
    def test_login_succeeds_and_sets_both_cookies(self, client, user_factory):
        user, password = user_factory()
        response = client.post("/login", json={"username": user.username, "password": password})

        assert response.status_code == 200
        assert response.json() == {"message": f"welcome {user.username}"}
        assert "access_token" in response.cookies
        assert "refresh_token" in response.cookies

    def test_wrong_password_is_rejected(self, client, user_factory):
        user, _password = user_factory()
        response = client.post("/login", json={"username": user.username, "password": "wrong-one"})
        assert response.status_code == 401

    def test_unknown_username_is_rejected(self, client, fake):
        response = client.post("/login", json={"username": make_username(fake), "password": "whatever"})
        assert response.status_code == 401

    def test_error_message_does_not_reveal_whether_username_or_password_was_wrong(
        self, client, user_factory
    ):
        user, _password = user_factory()
        wrong_password = client.post(
            "/login", json={"username": user.username, "password": "nope"}
        ).json()
        unknown_user = client.post(
            "/login", json={"username": "totally-unknown-user", "password": "nope"}
        ).json()
        assert wrong_password["detail"] == unknown_user["detail"]


class TestRefresh:
    def test_missing_refresh_cookie_is_rejected(self, client):
        response = client.post("/refresh")
        assert response.status_code == 401

    def test_tampered_refresh_cookie_is_rejected(self, client):
        client.cookies.clear()
        client.cookies.set("refresh_token", "not-a-real-token")
        response = client.post("/refresh")
        assert response.status_code == 401

    def test_an_access_token_cannot_be_used_as_a_refresh_token(self, client, user_factory):
        user, password = user_factory()
        login_response = client.post("/login", json={"username": user.username, "password": password})
        access_token = login_response.cookies["access_token"]

        client.cookies.clear()
        client.cookies.set("refresh_token", access_token)
        response = client.post("/refresh")
        assert response.status_code == 401

    def test_valid_refresh_cookie_issues_a_new_access_token(self, client, user_factory):
        user, password = user_factory()
        client.post("/login", json={"username": user.username, "password": password})

        response = client.post("/refresh")
        assert response.status_code == 200
        assert "access_token" in response.cookies


class TestLogout:
    def test_logout_clears_the_access_token_so_protected_routes_401(self, client, user_factory):
        user, password = user_factory()
        client.post("/login", json={"username": user.username, "password": password})

        response = client.post("/logout")
        assert response.status_code == 200

        me_response = client.get("/me")
        assert me_response.status_code == 401
