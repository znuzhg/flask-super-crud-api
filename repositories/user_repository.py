from __future__ import annotations

from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError

from database.base import get_session
from models.user import User


def create_user(name: str, email: str, password_hash: str, role: str = "user") -> User:
    session = get_session()
    user = User(name=name, email=email, password_hash=password_hash, role=role)
    session.add(user)
    try:
        session.commit()
    except Exception:
        session.rollback()
        raise
    session.refresh(user)
    return user


def get_user_by_email(email: str) -> Optional[User]:
    session = get_session()
    stmt = select(User).where(User.email == email, User.deleted_at.is_(None))
    return session.execute(stmt).scalar_one_or_none()


def get_user_by_id(user_id: int) -> Optional[User]:
    session = get_session()
    stmt = select(User).where(User.id == user_id, User.deleted_at.is_(None))
    return session.execute(stmt).scalar_one_or_none()


def update_user(user: User, *, name: Optional[str] = None, email: Optional[str] = None) -> User:
    session = get_session()
    if name is not None:
        user.name = name
    if email is not None:
        user.email = email
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise
    session.refresh(user)
    return user


def delete_user(user: User) -> None:
    session = get_session()
    # soft delete
    from datetime import datetime
    user.deleted_at = datetime.utcnow()
    session.commit()


def increment_token_version(user: User) -> User:
    session = get_session()
    # initialize if missing for legacy rows
    current = int(getattr(user, "token_version", 0) or 0)
    user.token_version = current + 1  # type: ignore[attr-defined]
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def list_users(
    page: int,
    per_page: int,
    *,
    name: Optional[str] = None,
    email: Optional[str] = None,
    sort_dir: str = "desc",
    sort_by: str = "created_at",
):
    session = get_session()
    stmt = select(User)
    stmt = stmt.where(User.deleted_at.is_(None))
    if name:
        stmt = stmt.where(User.name.ilike(f"%{name}%"))
    if email:
        stmt = stmt.where(User.email.ilike(f"%{email}%"))

    total = session.execute(select(func.count()).select_from(stmt.subquery())).scalar() or 0

    if sort_dir not in {"asc", "desc"}:
        sort_dir = "desc"
    # Map sort_by to a valid column
    sort_map = {
        "id": User.id,
        "created_at": User.created_at,
        "name": User.name,
        "email": User.email,
    }
    order_base = sort_map.get(sort_by, User.created_at)
    order_column = order_base.asc() if sort_dir == "asc" else order_base.desc()
    stmt = stmt.order_by(order_column).offset((page - 1) * per_page).limit(per_page)

    items = [row[0] for row in session.execute(stmt).all()]
    return items, total
