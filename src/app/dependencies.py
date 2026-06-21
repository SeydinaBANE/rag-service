"""Injectable FastAPI dependencies (overridable in tests)."""

from __future__ import annotations

from fastapi import Header, HTTPException

from app.config import get_settings
from app.governance import Principal


def get_principal(
    x_api_key: str = Header(..., description="API key for authentication"),
) -> Principal:
    """Resolve the authenticated principal from the ``X-API-Key`` header.

    Missing header → 422 (FastAPI required header); unknown key → 401.
    """
    role = get_settings().api_key_mapping.get(x_api_key)
    if role is None:
        raise HTTPException(status_code=401, detail="invalid API key")
    return Principal(user_id=f"key:{x_api_key[:8]}", roles=frozenset({role}))
