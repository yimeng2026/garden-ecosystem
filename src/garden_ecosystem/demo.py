"""One deterministic offline demonstration; no real provider or solver is called."""
from __future__ import annotations

import json
from dataclasses import asdict

from .bridge import health
from .context import resolve_budget
from .errors import BudgetExceeded
from .evaluation import SharedWorld, aggregate, scenario_report
from .learning import LearningLedger
from .providers import FailureKind, ProviderError, ProviderPool, ProviderProfile
from .receipts import (
    CheckpointStore, RunManifest, UnavailableExternalTool, VerificationReceipt,
)
from .reliability import Action, Guard
from .security import stable_hash
from .worlds import MemoryWorld, PortableAgent, migrate


def run_demo() -> dict[str, object]:
    pool = ProviderPool([
        ProviderProfile("primary", "mock-primary", "PRIMARY_KEY", ("fallback",)),
        ProviderProfile("fallback", "mock-fallback", "FALLBACK_KEY"),
    ], {"PRIMARY_KEY": "offline-demo-key-not-a-secret", "FALLBACK_KEY": "offline-demo-key-not-a-secret"})

    def transport(profile, secret, request):
        if profile.name == "primary":
            raise ProviderError(FailureKind.RATE_LIMIT, "mock transient failure")
        return {"content": "offline mock result", "mock": True}

    provider_result = pool.call({}, transport)
    budget = resolve_budget([{"role": "user", "content": "offline demo"}],
                            "mock", window=100, configured=16, reserve=4)
    try:
        resolve_budget([], "mock", window=8, configured=4, tools=2, reserve=4, minimum=4)
        budget_rejected = False
    except BudgetExceeded:
        budget_rejected = True

    guard = Guard()
    guard_result = guard.execute(Action("demo", "write_file", "demo.md"),
                                 lambda _: {"unexpected": "must not execute"})
    source = MemoryWorld("source")
    target = MemoryWorld("target", reject={"demo-agent"})
    source.add(PortableAgent("demo-agent", {"role": "reviewer"}))
    migration = migrate(source, target, "demo-agent")
    scenario = scenario_report(lambda: SharedWorld(["reviewer", "observer"]), [1, 2],
                               {"reviewer": {"observe": {"state": "candidate"}, "message": "review"},
                                "observer": {"observe": {"state": "watching"}}})
    manifest = RunManifest.create("offline-demo", {"model": "mock", "api_key": "not-a-secret"},
                                  seed=7, clock=lambda: 1000)
    checkpoints = CheckpointStore(clock=lambda: 1000)
    checkpoint = checkpoints.append(manifest.run_id, None, {"tool": "read"}, {"ok": True})
    receipt = VerificationReceipt.machine_checked("mock-verifier", "0", stable_hash(checkpoint.hash), mock=True)
    external = UnavailableExternalTool("lean")
    checks = {
        "provider_failover": provider_result["mock"] is True,
        "budget_rejected": budget_rejected,
        "write_not_executed": not guard_result["executed"],
        "rollback_preserved_source": migration.status == "rolled_back" and "demo-agent" in source.agents,
        "scenario_not_prediction": scenario["prediction_probability"] is None,
    }
    return {
        "ok": all(checks.values()), "checks": checks, "mock": True, "offline": True,
        "provider": {"result": provider_result, "audit": pool.audit},
        "budget": asdict(budget), "budget_failure": {"rejected": budget_rejected, "type": "BudgetExceeded"},
        "guard": guard_result, "migration": asdict(migration), "scenario": scenario,
        "evaluation": aggregate([]), "learning": LearningLedger().snapshot(),
        "manifest": manifest.snapshot(), "checkpoint": asdict(checkpoint),
        "verification_receipt": asdict(receipt), "external_tool": asdict(external.health()),
        "health": health([external]),
    }


def main() -> int:
    print(json.dumps(run_demo(), ensure_ascii=False, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
