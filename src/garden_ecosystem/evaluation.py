"""Structured domain evaluation and reproducible multi-agent scenario reports."""
from __future__ import annotations

import copy
import math
import statistics
from collections import defaultdict
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from enum import Enum
from typing import Any

from .security import stable_hash


class Domain(str, Enum):
    MCP = "mcp"
    SEARCH = "search"
    TERMINAL = "terminal"
    SWE = "swe"
    ANDROID = "android"
    WEB = "web"
    OS = "os"


DIMENSIONS = ("format", "factuality", "consistency", "realism", "quality")


@dataclass(frozen=True)
class EvaluationItem:
    domain: Domain
    reference: str
    prediction: str
    scores: Mapping[str, float]

    def __post_init__(self) -> None:
        object.__setattr__(self, "domain", Domain(self.domain))
        if not isinstance(self.reference, str) or not isinstance(self.prediction, str):
            raise ValueError("reference and prediction must be strings")
        for dimension in DIMENSIONS:
            value = self.scores.get(dimension)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                raise ValueError(f"invalid score: {dimension}")
            if not 0 <= value <= 100:
                raise ValueError(f"score out of range: {dimension}")


def _means(items: list[EvaluationItem]) -> dict[str, Any]:
    dimensions = {dimension: statistics.fmean(item.scores[dimension] for item in items)
                  for dimension in DIMENSIONS}
    return {"count": len(items), "by_dimension": dimensions,
            "overall": statistics.fmean(dimensions.values())}


def aggregate(items: Iterable[EvaluationItem]) -> dict[str, Any]:
    groups: dict[str, list[EvaluationItem]] = defaultdict(list)
    for item in items:
        groups[item.domain.value].append(item)
    domains = {name: _means(group) for name, group in sorted(groups.items())}
    macro = None
    if domains:
        by_dimension = {dimension: statistics.fmean(report["by_dimension"][dimension]
                                                   for report in domains.values())
                        for dimension in DIMENSIONS}
        macro = {"by_dimension": by_dimension, "overall": statistics.fmean(by_dimension.values())}
    return {"domains": domains, "macro_average": macro,
            "count": sum(report["count"] for report in domains.values()),
            "method": "macro average of per-domain means; not a global capability claim"}


class SharedWorld:
    """Small deterministic reference model, not a neural world model."""

    def __init__(self, agent_ids: Iterable[str]):
        ids = tuple(sorted(set(agent_ids)))
        if not ids or any(not agent_id for agent_id in ids):
            raise ValueError("at least one non-empty agent_id is required")
        self.agent_ids = ids
        self.observations = {agent_id: {} for agent_id in ids}
        self.hub: list[dict[str, Any]] = []
        self.version = 0

    def step(self, actions: Mapping[str, Mapping[str, Any]], seed: int = 0) -> dict[str, Any]:
        if isinstance(seed, bool) or not isinstance(seed, int):
            raise ValueError("seed must be an integer")
        unknown = set(actions) - set(self.agent_ids)
        if unknown:
            raise ValueError(f"unknown agents: {sorted(unknown)}")
        version = self.version + 1
        observations = copy.deepcopy(self.observations)
        messages = []
        for agent_id in sorted(actions):
            action = actions[agent_id]
            observed = action.get("observe", {})
            if not isinstance(observed, dict):
                raise ValueError("observe must be a dictionary")
            observations[agent_id] = copy.deepcopy(observed)
            if "message" in action:
                if not isinstance(action["message"], str):
                    raise ValueError("message must be text")
                messages.append({"from": agent_id, "text": action["message"], "version": version})
        hub = self.hub + messages
        state_hash = stable_hash({"seed": seed, "version": version,
                                  "observations": observations, "hub": hub})
        self.observations = observations
        self.hub = hub
        self.version = version
        return {"version": version, "observations": copy.deepcopy(observations),
                "messages": messages, "state_hash": state_hash}


def scenario_report(factory: Callable[[], SharedWorld], seeds: Iterable[int],
                    actions: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    seed_list = list(seeds)
    if len(set(seed_list)) != len(seed_list):
        raise ValueError("duplicate seeds would double-count a scenario")
    scenarios = []
    for seed in seed_list:
        result = factory().step(actions, seed=seed)
        scenarios.append({"seed": seed, "version": result["version"], "state_hash": result["state_hash"]})
    return {"scenario_count": len(scenarios), "scenarios": scenarios,
            "prediction_probability": None,
            "notice": "deterministic scenarios, not real-world probabilities or experimental validation"}
