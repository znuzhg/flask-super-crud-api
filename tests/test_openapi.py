from __future__ import annotations


def test_openapi_and_docs(client):
    r = client.get("/openapi.json")
    assert r.status_code == 200
    data = r.get_json()
    assert "openapi" in data or (isinstance(data, dict) and data)

    r = client.get("/docs")
    assert r.status_code == 200
    r = client.get("/redoc")
    assert r.status_code == 200

