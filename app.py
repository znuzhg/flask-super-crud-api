"""
Flask REST API entrypoint.

Bootstraps application with:
- flask-smorest OpenAPI generation (/openapi.json)
- Swagger UI (/docs) and Redoc (/redoc) served as simple HTML
- SQLAlchemy engine/session init and teardown
- Logging and health endpoint
"""

from __future__ import annotations

import time
import uuid
import logging
from flask import Flask, request, g, redirect, make_response, jsonify
from flask_smorest import Api

from config.settings import settings
from config.logging_conf import configure_logging
from database.base import init_engine, init_db, remove_session
from routes.auth import auth_bp
from routes.users import users_bp
from routes.admin import admin_bp
from utils.errors import register_error_handlers
from utils.response import json_response
from utils.cache import cache
from utils import metrics as metrics_util


def create_app(database_url: str | None = None) -> Flask:
    configure_logging(settings.LOG_LEVEL)
    app = Flask(__name__)
    app.config["SECRET_KEY"] = settings.SECRET_KEY
    app.config["MAX_CONTENT_LENGTH"] = settings.MAX_CONTENT_LENGTH

    # OpenAPI (flask-smorest) configuration: mount JSON at /openap.json
    app.config.update(
        API_TITLE="MySQL CRUD API",
        API_VERSION="1.0.0",
        OPENAPI_VERSION="3.0.3",
        OPENAPI_URL_PREFIX="/",
        OPENAPI_JSON_PATH="openap.json",
        API_SPEC_OPTIONS={
            "components": {
                "securitySchemes": {
                    "bearerAuth": {
                        "type": "http",
                        "scheme": "bearer",
                        "bearerFormat": "JWT",
                    }
                }
            },
            "security": [{"bearerAuth": []}],
        },
    )

    # DB
    init_engine(database_url or settings.DATABASE_URL)
    init_db()  # for quickstart; use Alembic in production

    # Initialize Api before registering blueprints for proper mounting
    api = Api(app)

    # Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(admin_bp)

    # Error handlers
    register_error_handlers(app)

    # Request logging with correlation id
    logger = logging.getLogger("request")

    @app.before_request
    def _start_timer():
        g.start_time = time.time()
        g.request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

    @app.after_request
    def _log_request(response):
        try:
            duration = (time.time() - g.get("start_time", time.time())) * 1000
            # metrics
            metrics_util.inc_request_count(request.path, request.method, response.status_code)
            metrics_util.observe_latency(request.path, duration)
            logger.info(
                "%s %s %s %d %.2fms req_id=%s",
                request.method,
                request.path,
                request.remote_addr,
                response.status_code,
                duration,
                g.get("request_id"),
            )
            response.headers["X-Request-ID"] = g.get("request_id")
            # CORS and security headers
            response.headers.setdefault("X-Content-Type-Options", "nosniff")
            response.headers.setdefault("X-Frame-Options", "DENY")
            response.headers.setdefault("X-XSS-Protection", "1; mode=block")
            response.headers.setdefault("Content-Security-Policy", "default-src 'self'")
            origins = settings.CORS_ORIGINS
            response.headers.setdefault("Access-Control-Allow-Origin", origins)
            response.headers.setdefault("Access-Control-Allow-Headers", "Authorization, Content-Type, If-Match")
            response.headers.setdefault("Access-Control-Allow-Methods", "GET, POST, PUT, PATCH, DELETE, OPTIONS")
        except Exception:
            pass
        return response

    # Ensure DB session is removed each request/app context
    @app.teardown_appcontext
    def _teardown(_exc):
        remove_session()

    @app.get("/health")
    def health():
        # DB
        db_ok = True
        try:
            from sqlalchemy import text

            s = remove_session.__globals__["db_session"]  # type: ignore
            conn = s().connection()
            conn.execute(text("SELECT 1"))
            db_ok = True
        except Exception:
            db_ok = False

        # Cache (redis)
        cache_ok = cache._client is not None  # type: ignore[attr-defined]

        # Queue status (rq)
        try:
            from redis import Redis  # type: ignore
            from rq import Queue  # type: ignore

            if settings.REDIS_URL:
                redis = Redis.from_url(settings.REDIS_URL)
                q = Queue(connection=redis)
                queue_ok = True
            else:
                queue_ok = False
        except Exception:
            queue_ok = False
        return json_response(data={"status": "ok", "database": db_ok, "cache": cache_ok, "queue": queue_ok})

    # Convenience routes for docs & schema
    @app.get("/docs")
    def docs_page():
        html = """
        <!doctype html>
        <html>
          <head>
            <meta charset='utf-8'/>
            <title>Swagger UI</title>
            <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css" />
          </head>
          <body>
            <div id="swagger-ui"></div>
            <script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
            <script>
              window.ui = SwaggerUIBundle({
                url: '/openapi.json',
                dom_id: '#swagger-ui'
              });
            </script>
          </body>
        </html>
        """
        resp = make_response(html)
        resp.headers["Content-Type"] = "text/html"
        return resp

    @app.get("/swagger.json")
    def swagger_json_alias():
        # Return the same OpenAPI JSON directly (200 OK)
        return jsonify(api.spec.to_dict())

    # The OpenAPI JSON is mounted at /openap.json via flask-smorest configuration.
    # Provide a compatibility alias for the canonical spelling as well.
    @app.get("/openapi.json")
    def openapi_canonical_alias():
        return jsonify(api.spec.to_dict())

    @app.get("/redoc")
    def redoc_page():
        html = """
        <!doctype html>
        <html>
          <head>
            <meta charset='utf-8'/>
            <title>ReDoc</title>
            <script src="https://unpkg.com/redoc@next/bundles/redoc.standalone.js"></script>
          </head>
          <body>
            <redoc spec-url='/openapi.json'></redoc>
          </body>
        </html>
        """
        resp = make_response(html)
        resp.headers["Content-Type"] = "text/html"
        return resp

    # Optional alias: /ap/docs -> /docs
    @app.get("/ap/docs")
    def docs_alias():
        return redirect("/docs", code=302)

    @app.get("/metrics")
    def metrics():
        text = metrics_util.render_prometheus()
        resp = make_response(text, 200)
        resp.headers["Content-Type"] = "text/plain; version=0.0.4"
        return resp

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=settings.DEBUG)
