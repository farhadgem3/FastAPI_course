"""End-to-end tests for the protected /me, /users, and /user/{id} endpoints."""
# from chatroom.factories import make_username


# class TestListUsers:
#     def test_requires_authentication(self, client):
#         assert client.get("/users").status_code == 401

#     def test_default_limit_is_one(self, auth_client, user_factory):
#         client, _user, _password = auth_client
#         for _ in range(3):
#             user_factory()

#         response = client.get("/users")
#         assert response.status_code == 200
#         assert len(response.json()) == 1

#     def test_pagination_returns_distinct_pages(self, auth_client, user_factory):
#         client, _user, _password = auth_client
#         for _ in range(5):
#             user_factory()

#         page_1 = client.get("/users", params={"limit": 2, "page": 1}).json()
#         page_2 = client.get("/users", params={"limit": 2, "page": 2}).json()

#         assert len(page_1) == 2
#         assert len(page_2) == 2
#         assert {u["id"] for u in page_1}.isdisjoint({u["id"] for u in page_2})

#     def test_limit_must_be_greater_than_zero(self, auth_client):
#         client, _user, _password = auth_client
#         assert client.get("/users", params={"limit": 0}).status_code == 422

#     def test_page_must_be_greater_than_zero(self, auth_client):
#         client, _user, _password = auth_client
#         assert client.get("/users", params={"page": 0}).status_code == 422


# class TestGetSingleUser:
#     def test_requires_authentication(self, client, user_factory):
#         target, _password = user_factory()
#         assert client.get(f"/user/{target.id}").status_code == 401

#     def test_returns_the_requested_user(self, auth_client, user_factory):
#         client, _user, _password = auth_client
#         target, _target_password = user_factory()

#         response = client.get(f"/user/{target.id}")
#         assert response.status_code == 200
#         assert response.json()["id"] == target.id

#     def test_unknown_id_returns_404(self, auth_client):
#         client, _user, _password = auth_client
#         assert client.get("/user/999999").status_code == 404

#     def test_non_positive_id_is_rejected(self, auth_client):
#         client, _user, _password = auth_client
#         assert client.get("/user/0").status_code == 422


# class TestUpdateUser:
#     def test_requires_authentication(self, client, user_factory):
#         target, _password = user_factory()
#         assert client.put(f"/user/{target.id}", json={"age": 25}).status_code == 401

#     def test_user_can_update_their_own_profile(self, auth_client, fake):
#         client, user, _password = auth_client
#         new_username = make_username(fake)

#         response = client.put(f"/user/{user.id}", json={"username": new_username, "age": 40})
#         assert response.status_code == 200
#         assert response.json()["username"] == new_username

#     def test_partial_update_only_touches_the_given_fields(self, auth_client, db_session):
#         client, user, _password = auth_client
#         original_username = user.username

#         response = client.put(f"/user/{user.id}", json={"age": 27})
#         assert response.status_code == 200
#         assert response.json()["username"] == original_username

#         db_session.refresh(user)
#         assert user.age == 27

#     def test_user_cannot_update_someone_elses_profile(self, auth_client, user_factory):
#         client, _user, _password = auth_client
#         other, _other_password = user_factory()

#         response = client.put(f"/user/{other.id}", json={"age": 22})
#         assert response.status_code == 403

#     def test_updating_to_a_taken_username_is_rejected(self, auth_client, user_factory):
#         client, user, _password = auth_client
#         other, _other_password = user_factory()

#         response = client.put(f"/user/{user.id}", json={"username": other.username})
#         assert response.status_code == 400

#     def test_unknown_id_returns_404(self, auth_client):
#         client, _user, _password = auth_client
#         assert client.put("/user/999999", json={"age": 22}).status_code == 404


# class TestDeleteUser:
#     def test_requires_authentication(self, client, user_factory):
#         target, _password = user_factory()
#         assert client.delete(f"/user/{target.id}").status_code == 401

#     def test_user_can_delete_their_own_account(self, auth_client, db_session):
#         client, user, _password = auth_client
#         user_id, user_type = user.id, type(user)

#         response = client.delete(f"/user/{user.id}")
#         assert response.status_code == 200
#         assert db_session.get(user_type, user_id) is None

#     def test_user_cannot_delete_someone_elses_account(self, auth_client, user_factory):
#         client, _user, _password = auth_client
#         other, _other_password = user_factory()

#         response = client.delete(f"/user/{other.id}")
#         assert response.status_code == 403

#     def test_unknown_id_returns_404(self, auth_client):
#         client, _user, _password = auth_client
#         assert client.delete("/user/999999").status_code == 404
