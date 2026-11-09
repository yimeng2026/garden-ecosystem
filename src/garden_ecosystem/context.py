"""Conservative context accounting and bounded tool-output handling."""
from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .errors import BudgetExceeded
from .security import stable_hash


def estimate_tokens(text: str) -> int:
    """A conservative scheduler estimate, not a provider billing measurement."""
    cjk = sum(0x3000 <= ord(char) <= 0x9FFF or 0xF900 <= ord(char) <= 0xFAFF
              or 0xFF00 <= ord(char) <= 0xFFEF for char in text)
    return cjk + math.ceil((len(text) - cjk) / 4)


@dataclass(frozen=True)
class UsageAnchor:
    model: str
    prefix_hash: str
    input_tokens: int

    def __post_init__(self) -> None:
        if isinstance(self.input_tokens, bool) or self.input_tokens <= 0:
            raise ValueError("input_tokens must be positive")


@dataclass(frozen=True)
class Budget:
    tokens: int
    available: int | None
    input_tokens: int
    source: str


def _integer(value: Any, name: str, *, positive: bool = False) -> int:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{name} must be a finite integer")
    if int(value) != value or (value <= 0 if positive else value < 0):
        raise ValueError(f"{name} has an invalid value")
    return int(value)


def resolve_budget(messages: object, model: str, window: int | None,
                   configured: int, anchor: UsageAnchor | None = None,
                   tools: int = 0, reserve: int = 64, minimum: int = 1) -> Budget:
    configured = _integer(configured, "configured", positive=True)
    tools = _integer(tools, "tools")
    reserve = _integer(reserve, "reserve")
    minimum = _integer(minimum, "minimum", positive=True)
    matches = bool(anchor and anchor.model == model and anchor.prefix_hash == stable_hash(messages))
    used = anchor.input_tokens if matches and anchor else estimate_tokens(
        json.dumps(messages, ensure_ascii=False, allow_nan=False)
    )
    source = "measured" if matches else "estimate"
    if window is None:
        return Budget(configured, None, used, "configured")
    window = _integer(window, "window", positive=True)
    available = window - used - tools - reserve
    if available < minimum:
        raise BudgetExceeded(f"output budget unavailable: {available}; minimum required: {minimum}")
    return Budget(min(configured, available), available, used, source)


class ToolOutputGovernor:
    def __init__(self, workspace: str | Path, inline_limit: int = 4000,
                 reference_threshold: int = 12000, max_file_bytes: int = 1_000_000):
        self.workspace = Path(workspace).resolve(strict=True)
        if not self.workspace.is_dir():
            raise ValueError("workspace must be an existing directory")
        if inline_limit <= 0 or reference_threshold < inline_limit or max_file_bytes <= 0:
            raise ValueError("invalid output limits")
        self.inline_limit = inline_limit
        self.reference_threshold = reference_threshold
        self.max_file_bytes = max_file_bytes

    def resolve(self, relative_path: str) -> Path:
        if not isinstance(relative_path, str) or not relative_path.strip():
            raise ValueError("a relative file path is required")
        candidate = Path(relative_path)
        if (candidate.is_absolute() or relative_path.startswith(("/", "\\"))
                or ".." in candidate.parts):
            raise ValueError("absolute paths and parent traversal are forbidden")
        try:
            resolved = (self.workspace / candidate).resolve(strict=True)
        except OSError as error:
            raise ValueError("path must resolve to a file inside the workspace") from error
        if not resolved.is_relative_to(self.workspace) or not resolved.is_file():
            raise ValueError("path must resolve to a file inside the workspace")
        return resolved

    def govern(self, text: str, relative_path: str | None = None) -> dict[str, Any]:
        if len(text) <= self.inline_limit:
            return {"kind": "raw", "text": text, "truncated": False}
        if len(text) <= self.reference_threshold:
            side = self.inline_limit // 2
            omitted = len(text) - 2 * side
            return {"kind": "excerpt", "text": text[:side] + f"\n[omitted {omitted} chars]\n" + (text[-side:] if side else ""),
                    "omitted_chars": omitted, "truncated": True}
        if relative_path is None:
            raise ValueError("large output requires a workspace-relative source reference")
        path = self.resolve(relative_path)
        return {"kind": "reference", "path": path.relative_to(self.workspace).as_posix(),
                "chars": len(text), "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                "note": "output is not inlined; use bounded interval reads"}

    def summary(self, text: str) -> dict[str, str]:
        return {"kind": "summary", "text": text, "notice": "summary, not original evidence"}

    def read_interval(self, relative_path: str, start: int = 0, end: int | None = None) -> dict[str, Any]:
        path = self.resolve(relative_path)
        start = _integer(start, "start")
        if end is not None:
            end = _integer(end, "end")
            if end < start:
                raise ValueError("end must not precede start")
        if path.stat().st_size > self.max_file_bytes:
            raise BudgetExceeded("file exceeds the bounded-reader byte limit")
        text = path.read_text(encoding="utf-8")
        return {"kind": "raw", "path": path.relative_to(self.workspace).as_posix(),
                "text": text[start:end], "start": start, "end": min(len(text), end) if end is not None else len(text)}


class IntervalCache:
    def __init__(self, workspace: str | Path):
        self.governor = ToolOutputGovernor(workspace)
        self._entries: dict[tuple[str, int, int | None, str], dict[str, Any]] = {}

    def get(self, relative_path: str, start: int = 0, end: int | None = None) -> dict[str, Any]:
        path = self.governor.resolve(relative_path)
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        key = (path.relative_to(self.governor.workspace).as_posix(), start, end, digest)
        if key in self._entries:
            return {**self._entries[key], "cache_hit": True}
        result = self.governor.read_interval(relative_path, start, end)
        self._entries[key] = result
        return {**result, "cache_hit": False}
