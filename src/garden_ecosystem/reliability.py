"""Default-deny runtime gate; this is not a substitute for an OS sandbox."""
from __future__ import annotations

import json
import re
import secrets as random_secrets
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field, replace
from enum import Enum
from pathlib import Path
from typing import Any

from .security import redact, stable_hash


class DecisionType(str, Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    ASK = "ASK"
    MODIFY = "MODIFY"


@dataclass(frozen=True)
class Action:
    actor: str
    tool: str
    target: str
    args: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.actor or not self.tool or not isinstance(self.target, str):
            raise ValueError("actor, tool and target are required")
        # Validate serializability at the boundary, before an approval is issued.
        json.dumps(self.args, allow_nan=False)

    @property
    def fingerprint(self) -> str:
        return stable_hash({"actor": self.actor, "tool": self.tool,
                            "target": self.target, "args": self.args})


@dataclass(frozen=True)
class Decision:
    type: DecisionType
    reason: str
    executable: bool = False
    suggested: Action | None = None
    policy: str = ""


@dataclass(frozen=True)
class ApprovalTicket:
    ticket_id: str
    action_hash: str
    actor: str
    expires_at: float


READ_TOOLS = {"read_file", "search", "list", "get", "status", "inspect"}
DESTRUCTIVE = re.compile(r"\b(drop\s+table|drop\s+database|delete\s+from|truncate\s+table|rm\s+-rf)\b", re.I)


class Guard:
    def __init__(self, *, secrets: tuple[str, ...] | list[str] = (),
                 clock: Callable[[], float] = time.time):
        self.secrets = tuple(secret for secret in secrets if secret)
        self.clock = clock
        self.audit: list[dict[str, Any]] = []
        self._tickets: dict[str, ApprovalTicket] = {}

    def _decision(self, kind: DecisionType, reason: str, policy: str,
                  suggested: Action | None = None) -> Decision:
        return Decision(kind, reason, kind is DecisionType.ALLOW, suggested, policy)

    def check(self, action: Action) -> Decision:
        target = action.target.lower()
        path = Path(action.target)
        unsafe_path = path.is_absolute() or action.target.startswith(("/", "\\")) or ".." in path.parts
        if action.tool in READ_TOOLS:
            if unsafe_path:
                return self._decision(DecisionType.DENY, "path outside the approved workspace", "WORKSPACE_BOUNDARY")
            return self._decision(DecisionType.ALLOW, "read-only action inside the workspace", "READ_ONLY")
        if action.tool == "write_file" and self._is_test_path(target):
            suggested = replace(action, target=f"src/{self._source_name(target)}")
            return self._decision(DecisionType.MODIFY, "test path change requires a source suggestion and review",
                                  "TEST_REVIEW", suggested)
        if action.tool in {"shell", "database"}:
            if DESTRUCTIVE.search(target):
                return self._decision(DecisionType.DENY, "destructive command is forbidden", "NO_DESTRUCTIVE")
            return self._decision(DecisionType.DENY, "commands are denied by default; use a reviewed executor",
                                  "COMMAND_REVIEW")
        if action.tool == "git" and re.search(r"push\s+(?:\S+\s+)*-(?:f|-force)\b", target):
            return self._decision(DecisionType.DENY, "force push is forbidden", "NO_FORCE_PUSH")
        if action.tool in {"spend", "transfer"}:
            amount = action.args.get("amount", 0)
            if isinstance(amount, bool) or not isinstance(amount, (int, float)) or amount < 0:
                return self._decision(DecisionType.DENY, "invalid spend amount", "SPEND_LIMIT")
            return self._decision(DecisionType.DENY if amount >= 1000 else DecisionType.ASK,
                                  "spend requires review", "SPEND_LIMIT")
        if action.tool in {"deploy", "git", "issue_key"}:
            return self._decision(DecisionType.ASK, "external side effect requires explicit approval", "EXTERNAL_EFFECT")
        return self._decision(DecisionType.DENY, "state-changing or unknown action is denied by default", "DEFAULT_DENY")

    @staticmethod
    def _is_test_path(target: str) -> bool:
        name = Path(target).name
        return name.startswith("test_") or name.endswith("_test.py") or "/tests/" in f"/{target}"

    @staticmethod
    def _source_name(target: str) -> str:
        name = Path(target).name
        if name.startswith("test_"):
            return name[len("test_"):]
        return name.removesuffix("_test.py") + ".py"

    def approve(self, action: Action, ttl_seconds: float = 300) -> ApprovalTicket:
        if self.check(action).type is not DecisionType.ASK:
            raise ValueError("approval is only available for ASK decisions")
        if ttl_seconds <= 0:
            raise ValueError("approval lifetime must be positive")
        ticket = ApprovalTicket(random_secrets.token_urlsafe(24), action.fingerprint,
                                action.actor, self.clock() + ttl_seconds)
        self._tickets[ticket.ticket_id] = ticket
        return ticket

    def _consume(self, ticket: ApprovalTicket, action: Action) -> bool:
        current = self._tickets.get(ticket.ticket_id)
        if current is None or current != ticket:
            return False
        if current.expires_at <= self.clock():
            self._tickets.pop(ticket.ticket_id, None)
            return False
        if current.actor != action.actor or current.action_hash != action.fingerprint:
            return False
        self._tickets.pop(ticket.ticket_id)
        return True

    def execute(self, action: Action, executor: Callable[[Action], Any],
                ticket: ApprovalTicket | None = None) -> dict[str, Any]:
        decision = self.check(action)
        permitted = decision.type is DecisionType.ALLOW or (
            decision.type is DecisionType.ASK and ticket is not None and self._consume(ticket, action)
        )
        record: dict[str, Any] = {
            "actor": action.actor, "tool": action.tool,
            "target": redact(action.target, self.secrets),
            "decision": decision.type.value, "policy": decision.policy,
            "executed": False, "status": "not_executed",
        }
        if permitted:
            try:
                result = executor(action)
                json.dumps(result, allow_nan=False)
                record.update(executed=True, status="completed", result=result)
            except Exception as error:  # Boundary: report failure, never convert it to success.
                record.update(status="error", error=redact(f"{type(error).__name__}: {error}", self.secrets))
        elif decision.type is DecisionType.ASK:
            record["status"] = "approval_required"
        elif decision.type is DecisionType.MODIFY:
            record["status"] = "suggestion_only"
            if decision.suggested:
                record["suggested_target"] = redact(decision.suggested.target, self.secrets)
        self.audit.append(record)
        return record
