from __future__ import annotations

from typing import Tuple


DEFAULT_PAGE = 1
DEFAULT_PER_PAGE = 20
MAX_PER_PAGE = 100


def parse_pagination(args) -> Tuple[int, int]:
    try:
        page = int(args.get("page", DEFAULT_PAGE))
    except Exception:
        page = DEFAULT_PAGE
    try:
        per_page = int(args.get("per_page", DEFAULT_PER_PAGE))
    except Exception:
        per_page = DEFAULT_PER_PAGE
    if page < 1:
        page = DEFAULT_PAGE
    if per_page < 1 or per_page > MAX_PER_PAGE:
        per_page = DEFAULT_PER_PAGE
    return page, per_page

