from __future__ import annotations


def test_refresh_rotation_revokes_old_tokens(client):
    # Register and login
    r = client.post(
        "/auth/register",
        json={"name": "Dave", "email": "dave@example.com", "password": "davepass"},
    )
    assert r.status_code == 201

    r = client.post("/auth/login", json={"email": "dave@example.com", "password": "davepass"})
    tokens = r.get_json()["data"]
    old_access = tokens["access_token"]
    old_refresh = tokens["refresh_token"]

    # Use old access on protected route (works before rotation)
    r = client.get("/auth/me", headers={"Authorization": f"Bearer {old_access}"})
    assert r.status_code == 200

    # Refresh to rotate tokens
    r = client.post("/auth/refresh", json={"refresh_token": old_refresh})
    assert r.status_code == 200
    new_tokens = r.get_json()["data"]
    new_access = new_tokens["access_token"]
    new_refresh = new_tokens["refresh_token"]
    assert new_access and new_refresh

    # Old access should now be revoked
    r = client.get("/auth/me", headers={"Authorization": f"Bearer {old_access}"})
    assert r.status_code == 401
    assert r.get_json()["error"]["code"] in ("TOKEN_REVOKED", "TOKEN_INVALID")

    # Old refresh should also be revoked
    r = client.post("/auth/refresh", json={"refresh_token": old_refresh})
    assert r.status_code == 401
    assert r.get_json()["error"]["code"] in ("TOKEN_REVOKED", "TOKEN_INVALID")

    # New access works
    r = client.get("/auth/me", headers={"Authorization": f"Bearer {new_access}"})
    assert r.status_code == 200

