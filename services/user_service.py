from __future__ import annotations

from typing import Optional

from repositories.user_repository import (
    create_user as repo_create_user,
    get_user_by_email as repo_get_by_email,
    get_user_by_id as repo_get_by_id,
    update_user as repo_update_user,
    delete_user as repo_delete_user,
    list_users as repo_list_users,
)
from utils.security import hash_password
from utils.cache import cache


def register_user(name: str, email: str, password: str, role: str = "user"):
    password_hash = hash_password(password)
    user = repo_create_user(name=name, email=email, password_hash=password_hash, role=role)
    cache.invalidate_prefix("users:list:")
    return user


def authenticate_user(email: str, password: str):
    user = repo_get_by_email(email)
    if not user:
        return None
    from utils.security import verify_password

    if not verify_password(password, user.password_hash):
        return None
    return user


def get_user(user_id: int):
    return repo_get_by_id(user_id)


def update_user(user_id: int, *, name: Optional[str] = None, email: Optional[str] = None):
    user = repo_get_by_id(user_id)
    if not user:
        return None
    user = repo_update_user(user, name=name, email=email)
    cache.invalidate_prefix("users:list:")
    return user


def delete_user(user_id: int) -> bool:
    user = repo_get_by_id(user_id)
    if not user:
        return False
    repo_delete_user(user)
    cache.invalidate_prefix("users:list:")
    return True


def list_users(
    page: int,
    per_page: int,
    *,
    name: Optional[str] = None,
    email: Optional[str] = None,
    sort_dir: str = "desc",
    sort_by: str = "created_at",
):
    return repo_list_users(page, per_page, name=name, email=email, sort_dir=sort_dir, sort_by=sort_by)
