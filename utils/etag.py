from __future__ import annotations

import hashlib
from datetime import datetime
from typing import Any


def etag_from_timestamp(ts: datetime, extra: str = "") -> str:
    base = f"{ts.timestamp()}:{extra}".encode("utf-8")
    return hashlib.sha256(base).hexdigest()

