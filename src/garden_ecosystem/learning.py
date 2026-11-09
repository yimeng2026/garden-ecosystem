"""Non-executable learning proposals with evidence thresholds and rollback."""
from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from typing import Any

from .errors import LearningDisabled
from .security import redact


FORBIDDEN_KEYS = {"code", "command", "shell", "env", "tool", "config", "secret",
                  "credentials", "executable", "api_key"}


@dataclass(frozen=True)
class LearningEvidence:
    task: str
    date: str
    helped: bool = False
    harmed: bool = False
    control: bool = False

    def __post_init__(self) -> None:
        if not self.task or not self.date:
            raise ValueError("evidence requires task and date")
        if not all(isinstance(value, bool) for value in (self.helped, self.harmed, self.control)):
            raise ValueError("evidence flags must be boolean")
        # A mixed outcome is retained; harm takes precedence during activation.


@dataclass
class LearningCandidate:
    id: str
    text: str
    kind: str
    status: str = "tentative"
    evidence: list[LearningEvidence] = field(default_factory=list)
    history: list[dict[str, str]] = field(default_factory=list)


class LearningLedger:
    def __init__(self, enabled: bool = False, secrets: tuple[str, ...] = ()):
        self.enabled = enabled
        self.secrets = secrets
        self.candidates: dict[str, LearningCandidate] = {}

    def record(self, payload: dict[str, Any]) -> LearningCandidate:
        if not self.enabled:
            raise LearningDisabled("learning is disabled by default")
        if not isinstance(payload, dict):
            raise ValueError("learning candidate must be a dictionary")
        self._check_content(payload)
        text = payload.get("text")
        kind = payload.get("kind")
        if not isinstance(text, str) or not text.strip():
            raise ValueError("candidate text is required")
        if kind not in {"guideline", "proposal", "profile"}:
            raise ValueError("only explanatory guideline, proposal and profile are accepted")
        candidate = LearningCandidate(uuid.uuid4().hex, redact(text.strip(), self.secrets), kind)
        self.candidates[candidate.id] = candidate
        return candidate

    @classmethod
    def _check_content(cls, value: Any) -> None:
        if isinstance(value, dict):
            for key, item in value.items():
                if str(key).lower() in FORBIDDEN_KEYS or str(key).lower().endswith("_key"):
                    raise ValueError("executable or secret-bearing learning content is forbidden")
                cls._check_content(item)
        elif isinstance(value, (list, tuple)):
            for item in value:
                cls._check_content(item)
        json.dumps(value, allow_nan=False)

    @staticmethod
    def _transition(item: LearningCandidate, status: str, reason: str) -> None:
        if item.status != status:
            item.history.append({"from": item.status, "to": status, "reason": reason})
            item.status = status

    def evaluate(self, candidate_id: str, helped: bool, task: str, date: str,
                 harmed: bool = False, control: bool = False) -> LearningCandidate:
        item = self.candidates[candidate_id]
        evidence = LearningEvidence(task, date, helped, harmed, control)
        item.evidence.append(evidence)
        if harmed:
            self._transition(item, "tentative", "harm evidence blocks activation")
            return item
        independent = {(entry.task, entry.date) for entry in item.evidence if entry.helped}
        if len(independent) >= 2 and not any(entry.harmed for entry in item.evidence):
            self._transition(item, "active", "two independent help observations")
        return item

    def retire(self, candidate_id: str, reason: str) -> LearningCandidate:
        if not reason:
            raise ValueError("retirement requires a reason")
        item = self.candidates[candidate_id]
        self._transition(item, "retired", reason)
        return item

    def rollback(self, candidate_id: str) -> LearningCandidate:
        item = self.candidates[candidate_id]
        if not item.history:
            raise ValueError("candidate has no status transition to roll back")
        previous = item.history[-1]["from"]
        self._transition(item, previous, "manual rollback; evidence retained")
        return item

    def snapshot(self) -> dict[str, Any]:
        return {"enabled": self.enabled, "candidates": [
            {"id": item.id, "text": item.text, "kind": item.kind, "status": item.status,
             "evidence_count": len(item.evidence), "history": list(item.history)}
            for item in self.candidates.values()
        ]}
