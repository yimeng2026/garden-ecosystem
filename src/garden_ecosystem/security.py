"""Deterministic fingerprints and best-effort secret redaction."""
from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable


def stable_hash(value: object) -> str:
    """Hash canonical JSON; NaN and Infinity are never valid evidence."""
    raw = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
        allow_nan=False,
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def redact(text: str, secrets: Iterable[str]) -> str:
    """Remove literal and JSON-escaped secrets; never accept empty replacements."""
    result = str(text)
    unique = {secret for secret in secrets if isinstance(secret, str) and secret}
    for secret in sorted(unique, key=len, reverse=True):
        result = result.replace(secret, "[redacted]")
        result = result.replace(json.dumps(secret, ensure_ascii=False)[1:-1], "[redacted]")
    return result
