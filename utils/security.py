from __future__ import annotations

import datetime as dt
import hashlib
import uuid
from functools import wraps
from typing import Callable, Iterable, Optional, Tuple

import jwt
from flask import request, g
from passlib.hash import bcrypt

from config.settings import settings
from repositories.user_repository import get_user_by_id
from utils.response import error_response


def hash_password(password: str) -> str:
    return bcrypt.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.verify(password, password_hash)
    except Exception:
        return False


# In-memory token blacklist (fallback). For production, use persistent store.
_blacklisted_jtis: set[str] = set()


def blacklist_token(jti: str) -> None:
    import logging

    logging.getLogger(__name__).info("Token blacklisted jti=%s", jti)
    _blacklisted_jtis.add(jti)


def is_token_blacklisted(jti: str) -> bool:
    return jti in _blacklisted_jtis


def _fingerprint_from_request() -> str:
    ip = request.headers.get("X-Forwarded-For", request.remote_addr or "")
    ua = request.headers.get("User-Agent", "")
    raw = f"{ip}|{ua}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _encode_token(user, *, refresh: bool = False) -> str:
    exp_seconds = settings.REFRESH_TOKEN_EXPIRES if refresh else settings.ACCESS_TOKEN_EXPIRES
    now = dt.datetime.utcnow()
    payload = {
        "sub": str(user.id),
        "role": user.role,
        "type": "refresh" if refresh else "access",
        "ver": int(getattr(user, "token_version", 0)),
        "iat": now,
        "nbf": now,
        "exp": now + dt.timedelta(seconds=exp_seconds),
        "iss": "mysql-crud-api",
        "jti": str(uuid.uuid4()),
        "fp": _fingerprint_from_request(),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALG)


def create_access_token(user) -> str:
    return _encode_token(user, refresh=False)


def create_refresh_token(user) -> str:
    return _encode_token(user, refresh=True)


def decode_token_raw(token: str):
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALG])
        return payload, None
    except jwt.ExpiredSignatureError:
        return None, ("TOKEN_EXPIRED", "Token expired")
    except jwt.InvalidSignatureError:
        return None, ("TOKEN_INVALID_SIGNATURE", "Invalid token signature")
    except jwt.InvalidTokenError:
        return None, ("TOKEN_INVALID", "Invalid token")
    except Exception:
        return None, ("TOKEN_INVALID", "Invalid token")


def decode_token(token: str, *, refresh: bool = False):
    payload, err = decode_token_raw(token)
    if err is not None:
        return None
    expected_type = "refresh" if refresh else "access"
    if payload.get("type") != expected_type:
        return None
    return payload


def require_auth(roles: Optional[Iterable[str] | str] = None):
    """Authenticate via Bearer token and optionally enforce roles.

    Compatible with previous usage without arguments: `@require_auth()`.
    Also supports inline RBAC: `@require_auth(roles="admin")` or
    `@require_auth(roles=["admin", "manager"])`.
    """

    # Normalize roles to a set, or None
    if isinstance(roles, str):
        required_roles = {roles}
    elif roles is None:
        required_roles = None
    else:
        required_roles = set(roles)

    def decorator(fn: Callable):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            auth_header = request.headers.get("Authorization", "")
            parts = auth_header.split()
            if len(parts) != 2 or parts[0].lower() != "bearer":
                return error_response("MISSING_AUTH_HEADER", "Missing or invalid Authorization header", status=401)

            payload, err = decode_token_raw(parts[1])
            if err is not None:
                code, msg = err
                return error_response(code, msg, status=401)

            if payload.get("type") != "access":
                return error_response("TOKEN_WRONG_TYPE", "Access token required", status=401)

            # Check blacklist
            if is_token_blacklisted(str(payload.get("jti", ""))):
                return error_response("TOKEN_REVOKED", "Token has been revoked", status=401)

            user = get_user_by_id(int(payload.get("sub", 0)))
            if not user:
                return error_response("USER_NOT_FOUND", "User not found", status=404)

            # token rotation / revocation via version check
            if int(payload.get("ver", -1)) != int(getattr(user, "token_version", 0)):
                return error_response("TOKEN_REVOKED", "Token has been revoked", status=401)

            # Fingerprint check (best-effort)
            fp = payload.get("fp")
            if fp and fp != _fingerprint_from_request():
                return error_response("TOKEN_CONTEXT_MISMATCH", "Token context mismatch", status=401)

            if required_roles is not None and user.role not in required_roles:
                return error_response("FORBIDDEN", "Not allowed", status=403)

            try:
                g.current_user_id = user.id
            except Exception:
                pass
            return fn(user, *args, **kwargs)

        return wrapper

    return decorator


def require_roles(*roles: str):
    def decorator(fn: Callable):
        @wraps(fn)
        def wrapper(current_user, *args, **kwargs):
            if current_user.role not in roles:
                return error_response("FORBIDDEN", "Not allowed", status=403)
            return fn(current_user, *args, **kwargs)

        return wrapper

    return decorator
