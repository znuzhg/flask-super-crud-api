from __future__ import annotations

import csv
import io
from flask import Blueprint, Response, request

from utils.security import require_auth
from services import user_service
from utils.response import json_response

try:
    from rq import Queue  # type: ignore
    from redis import Redis  # type: ignore
except Exception:  # pragma: no cover
    Queue = None  # type: ignore
    Redis = None  # type: ignore

from config.settings import settings


admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def _export_csv_sync() -> str:
    items, total = user_service.list_users(1, 10000, sort_dir="asc", sort_by="id")
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "name", "email", "role", "created_at", "is_active"])  # header
    for u in items:
        writer.writerow([u.id, u.name, u.email, u.role, u.created_at.isoformat(), getattr(u, "is_active", True)])
    return output.getvalue()


def _enqueue_export_job():
    if Queue is None or Redis is None or not settings.REDIS_URL:
        return None
    try:
        redis = Redis.from_url(settings.REDIS_URL)
        q = Queue("default", connection=redis)
        job = q.enqueue(_export_csv_sync)
        return job.get_id()
    except Exception:
        return None


@admin_bp.route("/users/export", methods=["GET"])  # backward-compatible sync export
@require_auth(roles="admin")
def export_users(current_user):  # type: ignore[no-redef]
    data = _export_csv_sync()
    return Response(
        data,
        mimetype="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=users.csv",
        },
    )


@admin_bp.route("/users/export", methods=["POST"])  # async when possible
@require_auth(roles="admin")
def export_users_async(current_user):  # type: ignore[no-redef]
    job_id = _enqueue_export_job()
    if not job_id:
        # fallback to sync
        data = _export_csv_sync()
        return Response(
            data,
            mimetype="text/csv",
            headers={
                "Content-Disposition": "attachment; filename=users.csv",
            },
        )
    return json_response(data={"job_id": job_id})


@admin_bp.route("/jobs/<string:job_id>", methods=["GET"])
@require_auth(roles="admin")
def get_job_status(current_user, job_id):  # type: ignore[no-redef]
    if Queue is None or Redis is None or not settings.REDIS_URL:
        return json_response(data={"status": "disabled"})
    try:
        redis = Redis.from_url(settings.REDIS_URL)
        from rq.job import Job  # type: ignore

        job = Job.fetch(job_id, connection=redis)
        status = job.get_status(refresh=True)
        data: dict = {"status": status}
        if job.is_finished and job.result:
            data["result_available"] = True
        return json_response(data=data)
    except Exception:
        return json_response(data={"status": "unknown"})
