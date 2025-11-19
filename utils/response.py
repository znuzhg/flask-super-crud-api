from __future__ import annotations

"""
JSON response helpers enforcing a consistent envelope:
{
  "success": true/false,
  "data": ...,
  "error": { "code": str, "message": str, "details": any } | null
}
"""

from flask import jsonify
from typing import Any, Optional, Tuple


def json_response(*, data: Any, error: Optional[dict] = None, status: int = 200) -> Tuple[Any, int]:
    body = {
        "success": error is None,
        "data": data,
        "error": error,
    }
    return jsonify(body), status


def error_response(code: str, message: str, *, status: int = 400, details: Any | None = None):
    # Include a backward-compatible alias 'detals' if some clients expect the misspelling.
    err = {"code": code, "message": message, "details": details, "detals": details}
    return json_response(data=None, error=err, status=status)
