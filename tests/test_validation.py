from __future__ import annotations


def test_register_validation_errors(client):
    # Missing fields
    r = client.post("/auth/register", json={"email": "bad"})
    assert r.status_code == 400
    body = r.get_json()
    assert body["error"]["code"] == "VALIDATION_ERROR"

    # Invalid email
    r = client.post("/auth/register", json={"name": "x", "email": "bad", "password": "secret123"})
    assert r.status_code == 400


def test_login_wrong_password(client):
    # Create user
    r = client.post(
        "/auth/register",
        json={"name": "Eve", "email": "eve@example.com", "password": "correctpass"},
    )
    assert r.status_code == 201

    # Wrong password
    r = client.post("/auth/login", json={"email": "eve@example.com", "password": "wrongpass"})
    assert r.status_code == 401
    assert r.get_json()["error"]["code"] == "INVALID_CREDENTIALS"

