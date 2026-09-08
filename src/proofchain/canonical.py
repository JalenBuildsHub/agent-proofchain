"""Portable canonical JSON helpers for receipt payloads."""

from __future__ import annotations

import json
from typing import Any


def canonical_json(payload: Any) -> str:
    """Serialize a receipt using stable keys and literal UTF-8 text."""
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )
