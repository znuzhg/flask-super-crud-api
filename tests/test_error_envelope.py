from __future__ import annotations


def test_error_envelope_has_details_and_detals(client):
    # Trigger validation error
    r = client.post("/auth/login", json={"email": "not-an-email"})
    assert r.status_code == 400
    body = r.get_json()
    assert body["success"] is False
    assert body["data"] is None
    assert "error" in body
    err = body["error"]
    # Either marshalling path, ensure both keys exist
    assert "details" in err
    assert "detals" in err

