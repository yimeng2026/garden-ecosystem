"""Small, JSON-safe bridge for the existing garden service."""
from __future__ import annotations

from dataclasses import asdict
from typing import Iterable

from . import __version__
from .receipts import ExternalToolAdapter


def capabilities() -> dict[str, object]:
    return {
        "name": "garden-ecosystem", "version": __version__, "protocol": "python-dict-v1",
        "default_policy": "deny", "network": "injected_only",
        "external_tools": "explicit_adapters_only",
        "modules": ["providers", "context", "reliability", "worlds", "evaluation",
                    "learning", "research", "receipts", "lean", "service", "proof"],
    }


def health(tools: Iterable[ExternalToolAdapter] = ()) -> dict[str, object]:
    return {
        "ok": True, "learning_enabled": False, "secrets_loaded": False,
        "tools": {tool.name: asdict(tool.health()) for tool in tools},
    }
