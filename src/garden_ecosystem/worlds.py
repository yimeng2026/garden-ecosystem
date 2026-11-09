"""Portable agent state and transactional migration with honest rollback outcomes."""
from __future__ import annotations

import copy
import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Protocol

from .errors import GardenError


class LifeState(str, Enum):
    ALIVE = "alive"
    SLEEPING = "sleeping"
    TRAVELING = "traveling"
    DEAD = "dead"
    ARCHIVED = "archived"


@dataclass(frozen=True)
class PortableAgent:
    agent_id: str
    attributes: dict[str, Any]
    lifecycle: LifeState = LifeState.ALIVE
    capabilities: tuple[str, ...] = ()
    extensions: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.agent_id:
            raise ValueError("stable agent_id is required")
        object.__setattr__(self, "lifecycle", LifeState(self.lifecycle))
        object.__setattr__(self, "attributes", copy.deepcopy(self.attributes))
        object.__setattr__(self, "extensions", copy.deepcopy(self.extensions))
        object.__setattr__(self, "capabilities", tuple(self.capabilities))
        json.dumps(self.snapshot(), allow_nan=False)

    def snapshot(self) -> dict[str, Any]:
        return {"agent_id": self.agent_id, "attributes": copy.deepcopy(self.attributes),
                "lifecycle": self.lifecycle.value, "capabilities": list(self.capabilities),
                "extensions": copy.deepcopy(self.extensions)}

    @classmethod
    def from_snapshot(cls, value: dict[str, Any]) -> PortableAgent:
        return cls(value["agent_id"], copy.deepcopy(value["attributes"]), value["lifecycle"],
                   tuple(value["capabilities"]), copy.deepcopy(value["extensions"]))


class WorldAdapter(Protocol):
    name: str
    def snapshot(self, agent_id: str) -> PortableAgent: ...
    def validate(self, agent: PortableAgent) -> None: ...
    def remove(self, agent_id: str) -> None: ...
    def stage(self, agent: PortableAgent) -> None: ...
    def commit(self, agent_id: str) -> None: ...
    def abort(self, agent_id: str) -> None: ...
    def restore(self, agent: PortableAgent) -> None: ...


class MigrationError(GardenError):
    pass


@dataclass
class MemoryWorld:
    name: str
    reject: set[str] = field(default_factory=set)
    fail_commit: set[str] = field(default_factory=set)
    fail_restore: set[str] = field(default_factory=set)
    supported_capabilities: set[str] | None = None
    agents: dict[str, PortableAgent] = field(default_factory=dict)
    staging: dict[str, PortableAgent] = field(default_factory=dict)

    def add(self, agent: PortableAgent) -> None:
        if agent.agent_id in self.agents or agent.agent_id in self.staging:
            raise MigrationError("duplicate agent identity")
        if agent.lifecycle is LifeState.TRAVELING:
            raise MigrationError("traveling agent cannot start another migration")
        self.agents[agent.agent_id] = PortableAgent.from_snapshot(agent.snapshot())

    def snapshot(self, agent_id: str) -> PortableAgent:
        try:
            return PortableAgent.from_snapshot(self.agents[agent_id].snapshot())
        except KeyError as error:
            raise MigrationError(f"agent not found: {agent_id}") from error

    def validate(self, agent: PortableAgent) -> None:
        if agent.agent_id in self.reject:
            raise MigrationError(f"{self.name} rejects {agent.agent_id}")
        if agent.agent_id in self.agents or agent.agent_id in self.staging:
            raise MigrationError(f"{self.name} already contains {agent.agent_id}")
        if self.supported_capabilities is not None:
            unsupported = set(agent.capabilities) - self.supported_capabilities
            if unsupported:
                raise MigrationError(f"unsupported capabilities: {sorted(unsupported)}")

    def remove(self, agent_id: str) -> None:
        self.staging.pop(agent_id, None)
        if agent_id not in self.agents:
            raise MigrationError(f"cannot remove missing agent: {agent_id}")
        del self.agents[agent_id]

    def stage(self, agent: PortableAgent) -> None:
        self.validate(agent)
        self.staging[agent.agent_id] = PortableAgent.from_snapshot(agent.snapshot())

    def commit(self, agent_id: str) -> None:
        if agent_id in self.fail_commit:
            raise MigrationError(f"commit failed: {agent_id}")
        if agent_id not in self.staging:
            raise MigrationError("cannot commit an unstaged agent")
        self.agents[agent_id] = self.staging.pop(agent_id)

    def abort(self, agent_id: str) -> None:
        self.staging.pop(agent_id, None)
        self.agents.pop(agent_id, None)

    def restore(self, agent: PortableAgent) -> None:
        if agent.agent_id in self.fail_restore:
            raise MigrationError(f"source restoration failed: {agent.agent_id}")
        self.add(agent)


@dataclass(frozen=True)
class MigrationResult:
    agent_id: str
    source: str
    target: str
    status: str
    needs_manual_recovery: bool = False
    error: str | None = None
    rollback_error: str | None = None


def migrate(source: WorldAdapter, target: WorldAdapter, agent_id: str) -> MigrationResult:
    snapshot: PortableAgent | None = None
    source_removed = False
    target_touched = False
    try:
        if source.name == target.name:
            raise MigrationError("source and target must differ")
        snapshot = source.snapshot(agent_id)
        target.validate(snapshot)  # Reject before removing the source where possible.
        source.remove(agent_id)
        source_removed = True
        target_touched = True  # Validated target has no pre-existing copy to protect.
        target.stage(snapshot)
        target.commit(agent_id)
        return MigrationResult(agent_id, source.name, target.name, "completed")
    except Exception as error:
        if not source_removed and not target_touched:
            return MigrationResult(agent_id, source.name, target.name,
                                   "failed" if snapshot is None else "rolled_back", error=str(error))
        rollback_errors = []
        if target_touched:
            try:
                target.abort(agent_id)
            except Exception as rollback_error:
                rollback_errors.append(f"target: {rollback_error}")
        if source_removed and snapshot is not None:
            try:
                source.restore(snapshot)
            except Exception as rollback_error:
                rollback_errors.append(f"source: {rollback_error}")
        needs_recovery = bool(rollback_errors)
        return MigrationResult(agent_id, source.name, target.name,
                               "recovery_required" if needs_recovery else "rolled_back",
                               needs_recovery, str(error), "; ".join(rollback_errors) or None)


def self_test(world: WorldAdapter, agent: PortableAgent) -> bool:
    clone = copy.deepcopy(world)
    clone.stage(agent)
    clone.commit(agent.agent_id)
    restored = clone.snapshot(agent.agent_id)
    if restored.snapshot() != agent.snapshot():
        raise MigrationError("isolated import/export round-trip mismatch")
    return True
