from __future__ import annotations

import requests
from typing import Any, Dict, Optional


class APIClient:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None

    def _headers(self) -> Dict[str, str]:
        h = {"Content-Type": "application/json"}
        if self.access_token:
            h["Authorization"] = f"Bearer {self.access_token}"
        return h

    def login(self, email: str, password: str) -> None:
        r = requests.post(f"{self.base_url}/auth/login", json={"email": email, "password": password})
        r.raise_for_status()
        data = r.json()["data"]
        self.access_token = data["access_token"]
        self.refresh_token = data["refresh_token"]

    def refresh(self) -> None:
        assert self.refresh_token
        r = requests.post(f"{self.base_url}/auth/refresh", json={"refresh_token": self.refresh_token})
        r.raise_for_status()
        data = r.json()["data"]
        self.access_token = data["access_token"]
        self.refresh_token = data.get("refresh_token", self.refresh_token)

    def get_current_user(self) -> Dict[str, Any]:
        r = requests.get(f"{self.base_url}/users/me", headers=self._headers())
        r.raise_for_status()
        return r.json()["data"]

    def list_users(self, **params: Any) -> Dict[str, Any]:
        r = requests.get(f"{self.base_url}/users", headers=self._headers(), params=params)
        r.raise_for_status()
        return r.json()["data"]

    def create_user(self, name: str, email: str, password: str, role: str = "user") -> Dict[str, Any]:
        r = requests.post(
            f"{self.base_url}/users",
            headers=self._headers(),
            json={"name": name, "email": email, "password": password, "role": role},
        )
        r.raise_for_status()
        return r.json()["data"]

    def update_user(self, user_id: int, **fields: Any) -> Dict[str, Any]:
        r = requests.put(f"{self.base_url}/users/{user_id}", headers=self._headers(), json=fields)
        r.raise_for_status()
        return r.json()["data"]

    def delete_user(self, user_id: int) -> None:
        r = requests.delete(f"{self.base_url}/users/{user_id}", headers=self._headers())
        r.raise_for_status()

    def admin_export_users(self) -> bytes:
        r = requests.get(f"{self.base_url}/admin/users/export", headers=self._headers())
        r.raise_for_status()
        return r.content

