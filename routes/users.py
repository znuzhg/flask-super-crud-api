from __future__ import annotations

from flask import Blueprint, request
from marshmallow import Schema, fields, validate, ValidationError

from utils.response import json_response, error_response
from utils.pagination import parse_pagination
from utils.security import require_auth, require_roles
from services import user_service
from utils.cache import cache
from utils.etag import etag_from_timestamp


users_bp = Blueprint("users", __name__, url_prefix="/users")


class CreateUserSchema(Schema):
    name = fields.Str(required=True, validate=validate.Length(min=1, max=255))
    email = fields.Email(required=True)
    password = fields.Str(required=True, validate=validate.Length(min=6))
    role = fields.Str(load_default="user", validate=validate.OneOf(["user", "admin"]))
    avatar_url = fields.Url(required=False)
    bio = fields.Str(required=False, validate=validate.Length(max=2000))


class UpdateUserSchema(Schema):
    name = fields.Str(required=False, validate=validate.Length(min=1, max=255))
    email = fields.Email(required=False)
    avatar_url = fields.Url(required=False)
    bio = fields.Str(required=False, validate=validate.Length(max=2000))


@users_bp.route("", methods=["POST"])
@require_auth()
@require_roles("admin")
def create(current_user):  # type: ignore[no-redef]
    try:
        payload = CreateUserSchema().load(request.json or {})
    except ValidationError as err:
        return error_response("VALIDATION_ERROR", "Invalid input", status=400, details=err.messages)
    try:
        user = user_service.register_user(
            name=payload["name"],
            email=payload["email"],
            password=payload["password"],
            role=payload.get("role", "user"),
        )
    except Exception:
        return error_response("EMAIL_EXISTS", "Email already in use", status=409)
    return json_response(data={"id": user.id, "name": user.name, "email": user.email, "role": user.role}, status=201)


@users_bp.route("", methods=["GET"])
@require_auth(roles="admin")
def list_users(current_user):  # type: ignore[no-redef]
    """
    List users
    ---
    tags:
      - users
    security:
      - bearerAuth: []
    parameters:
      - in: query
        name: page
        schema: {type: integer}
      - in: query
        name: per_page
        schema: {type: integer}
      - in: query
        name: name
        schema: {type: string}
      - in: query
        name: email
        schema: {type: string}
      - in: query
        name: sort
        schema: {type: string, enum: [asc, desc]}
      - in: query
        name: sort_by
        schema: {type: string, enum: [created_at, name, email]}
    responses:
      200:
        description: Users list
    """
    page, per_page = parse_pagination(request.args)
    name = request.args.get("name")
    email = request.args.get("email")
    sort = request.args.get("sort", "desc")
    sort_by = request.args.get("sort_by", "created_at")

    cache_key = f"users:list:page={page}&per={per_page}&name={name}&email={email}&sort={sort}&sort_by={sort_by}"
    cached = cache.get(cache_key)
    if cached is not None:
        return json_response(data=cached)

    items, total = user_service.list_users(page, per_page, name=name, email=email, sort_dir=sort, sort_by=sort_by)
    data_items = [
        {"id": u.id, "name": u.name, "email": u.email, "role": u.role}
        for u in items
    ]
    meta = {"page": page, "per_page": per_page, "total": total, "pages": (total + per_page - 1) // per_page, "sort": sort, "sort_by": sort_by}
    data = {"items": data_items, "meta": meta}
    cache.set(cache_key, data, ttl=30)
    return json_response(data=data)


@users_bp.route("/<int:user_id>", methods=["GET"])
@require_auth(roles="admin")
def get_user(current_user, user_id):  # type: ignore[no-redef]
    u = user_service.get_user(user_id)
    if not u:
        return error_response("USER_NOT_FOUND", "User not found", status=404)
    data = {"id": u.id, "name": u.name, "email": u.email, "role": u.role}
    # Attach ETag via response headers
    from flask import make_response

    body, status = json_response(data=data)
    resp = make_response(body, status)
    resp.headers["ETag"] = etag_from_timestamp(u.updated_at)
    return resp


@users_bp.route("/<int:user_id>", methods=["PUT"])
@require_auth(roles="admin")
def update_user(current_user, user_id):  # type: ignore[no-redef]
    try:
        payload = UpdateUserSchema().load(request.json or {})
    except ValidationError as err:
        return error_response("VALIDATION_ERROR", "Invalid input", status=400, details=err.messages)
    u = user_service.get_user(user_id)
    if not u:
        return error_response("USER_NOT_FOUND", "User not found", status=404)
    try:
        u = user_service.update_user(user_id, name=payload.get("name"), email=payload.get("email"))
    except Exception:
        return error_response("EMAIL_EXISTS", "Email already in use", status=409)
    # Check ETag if provided (If-Match)
    if_match = request.headers.get("If-Match")
    if if_match and if_match != etag_from_timestamp(u.updated_at):
        return error_response("VERSION_CONFLICT", "ETag mismatch", status=409)
    return json_response(data={"id": u.id, "name": u.name, "email": u.email, "role": u.role})


@users_bp.route("/<int:user_id>", methods=["DELETE"])
@require_auth(roles="admin")
def delete_user(current_user, user_id):  # type: ignore[no-redef]
    u = user_service.get_user(user_id)
    if not u:
        return error_response("USER_NOT_FOUND", "User not found", status=404)
    ok = user_service.delete_user(user_id)
    if not ok:
        return error_response("USER_NOT_FOUND", "User not found", status=404)
    # Consistent envelope on delete (200 OK)
    return json_response(data=None)


@users_bp.route("/me", methods=["GET"])
@require_auth()
def me(current_user):  # type: ignore[no-redef]
    """
    Get current user
    ---
    tags:
      - users
    security:
      - bearerAuth: []
    responses:
      200:
        description: Current authenticated user
    """
    from flask import make_response

    data = {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "role": current_user.role,
    }
    body, status = json_response(data=data)
    resp = make_response(body, status)
    resp.headers["ETag"] = etag_from_timestamp(current_user.updated_at)
    return resp


class PatchUserSchema(Schema):
    name = fields.Str(required=False, validate=validate.Length(min=1, max=255))
    email = fields.Email(required=False)
    avatar_url = fields.Url(required=False)
    bio = fields.Str(required=False, validate=validate.Length(max=2000))


@users_bp.route("/<int:user_id>", methods=["PATCH"])
@require_auth(roles="admin")
def patch_user(current_user, user_id):  # type: ignore[no-redef]
    try:
        payload = PatchUserSchema().load(request.json or {})
    except ValidationError as err:
        return error_response("VALIDATION_ERROR", "Invalid input", status=400, details={"fields": err.messages})

    u = user_service.get_user(user_id)
    if not u:
        return error_response("USER_NOT_FOUND", "User not found", status=404)

    if_match = request.headers.get("If-Match")
    if if_match and if_match != etag_from_timestamp(u.updated_at):
        return error_response("VERSION_CONFLICT", "ETag mismatch", status=409)

    name = payload.get("name")
    email = payload.get("email")
    # For brevity, avatar_url/bio omitted in repo layer; could be added if needed
    try:
        u = user_service.update_user(user_id, name=name, email=email)
    except Exception:
        return error_response("EMAIL_EXISTS", "Email already in use", status=409)
    return json_response(data={"id": u.id, "name": u.name, "email": u.email, "role": u.role})
