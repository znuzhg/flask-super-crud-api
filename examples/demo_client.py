from __future__ import annotations

from client import APIClient


def main() -> None:
    api = APIClient("http://localhost:5000")
    api.login("admin@example.com", "secret123")
    me = api.get_current_user()
    print("Current user:", me)
    data = api.list_users(page=1, per_page=5)
    print("Users page:", data)


if __name__ == "__main__":
    main()

