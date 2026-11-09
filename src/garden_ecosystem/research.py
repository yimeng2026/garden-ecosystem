"""Preregistration, parameter provenance and retained negative results."""
from __future__ import annotations

import copy
import json
from dataclasses import asdict, dataclass
from types import MappingProxyType
from typing import Any, Mapping

from .errors import GardenError
from .security import stable_hash


ORIGINS = {"endogenous", "calibrated", "estimated", "untested"}


@dataclass(frozen=True)
class ParameterRecord:
    name: str
    origin: str
    physical_meaning: str

    def __post_init__(self) -> None:
        if not self.name or self.origin not in ORIGINS or not self.physical_meaning:
            raise ValueError("parameter name, known origin and physical meaning are required")


@dataclass(frozen=True)
class NegativeResult:
    candidate: str
    reason: str
    evidence: str

    def __post_init__(self) -> None:
        if not self.candidate or not self.reason or not self.evidence:
            raise ValueError("candidate, exclusion reason and evidence reference are required")


class PreregistrationError(GardenError):
    pass


class Preregistration:
    def __init__(self, payload: Mapping[str, Any]):
        self._draft = copy.deepcopy(dict(payload))
        json.dumps(self._draft, allow_nan=False)
        self._frozen: MappingProxyType[str, Any] | None = None
        self._frozen_hash: str | None = None
        self._observations: list[dict[str, Any]] = []
        self._negative_results: list[NegativeResult] = []

    @property
    def payload(self) -> dict[str, Any]:
        source = self._frozen if self._frozen is not None else self._draft
        return copy.deepcopy(dict(source))

    @property
    def frozen_hash(self) -> str | None:
        return self._frozen_hash

    @property
    def observations(self) -> list[dict[str, Any]]:
        return copy.deepcopy(self._observations)

    def freeze(self) -> str:
        if self._frozen_hash is None:
            self._frozen_hash = stable_hash(self._draft)
            self._frozen = MappingProxyType(copy.deepcopy(self._draft))
        return self._frozen_hash

    def append_observation(self, observation: Mapping[str, Any]) -> None:
        if self._frozen is None:
            raise PreregistrationError("freeze the hypothesis before recording observations")
        saved = copy.deepcopy(dict(observation))
        json.dumps(saved, allow_nan=False)
        self._observations.append(saved)

    def negative_result(self, candidate: str, reason: str, evidence: str) -> NegativeResult:
        result = NegativeResult(candidate, reason, evidence)
        self._negative_results.append(result)
        return result

    def snapshot(self) -> dict[str, Any]:
        return {"payload": self.payload if self._frozen is not None else None,
                "frozen_hash": self._frozen_hash,
                "observations": self.observations,
                "negative_results": [asdict(result) for result in self._negative_results]}
