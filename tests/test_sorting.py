from __future__ import annotations


def auth_headers(client, email: str, password: str):
    r = client.post("/auth/login", json={"email": email, "password": password})
    access = r.get_json()["data"]["access_token"]
    return {"Authorization": f"Bearer {access}"}


def test_sorting_and_pagination(client):
    # Create admin
    r = client.post(
        "/auth/register",
        json={"name": "Admin", "email": "admin2@example.com", "password": "secret123", "role": "admin"},
    )
    assert r.status_code == 201
    headers = auth_headers(client, "admin2@example.com", "secret123")

    # Create users
    for name in ["Charlie", "Alice", "Bob"]:
        r = client.post(
            "/users",
            json={"name": name, "email": f"{name.lower()}@example.com", "password": "pass1234"},
            headers=headers,
        )
        assert r.status_code == 201

    # Sort by name asc
    r = client.get("/users?sort=asc&sort_by=name", headers=headers)
    assert r.status_code == 200
    items = [i["name"] for i in r.get_json()["data"]["items"]]
    assert items == sorted(items)

