"""Provider capability profiles, constrained failover and secret scoping."""
from __future__ import annotations

import json
import re
from collections.abc import Callable, Iterator, Mapping, MutableMapping
from contextlib import contextmanager
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from .errors import GardenError
from .security import redact


class FailureKind(str, Enum):
    ABORT = "abort"
    AUTH = "auth"
    INVALID_REQUEST = "invalid_request"
    NOT_FOUND = "not_found"
    CONTEXT_OVERFLOW = "context_overflow"
    RATE_LIMIT = "rate_limit"
    SERVER = "server"
    TIMEOUT = "timeout"
    NETWORK = "network"


TRANSIENT = {FailureKind.RATE_LIMIT, FailureKind.SERVER,
             FailureKind.TIMEOUT, FailureKind.NETWORK}


class ProviderError(GardenError):
    def __init__(self, kind: FailureKind, message: str):
        super().__init__(message)
        self.kind = FailureKind(kind)


@dataclass(frozen=True)
class ProviderProfile:
    name: str
    model: str
    secret_env: str
    fallbacks: tuple[str, ...] = ()
    context_window: int | None = None
    max_output_tokens: int = 8192
    protocol: str = "chat_completions"

    def __post_init__(self) -> None:
        if not re.fullmatch(r"[a-z][a-z0-9_.-]*", self.name):
            raise ValueError("provider name must be lowercase and portable")
        if not self.model or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", self.secret_env):
            raise ValueError("model and environment variable name are required")
        if self.protocol not in {"chat_completions", "responses", "anthropic_messages"}:
            raise ValueError("unsupported provider protocol")
        if self.context_window is not None and self.context_window <= 0:
            raise ValueError("context_window must be positive")
        if self.max_output_tokens <= 0:
            raise ValueError("max_output_tokens must be positive")


Transport = Callable[[ProviderProfile, str, Mapping[str, Any]], Any]


@contextmanager
def scoped_secret(environ: MutableMapping[str, str], name: str, value: str) -> Iterator[str]:
    """Temporarily provide a secret and restore the caller's exact prior state."""
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name) or not value:
        raise ValueError("a valid environment name and non-empty secret are required")
    sentinel = object()
    previous = environ.get(name, sentinel)
    environ[name] = value
    try:
        yield value
    finally:
        if previous is sentinel:
            environ.pop(name, None)
        else:
            environ[name] = previous  # type: ignore[assignment]


@dataclass
class ProviderPool:
    profiles: list[ProviderProfile]
    environ: Mapping[str, str] = field(default_factory=dict)
    max_hops: int = 2
    audit: list[dict[str, object]] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.environ = dict(self.environ)
        if self.max_hops < 0:
            raise ValueError("max_hops cannot be negative")
        if len({profile.name for profile in self.profiles}) != len(self.profiles):
            raise ValueError("duplicate provider name")

    def _chain(self, start: ProviderProfile) -> Iterator[ProviderProfile]:
        by_name = {profile.name: profile for profile in self.profiles}
        seen: set[str] = set()
        current = start
        for index in range(self.max_hops + 1):
            if current.name in seen:
                return
            seen.add(current.name)
            yield current
            fallback = next((name for name in current.fallbacks if name in by_name and name not in seen), None)
            if fallback is None:
                return
            current = by_name[fallback]

    def _safe_error(self, error: ProviderError) -> ProviderError:
        return ProviderError(error.kind, redact(str(error), self.environ.values()))

    def call(self, request: Mapping[str, Any], transport: Transport) -> Any:
        if not self.profiles:
            raise ProviderError(FailureKind.INVALID_REQUEST, "no provider configured")
        requested = request.get("provider")
        start = next((p for p in self.profiles if p.name == requested), self.profiles[0]) if requested else self.profiles[0]
        if requested and start.name != requested:
            raise ProviderError(FailureKind.NOT_FOUND, f"unknown provider: {requested}")
        last: ProviderError | None = None
        for profile in self._chain(start):
            secret = self.environ.get(profile.secret_env)
            if not secret:
                last = ProviderError(FailureKind.AUTH, f"missing environment variable: {profile.secret_env}")
                self.audit.append({"provider": profile.name, "kind": last.kind.value, "ok": False})
                break
            try:
                result = transport(profile, secret, request)
                # Fail early on non-JSON/non-finite output rather than persisting it.
                json.dumps(result, allow_nan=False)
                self.audit.append({"provider": profile.name, "kind": None, "ok": True})
                return result
            except ProviderError as error:
                safe = self._safe_error(error)
                self.audit.append({"provider": profile.name, "kind": safe.kind.value, "ok": False})
                last = safe
                if safe.kind not in TRANSIENT:
                    break
        raise last or ProviderError(FailureKind.NETWORK, "no failover candidate available")
