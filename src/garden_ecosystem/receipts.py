"""Resumable execution chains and evidence-level receipts."""
from __future__ import annotations

import copy
import json
import math
import time
import uuid
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from enum import Enum
from typing import Any, Protocol

from .errors import CheckpointMismatch, GardenError
from .security import stable_hash


def public_config(value: Any) -> Any:
    """Return a JSON-safe configuration view with credential-shaped values removed."""
    if isinstance(value, dict):
        result = {}
        for key, item in value.items():
            normalized = str(key).lower().replace("-", "_")
            if (any(part in normalized for part in ("secret", "token", "password", "api_key", "apikey", "credential", "authorization"))
                    or normalized in {"auth", "key"}):
                result[str(key)] = "[redacted]"
            else:
                result[str(key)] = public_config(item)
        return result
    if isinstance(value, (list, tuple)):
        return [public_config(item) for item in value]
    return value


_public = public_config


@dataclass(frozen=True)
class RunManifest:
    run_id: str
    project: str
    config_hash: str
    seed: int
    created_at: float

    @classmethod
    def create(cls, project: str, config: Mapping[str, Any], seed: int,
               clock: Callable[[], float] = time.time) -> RunManifest:
        if not project or isinstance(seed, bool) or not isinstance(seed, int):
            raise ValueError("project and integer seed are required")
        created = clock()
        if not math.isfinite(created):
            raise ValueError("created_at must be finite")
        public = _public(dict(config))
        json.dumps(public, allow_nan=False)
        return cls(uuid.uuid4().hex, project, stable_hash(public), seed, created)

    def snapshot(self) -> dict[str, Any]:
        return {"run_id": self.run_id, "project": self.project,
                "config_hash": self.config_hash, "seed": self.seed, "created_at": self.created_at}


@dataclass(frozen=True)
class Checkpoint:
    run_id: str
    previous_hash: str | None
    hash: str
    action: dict[str, Any]
    state: dict[str, Any]
    created_at: float


class CheckpointStore:
    """In-memory hash chain; persistence belongs to the calling garden service."""

    def __init__(self, clock: Callable[[], float] = time.time):
        self.clock = clock
        self._heads: dict[str, str] = {}
        self._nodes: dict[str, Checkpoint] = {}

    def append(self, run_id: str, previous_hash: str | None,
               action: Mapping[str, Any], state: Mapping[str, Any]) -> Checkpoint:
        current = self._heads.get(run_id)
        if current != previous_hash:
            raise CheckpointMismatch("previous hash is not the current chain head")
        created = self.clock()
        if not math.isfinite(created):
            raise ValueError("checkpoint timestamp must be finite")
        action_copy = copy.deepcopy(dict(action))
        state_copy = copy.deepcopy(dict(state))
        json.dumps(action_copy, allow_nan=False)
        json.dumps(state_copy, allow_nan=False)
        digest = stable_hash({"run_id": run_id, "previous_hash": previous_hash,
                              "action": action_copy, "state": state_copy})
        node = Checkpoint(run_id, previous_hash, digest, action_copy, state_copy, created)
        self._nodes[digest] = node
        self._heads[run_id] = digest
        return copy.deepcopy(node)

    def resume(self, run_id: str, previous_hash: str, action: Mapping[str, Any]) -> Checkpoint:
        current = self._heads.get(run_id)
        if current != previous_hash or current not in self._nodes:
            raise CheckpointMismatch("checkpoint is not the current chain head")
        node = self._nodes[current]
        if stable_hash(node.action) != stable_hash(dict(action)):
            raise CheckpointMismatch("action differs from the recorded checkpoint")
        return copy.deepcopy(node)


class VerificationLevel(str, Enum):
    GENERATED = "generated"
    EXECUTED = "executed"
    MACHINE_CHECKED = "machine_checked"
    NUMERICALLY_REPRODUCED = "numerically_reproduced"
    EXTERNALLY_VALIDATED = "externally_validated"


@dataclass(frozen=True)
class VerificationReceipt:
    level: VerificationLevel
    tool: str
    version: str
    evidence_hash: str
    mock: bool = False
    attested: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "level", VerificationLevel(self.level))
        if not self.tool or not self.version or not self.evidence_hash:
            raise ValueError("tool, version and evidence hash are required")
        if (self.level in {VerificationLevel.MACHINE_CHECKED,
                           VerificationLevel.NUMERICALLY_REPRODUCED,
                           VerificationLevel.EXTERNALLY_VALIDATED}
                and not self.mock and not self.attested):
            raise ValueError("verified receipt requires external attestation or explicit mock=True")

    @classmethod
    def machine_checked(cls, tool: str, version: str, evidence_hash: str,
                        mock: bool = False, attested: bool = False) -> VerificationReceipt:
        if not mock and not attested:
            raise ValueError("real machine-check receipt requires external attestation")
        return cls(VerificationLevel.MACHINE_CHECKED, tool, version, evidence_hash, mock, attested)


@dataclass(frozen=True)
class ToolHealth:
    status: str
    reason: str

    def __post_init__(self) -> None:
        if self.status not in {"available", "degraded", "unavailable"}:
            raise ValueError("invalid tool health status")


class ExternalToolUnavailable(GardenError):
    pass


class ExternalToolAdapter(Protocol):
    name: str
    def health(self) -> ToolHealth: ...
    def execute(self, action: Mapping[str, Any]) -> VerificationReceipt: ...


class UnavailableExternalTool:
    def __init__(self, name: str):
        self.name = name

    def health(self) -> ToolHealth:
        return ToolHealth("unavailable", f"no configured real adapter for {self.name}")

    def execute(self, action: Mapping[str, Any]) -> VerificationReceipt:
        raise ExternalToolUnavailable(f"{self.name} is unavailable; no execution was attempted")
