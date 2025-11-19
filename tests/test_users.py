from __future__ import annotations


def auth_headers(client, email: str, password: str):
    r = client.post("/auth/login", json={"email": email, "password": password})
    access = r.get_json()["data"]["access_token"]
    return {"Authorization": f"Bearer {access}"}


def test_users_crud_with_pagination(client):
    # Create admin
    r = client.post(
        "/auth/register",
        json={"name": "Admin", "email": "admin@example.com", "password": "secret123", "role": "admin"},
    )
    assert r.status_code == 201

    headers = auth_headers(client, "admin@example.com", "secret123")

    # Create user
    r = client.post(
        "/users",
        json={"name": "Alice", "email": "alice@example.com", "password": "passw0rd"},
        headers=headers,
    )
    assert r.status_code == 201
    alice_id = r.get_json()["data"]["id"]

    # List users
    r = client.get("/users?per_page=1", headers=headers)
    assert r.status_code == 200
    body = r.get_json()["data"]
    assert "items" in body and "meta" in body
    assert body["meta"]["page"] == 1

    # Get user
    r = client.get(f"/users/{alice_id}", headers=headers)
    assert r.status_code == 200
    assert r.get_json()["data"]["email"] == "alice@example.com"

    # Update user
    r = client.put(f"/users/{alice_id}", json={"name": "Alice New"}, headers=headers)
    assert r.status_code == 200
    assert r.get_json()["data"]["name"] == "Alice New"

    # Delete user
    r = client.delete(f"/users/{alice_id}", headers=headers)
    assert r.status_code == 200
    assert r.get_json()["success"] is True

