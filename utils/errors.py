from __future__ import annotations

"""
Global Flask error handler registration.

Provides consistent JSON responses for common error types using the
json envelope defined in utils.response.
"""

import logging
from flask import Flask
from werkzeug.exceptions import HTTPException, NotFound
from marshmallow import ValidationError

from utils.response import error_response

logger = logging.getLogger(__name__)


def register_error_handlers(app: Flask) -> None:
    """Register global error handlers returning JSON envelopes.

    - ValidationError -> 400 VALIDATION_ERROR with field details
    - NotFound        -> 404 NOT_FOUND
    - HTTPException   -> status from exception, code HTTP_ERROR
    - Exception       -> 500 INTERNAL_ERROR (logged)
    """

    @app.errorhandler(ValidationError)
    def on_validation_error(err: ValidationError):  # type: ignore[override]
        return error_response(
            "VALIDATION_ERROR", "Invalid input", status=400, details=err.messages
        )

    @app.errorhandler(NotFound)
    def on_not_found(err: NotFound):  # type: ignore[override]
        return error_response("NOT_FOUND", "Resource not found", status=404)

    @app.errorhandler(HTTPException)
    def on_http_exception(err: HTTPException):  # type: ignore[override]
        status = err.code or 500
        message = err.description or err.name
        return error_response("HTTP_ERROR", message, status=status)

    @app.errorhandler(Exception)
    def on_exception(err: Exception):  # type: ignore[override]
        logger.exception("Unhandled error: %s", err)
        return error_response("INTERNAL_ERROR", "Unexpected server error", status=500)

