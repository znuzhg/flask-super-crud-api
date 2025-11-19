from __future__ import annotations

import json


def test_register_and_login_and_me(client):
    # register
    r = client.post(
        "/auth/register",
        json={"name": "Admin", "email": "admin@example.com", "password": "secret123", "role": "admin"},
    )
    assert r.status_code == 201, r.data
    body = r.get_json()
    assert body["success"] is True
    user_id = body["data"]["id"]
    assert body["data"]["email"] == "admin@example.com"

    # login
    r = client.post(
        "/auth/login",
        json={"email": "admin@example.com", "password": "secret123"},
    )
    assert r.status_code == 200, r.data
    tokens = r.get_json()["data"]
    access = tokens["access_token"]
    refresh = tokens["refresh_token"]
    assert access and refresh

    # me
    r = client.get("/auth/me", headers={"Authorization": f"Bearer {access}"})
    assert r.status_code == 200
    me = r.get_json()["data"]
    assert me["id"] == user_id
    assert me["email"] == "admin@example.com"

    # refresh
    r = client.post("/auth/refresh", json={"refresh_token": refresh})
    assert r.status_code == 200
    new_access = r.get_json()["data"]["access_token"]
    assert new_access

