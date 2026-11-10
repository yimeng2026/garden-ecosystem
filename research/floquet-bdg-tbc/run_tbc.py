"""Gated static and clean-kicked TBC dynamical-winding experiments."""

import datetime
import json
from pathlib import Path

import numpy as np

from tbc_model import winding_convergence

ROOT = Path(__file__).resolve().parent
WORKTREE = ROOT.parents[1]


def parameters(n, mu0, mu1, omega):
    return {
        "n": n,
        "mu0": np.full(n, mu0) if np.ndim(mu0) == 0 else np.asarray(mu0, dtype=float),
        "mu1": np.full(n, mu1) if np.ndim(mu1) == 0 else np.asarray(mu1, dtype=float),
        "omega": float(omega),
        "gamma": 1.0,
        "delta": 1.0,
    }


def evaluate_gaps(case_parameters, nominal_steps=(0.05, 0.025), keep_curve=False):
    return {
        "zero": winding_convergence(case_parameters, 0.0, nominal_steps, keep_curve),
        "pi": winding_convergence(case_parameters, np.pi, nominal_steps, keep_curve),
    }


def run_static(n=40, nominal_steps=(0.05, 0.025), keep_curve=True):
    topological = evaluate_gaps(parameters(n, 0.0, 0.0, 7.0), nominal_steps, keep_curve)
    trivial = evaluate_gaps(parameters(n, 2.5, 0.0, 17.0), nominal_steps, keep_curve)
    singular = winding_convergence(
        parameters(n, 2.5, 0.0, 7.0), 0.0, nominal_steps, keep_curve=False
    )
    passed = (
        topological["zero"]["nearest_integer"] == 1
        and topological["pi"]["nearest_integer"] == 0
        and trivial["zero"]["nearest_integer"] == 0
        and trivial["pi"]["nearest_integer"] == 0
        and all(row["status"] == "ok" for row in (*topological.values(), *trivial.values()))
        and singular["status"] == "gapless_or_undefined"
    )
    return {
        "n": n,
        "passed": passed,
        "topological_omega7": topological,
        "trivial_omega17": trivial,
        "trivial_omega7_zero_gap": singular,
    }


def run_clean(n=80, nominal_steps=(0.05, 0.025), keep_curve=True):
    reference_path = ROOT.parent / "floquet-bdg-convention" / "results.json"
    reference_data = json.loads(reference_path.read_text(encoding="utf-8"))
    reference = {
        key: int(reference_data["endpoint_invariants"][key]) for key in ("p0", "p_pi")
    }
    result = evaluate_gaps(parameters(n, 2.5, 0.2, 7.0), nominal_steps, keep_curve)
    passed = (
        result["zero"]["status"] == "ok"
        and result["pi"]["status"] == "ok"
        and result["zero"]["nearest_integer"] == reference["p0"]
        and result["pi"]["nearest_integer"] == reference["p_pi"]
    )
    return {
        "n": n,
        "mu0": 2.5,
        "mu1": 0.2,
        "omega": 7.0,
        "reference": reference,
        "reference_sha256": __import__("hashlib").sha256(reference_path.read_bytes()).hexdigest(),
        **result,
        "passed": passed,
    }


def concise(result):
    return {
        "status": result["status"],
        "value": result["value"],
        "nearest_integer": result["nearest_integer"],
        "min_bulk_gap": result["min_bulk_gap"],
        "mesh_difference": result["mesh_difference"],
        "integer_residual": result["integer_residual"],
    }


def main():
    static = run_static()
    data = {
        "schema": "floquet-bdg-tbc-dynamical-winding-v1",
        "recorded_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "method": {
            "basis": "(a1,b1,...,aN,bN), S=diag(-1,+1,...)",
            "periodization": "unitary Schur; phi_eff valence=2epsilon-|phi|, conduction=|phi|-2pi",
            "nominal_steps": [0.05, 0.025],
            "gap_tolerance": 1e-8,
            "condition_limit": 1e12,
            "integer_tolerance": 1e-3,
        },
        "static": static,
        "clean": None,
        "disorder": None,
    }
    if not static["passed"]:
        data["status"] = "static_baseline_failed"
    else:
        clean = run_clean()
        data["clean"] = clean
        data["status"] = "clean_floquet_baseline_passed" if clean["passed"] else "clean_floquet_baseline_failed"
    (ROOT / "results.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print("static_passed", static["passed"])
    for name in ("topological_omega7", "trivial_omega17"):
        print(name, "zero", concise(static[name]["zero"]))
        print(name, "pi", concise(static[name]["pi"]))
    print("trivial_omega7_zero", concise(static["trivial_omega7_zero_gap"]))
    if data["clean"] is not None:
        print("clean_zero", concise(data["clean"]["zero"]))
        print("clean_pi", concise(data["clean"]["pi"]))
        print("clean_reference", data["clean"]["reference"])
    print("status", data["status"])
    print("results", str(ROOT / "results.json"))
    return 0 if data["status"] == "clean_floquet_baseline_passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
