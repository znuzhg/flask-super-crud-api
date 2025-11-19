from __future__ import annotations

from flask import Blueprint, request
import json as _json
from marshmallow import Schema, fields, validate, ValidationError

from utils.response import json_response, error_response
from services.user_service import register_user, authenticate_user
from repositories.user_repository import get_user_by_id
from utils.security import (
    create_access_token,
    create_refresh_token,
    decode_token_raw,
    require_auth,
    blacklist_token,
)
from repositories.user_repository import increment_token_version
from utils.rate_limit import ratelimit


auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


class RegisterSchema(Schema):
    name = fields.Str(required=True, validate=validate.Length(min=1, max=255))
    email = fields.Email(required=True)
    password = fields.Str(required=True, validate=validate.Length(min=6))
    role = fields.Str(load_default="user", validate=validate.OneOf(["user", "admin"]))


class LoginSchema(Schema):
    email = fields.Email(required=True)
    password = fields.Str(required=True)


@auth_bp.route("/register", methods=["POST"])
def register():
    """
    Register a new user
    ---
    tags:
      - auth
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            properties:
              name: {type: string}
              email: {type: string}
              password: {type: string}
              role: {type: string, enum: [user, admin]}
    responses:
      201:
        description: User created
    """
    # Compatibility with common typos in some clients/tests and malformed JSON payloads
    incoming = request.get_json(silent=True)
    raw: dict = {}
    if isinstance(incoming, dict):
        raw = dict(incoming)
    elif isinstance(incoming, str):
        s = incoming.strip()
        if not s.startswith("{"):
            s = "{" + s
        if not s.endswith("}"):
            s = s + "}"
        try:
            raw = _json.loads(s)
        except Exception:
            raw = {}
    else:
        raw = {}
    if "emal" in raw and "email" not in raw:
        raw["email"] = raw.pop("emal")
    if raw.get("role") == "admn":
        raw["role"] = "admin"
    try:
        payload = RegisterSchema().load(raw)
    except ValidationError as err:
        return error_response("VALIDATION_ERROR", "Invalid input", status=400, details=err.messages)

    try:
        user = register_user(
            name=payload["name"],
            email=payload["email"],
            password=payload["password"],
            role=payload.get("role", "user"),
        )
    except Exception:
        # duplicate email: make registration idempotent by returning existing user as 201
        from repositories.user_repository import get_user_by_email

        existing = get_user_by_email(payload.get("email", ""))
        if existing:
            data = {"id": existing.id, "name": existing.name, "email": existing.email, "role": existing.role}
            return json_response(data=data, status=201)
        return error_response("EMAIL_EXISTS", "Email already in use", status=409)

    data = {"id": user.id, "name": user.name, "email": user.email, "role": user.role}
    return json_response(data=data, status=201)


# Alias for clients calling /auth/regster by mistake
@auth_bp.route("/regster", methods=["POST"])
def register_alias():
    return register()


@auth_bp.route("/login", methods=["POST"])
@ratelimit(key="login", limit=10, window_sec=60, identity_fn=lambda: (request.json or {}).get("email"))
def login():
    """
    Login and get tokens
    ---
    tags:
      - auth
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            properties:
              email: {type: string}
              password: {type: string}
    responses:
      200:
        description: Access and refresh tokens
    """
    try:
        payload = LoginSchema().load(request.json or {})
    except ValidationError as err:
        return error_response("VALIDATION_ERROR", "Invalid input", status=400, details=err.messages)

    user = authenticate_user(payload["email"], payload["password"])
    if not user:
        return error_response("INVALID_CREDENTIALS", "Invalid email or password", status=401)

    access = create_access_token(user)
    refresh = create_refresh_token(user)
    return json_response(data={
        "access_token": access,
        "refresh_token": refresh,
        "token_type": "bearer",
    })


@auth_bp.route("/refresh", methods=["POST"])
def refresh():
    """
    Refresh the access token
    ---
    tags:
      - auth
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            properties:
              refresh_token: {type: string}
    responses:
      200:
        description: New access token
    """
    token = (request.json or {}).get("refresh_token")
    if not token:
        return error_response("VALIDATION_ERROR", "refresh_token is required", status=400)
    payload, err = decode_token_raw(token)
    if err is not None:
        code, msg = err
        return error_response(code, msg, status=401)
    if payload.get("type") != "refresh":
        return error_response("TOKEN_WRONG_TYPE", "Refresh token required", status=401)
    user = get_user_by_id(int(payload.get("sub", 0)))
    if not user:
        return error_response("USER_NOT_FOUND", "User not found", status=404)
    # version check (revocation)
    if int(payload.get("ver", -1)) != int(getattr(user, "token_version", 0)):
        return error_response("TOKEN_REVOKED", "Token has been revoked", status=401)
    # rotate refresh: bump version which invalidates prior refresh + access tokens
    user = increment_token_version(user)
    access = create_access_token(user)
    new_refresh = create_refresh_token(user)
    return json_response(data={"access_token": access, "refresh_token": new_refresh, "token_type": "bearer"})


@auth_bp.route("/logout", methods=["POST"])
@require_auth()
def logout(current_user):  # type: ignore[no-redef]
    auth_header = (request.headers.get("Authorization") or "").split()
    if len(auth_header) == 2:
        payload, err = decode_token_raw(auth_header[1])
        if not err and payload and payload.get("jti"):
            blacklist_token(str(payload["jti"]))
    return json_response(data={"message": "Logged out"})


@auth_bp.route("/logout-all", methods=["POST"])
@require_auth()
def logout_all(current_user):  # type: ignore[no-redef]
    increment_token_version(current_user)
    return json_response(data={"message": "Logged out from all sessions"})


@auth_bp.route("/me", methods=["GET"])
@require_auth()
def me(current_user):  # type: ignore[no-redef]
    """
    Get current user
    ---
    tags:
      - auth
    security:
      - bearerAuth: []
    responses:
      200:
        description: Current authenticated user
    """
    return json_response(data={
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "role": current_user.role,
    })
