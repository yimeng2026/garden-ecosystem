"""Run bounded N=400/N=600 diagnostic cases with resumable grids."""

import argparse
import json
from pathlib import Path

import numpy as np

from resumable_winding import resumable_winding
from run_disorder import beta_for, evaluate_realization, require_baseline
from tbc_model import winding_convergence_from_rows

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "scale_diagnostic.json"


def diagnostic_registry():
    return [
        {
            "n": 400, "strength": 0.1, "seed": 0, "kind": "disorder", "target": "zero",
            "rationale": "N=320 endpoint weight is just below 0.5; test threshold crossing, not recovery proof",
        },
        {
            "n": 600, "strength": 0.05, "seed": 0, "kind": "disorder", "target": "zero",
            "rationale": "L50 grows 21→31→51; test whether tail growth persists, with no recovery bracket",
        },
    ]


def write_atomic(data):
    temporary = OUTPUT.with_suffix(".tmp")
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(OUTPUT)


def load_state():
    if OUTPUT.exists():
        return json.loads(OUTPUT.read_text(encoding="utf-8"))
    return {
        "schema": "floquet-bdg-scale-diagnostic-v1", "rows": [],
        "partial_grids": {}, "n400_complete": False, "n600_complete": False, "complete": False,
    }


def run_diagnostic_case(n, grid, max_chunks=4):
    case = next(case for case in diagnostic_registry() if case["n"] == n)
    if n == 600:
        state = load_state()
        if not state["n400_complete"]:
            raise RuntimeError("N=400 diagnostic must complete before N=600")
    state = load_state()
    if any(row["n"] == n for row in state["rows"]):
        return state
    step = float(grid)
    if str(step) not in ("0.05", "0.025"):
        raise ValueError("grid must be 0.05 or 0.025")
    beta = beta_for(case["seed"], n)
    parameters = {
        "n": n, "mu0": np.full(n, 2.5), "mu1": case["strength"] * beta,
        "omega": 7.0, "gamma": 1.0, "delta": 1.0,
    }
    work_path = ROOT / "scale_work" / f"n{n}_zero_dtheta{str(step).replace('.', 'p')}.json"
    result = resumable_winding(
        parameters, step, 0.0, work_path, free_method="eigh",
        chunk_size=8, max_chunks=max_chunks,
    )
    partial = state["partial_grids"].setdefault(str(n), {})
    if result["status"] == "partial":
        partial[str(step)] = {
            "status": "partial", "next_index": result["next_index"], "points": result["points"],
            "work_path": str(work_path),
        }
        write_atomic(state)
        return state
    partial["last_completed_grid"] = str(step)
    partial.setdefault("grid_results", {})[str(step)] = result
    if len(partial["grid_results"]) == 2:
        aggregate = winding_convergence_from_rows(
            [partial["grid_results"]["0.05"], partial["grid_results"]["0.025"]],
            free_method="eigh", epsilon=0.0,
        )
        row = evaluate_realization(
            n, case["seed"], case["strength"], case["kind"], (0.05, 0.025),
            targets=("zero",), free_method="eigh", windings_override={"zero": aggregate},
        )
        row["rationale"] = case["rationale"]
        state["rows"].append(row)
        state[f"n{n}_complete"] = True
        state["complete"] = state["n400_complete"] and state["n600_complete"]
        state["partial_grids"].pop(str(n), None)
    write_atomic(state)
    return state


def merge_diagnostics(require_both=False):
    data = load_state()
    if require_both:
        if not data["complete"] or len(data["rows"]) != 2:
            raise ValueError("incomplete scale diagnostic registry")
    elif not data["n400_complete"] or not any(row["n"] == 400 for row in data["rows"]):
        raise ValueError("incomplete N400 diagnostic")
    return data


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, choices=(400, 600), required=True)
    parser.add_argument("--grid", choices=("0.05", "0.025"), required=True)
    parser.add_argument("--max-chunks", type=int, default=4)
    parser.add_argument("--merge-only", action="store_true")
    args = parser.parse_args()
    try:
        if args.merge_only:
            data = merge_diagnostics(require_both=False)
            print("n400_complete", data["n400_complete"], "n600_complete", data["n600_complete"], "rows", len(data["rows"]))
            return 0
        data = run_diagnostic_case(args.n, args.grid, args.max_chunks)
        for row in data["rows"]:
            print(
                f"N={row['n']} r={row['strength']} seed={row['seed']} status={row['zero']['status']} "
                f"W0={row['zero']['nearest_integer']} raw={row['zero']['value']} "
                f"gap={row['zero']['min_bulk_gap']} endpoint={row['endpoint']['zero']['joint_pass']}"
            )
        print("partial_grids", json.dumps(data["partial_grids"], ensure_ascii=False))
        print("n400_complete", data["n400_complete"], "n600_complete", data["n600_complete"])
        return 0
    except (RuntimeError, ValueError, FileNotFoundError) as error:
        print("scale_diagnostic_error", str(error))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
