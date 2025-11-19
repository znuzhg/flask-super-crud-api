from __future__ import annotations


def auth_headers(client, email: str, password: str):
    r = client.post("/auth/login", json={"email": email, "password": password})
    access = r.get_json()["data"]["access_token"]
    return {"Authorization": f"Bearer {access}"}


def test_rbac_enforcement(client):
    # Create admin and a normal user
    r = client.post(
        "/auth/register",
        json={"name": "Admin", "email": "admin@example.com", "password": "secret123", "role": "admin"},
    )
    assert r.status_code == 201

    r = client.post(
        "/auth/register",
        json={"name": "Bob", "email": "bob@example.com", "password": "bobpass"},
    )
    assert r.status_code == 201
    bob_id = r.get_json()["data"]["id"]

    admin_h = auth_headers(client, "admin@example.com", "secret123")
    user_h = auth_headers(client, "bob@example.com", "bobpass")

    # Non-admin cannot list users
    r = client.get("/users", headers=user_h)
    assert r.status_code == 403
    body = r.get_json()
    assert body["error"]["code"] == "FORBIDDEN"

    # Non-admin cannot get another user's details
    r = client.get(f"/users/{bob_id}", headers=user_h)
    # Bob trying to access Bob is allowed only for admin endpoints; we enforce admin only, so expect 403
    assert r.status_code == 403

    # Admin can list
    r = client.get("/users", headers=admin_h)
    assert r.status_code == 200


def test_users_me_endpoint(client):
    # Create user and call /users/me
    r = client.post(
        "/auth/register",
        json={"name": "Carol", "email": "carol@example.com", "password": "carolpass"},
    )
    assert r.status_code == 201
    headers = auth_headers(client, "carol@example.com", "carolpass")
    r = client.get("/users/me", headers=headers)
    assert r.status_code == 200
    me = r.get_json()["data"]
    assert me["email"] == "carol@example.com"

