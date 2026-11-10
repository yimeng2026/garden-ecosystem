"""Preregistered N=80 TBC disorder and uniform-mean checkpoint runner."""

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / "floquet-bdg-convention"))
sys.path.insert(0, str(ROOT.parent / "floquet-bdg-disorder"))

from convention_model import quasienergy_spectrum  # noqa: E402
from disorder_model import beta_sequence, disordered_floquet, observe_candidate  # noqa: E402
from tbc_model import winding_convergence  # noqa: E402

STRENGTHS = (0.05, 0.1, 0.2)
SEEDS = (0, 1, 2, 3)


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def require_baseline(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if data.get("status") != "clean_floquet_baseline_passed" or not data.get("static", {}).get("passed"):
        raise RuntimeError("static and clean TBC baselines must pass before disorder promotion")
    return data


def beta_for(seed, n=80):
    return beta_sequence(seed, n)


def evaluate_realization(n, seed, strength, kind, nominal_steps):
    if kind not in ("disorder", "uniform_mean"):
        raise ValueError("kind must be disorder or uniform_mean")
    if strength not in STRENGTHS:
        raise ValueError("strength is outside the preregistered set")
    beta = beta_for(seed, n) if kind == "disorder" else np.ones(n)
    case = {
        "n": n,
        "mu0": np.full(n, 2.5),
        "mu1": 2 * strength * beta,
        "omega": 7.0,
        "gamma": 1.0,
        "delta": 1.0,
    }
    zero = winding_convergence(case, 0.0, nominal_steps, keep_curve=False)
    pi = winding_convergence(case, np.pi, nominal_steps, keep_curve=False)
    u, period = disordered_floquet(n, 2.5, beta, strength, 7.0, 1.0, 1.0)
    spectrum = quasienergy_spectrum(u, period)
    endpoint = {"zero": observe_candidate(spectrum, n, 1.0), "pi": observe_candidate(spectrum, n, -1.0)}
    for observation in endpoint.values():
        observation.pop("profile")
    return {
        "n": n,
        "seed": int(seed),
        "strength": float(strength),
        "kind": kind,
        "beta_sha256": sha256_bytes(beta.tobytes()),
        "full_kick_parameter": "2*r*beta",
        "zero": zero,
        "pi": pi,
        "endpoint": endpoint,
        "open_unitarity_error": float(np.max(np.abs(u.T @ u - np.eye(2 * n)))),
    }


def run_strength(strength, n=80, seeds=SEEDS, nominal_steps=(0.05, 0.025)):
    baseline_path = ROOT / "results.json"
    require_baseline(baseline_path)
    rows = []
    for seed in seeds:
        for kind in ("disorder", "uniform_mean"):
            rows.append(evaluate_realization(n, seed, strength, kind, nominal_steps))
    expected = {(seed, kind) for seed in seeds for kind in ("disorder", "uniform_mean")}
    complete = {(row["seed"], row["kind"]) for row in rows} == expected and len(rows) == 2 * len(seeds)
    return {
        "schema": "floquet-bdg-tbc-disorder-checkpoint-v1",
        "strength": float(strength),
        "n": n,
        "seeds": list(seeds),
        "nominal_steps": list(nominal_steps),
        "baseline_sha256": sha256_bytes(baseline_path.read_bytes()),
        "complete": complete,
        "rows": rows,
    }


def run_strength_incremental(
    strength,
    n=80,
    seeds=SEEDS,
    nominal_steps=(0.05, 0.025),
    path=None,
    expected_seeds=SEEDS,
):
    """Compute missing rows and atomically checkpoint after every seed."""
    baseline_path = ROOT / "results.json"
    require_baseline(baseline_path)
    path = checkpoint_path(strength) if path is None else Path(path)
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
        if (
            data.get("strength") != strength
            or data.get("n") != n
            or data.get("seeds") != list(expected_seeds)
            or data.get("nominal_steps") != list(nominal_steps)
        ):
            raise ValueError("checkpoint metadata does not match the requested ensemble")
    else:
        data = {
            "schema": "floquet-bdg-tbc-disorder-checkpoint-v1",
            "strength": float(strength),
            "n": n,
            "seeds": list(expected_seeds),
            "nominal_steps": list(nominal_steps),
            "baseline_sha256": sha256_bytes(baseline_path.read_bytes()),
            "complete": False,
            "rows": [],
        }
    rows = data["rows"]
    seen = {(row["seed"], row["kind"]) for row in rows}
    if len(seen) != len(rows):
        raise ValueError("duplicate realization in checkpoint")
    expected = {(seed, kind) for seed in expected_seeds for kind in ("disorder", "uniform_mean")}
    for seed in seeds:
        for kind in ("disorder", "uniform_mean"):
            if (seed, kind) not in seen:
                rows.append(evaluate_realization(n, seed, strength, kind, nominal_steps))
        rows.sort(key=lambda row: (row["seed"], row["kind"]))
        data["rows"] = rows
        data["complete"] = {(row["seed"], row["kind"]) for row in rows} == expected and len(rows) == 2 * len(expected_seeds)
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        temporary.replace(path)
    return data


def checkpoint_path(strength):
    tag = f"{strength:.2f}".replace(".", "p")
    return ROOT / f"disorder_r{tag}.json"


def summarize(rows):
    summary = []
    for strength in STRENGTHS:
        for kind in ("disorder", "uniform_mean"):
            for target in ("zero", "pi"):
                subset = [row for row in rows if row["strength"] == strength and row["kind"] == kind]
                values = [row[target]["value"] for row in subset if row[target]["value"] is not None]
                integers = [str(row[target]["nearest_integer"]) for row in subset]
                summary.append({
                    "strength": strength,
                    "kind": kind,
                    "target": target,
                    "total": len(subset),
                    "valid_winding_count": sum(row[target]["status"] == "ok" for row in subset),
                    "undefined_count": sum(row[target]["status"] == "gapless_or_undefined" for row in subset),
                    "not_converged_count": sum(row[target]["status"] == "not_converged" for row in subset),
                    "nearest_integer_frequencies": dict(Counter(integers)),
                    "median_raw_value": float(np.median(values)) if values else None,
                    "minimum_bulk_gap": min(row[target]["min_bulk_gap"] for row in subset),
                    "endpoint_joint_pass_count": sum(row["endpoint"][target]["joint_pass"] for row in subset),
                })
    return summary


def paired_comparisons(rows):
    comparisons = []
    for strength in STRENGTHS:
        for seed in SEEDS:
            disorder = next(row for row in rows if row["strength"] == strength and row["seed"] == seed and row["kind"] == "disorder")
            control = next(row for row in rows if row["strength"] == strength and row["seed"] == seed and row["kind"] == "uniform_mean")
            for target in ("zero", "pi"):
                both_valid = disorder[target]["status"] == "ok" and control[target]["status"] == "ok"
                comparisons.append({
                    "strength": strength,
                    "seed": seed,
                    "target": target,
                    "both_valid": both_valid,
                    "disorder_integer": disorder[target]["nearest_integer"],
                    "uniform_mean_integer": control[target]["nearest_integer"],
                    "integer_agreement": disorder[target]["nearest_integer"] == control[target]["nearest_integer"] if both_valid else None,
                })
    return comparisons


def merge_checkpoints(paths):
    expected_paths = {checkpoint_path(strength) for strength in STRENGTHS}
    if len(paths) != 3 or set(paths) != expected_paths or not all(path.exists() for path in paths):
        raise ValueError("incomplete preregistered disorder checkpoints")
    checkpoints = [json.loads(path.read_text(encoding="utf-8")) for path in paths]
    rows = []
    for strength, data in zip(STRENGTHS, checkpoints):
        expected = {(seed, kind) for seed in SEEDS for kind in ("disorder", "uniform_mean")}
        if (
            not data.get("complete")
            or data.get("strength") != strength
            or data.get("n") != 80
            or len(data.get("rows", [])) != 8
            or {(row["seed"], row["kind"]) for row in data["rows"]} != expected
        ):
            raise ValueError("incomplete preregistered disorder checkpoints")
        rows.extend(data["rows"])
    rows.sort(key=lambda row: (row["strength"], row["seed"], row["kind"]))
    baseline_hashes = sorted({data["baseline_sha256"] for data in checkpoints})
    return {
        "schema": "floquet-bdg-tbc-disorder-ensemble-v1",
        "status": "complete_raw_results",
        "complete": True,
        "n": 80,
        "strengths": list(STRENGTHS),
        "seeds": list(SEEDS),
        "random_protocol": "default_rng(20261111+seed).random(320)[:80]",
        "full_kick_parameter": "2*r*beta; uniform control uses 2*r*ones",
        "baseline_sha256": baseline_hashes,
        "checkpoint_sha256": {path.name: sha256_bytes(path.read_bytes()) for path in paths},
        "realizations": rows,
        "summary": summarize(rows),
        "paired_comparisons": paired_comparisons(rows),
        "scope": {
            "all_24_realizations_retained": True,
            "all_failures_retained": True,
            "majority_vote_is_topological_proof": False,
            "thermodynamic_limit_proof": False,
            "interactions_or_dissipation": False,
            "material_tc_or_experiment": False,
        },
    }


def write_csv(data, path):
    fields = [
        "n", "seed", "strength", "kind", "target", "winding_status", "winding_value",
        "nearest_integer", "min_bulk_gap", "max_block_condition", "mesh_difference",
        "integer_residual", "endpoint_joint_pass", "endpoint_max_distance",
        "endpoint_max_separation_ratio", "edge_weight", "subspace_ipr", "second_pair_subspace_ipr",
    ]
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for row in data["realizations"]:
            for target in ("zero", "pi"):
                winding, endpoint = row[target], row["endpoint"][target]
                writer.writerow({
                    "n": row["n"], "seed": row["seed"], "strength": row["strength"],
                    "kind": row["kind"], "target": target,
                    "winding_status": winding["status"], "winding_value": winding["value"],
                    "nearest_integer": winding["nearest_integer"], "min_bulk_gap": winding["min_bulk_gap"],
                    "max_block_condition": max(item.get("max_block_condition", np.nan) for item in winding["rows"]),
                    "mesh_difference": winding["mesh_difference"], "integer_residual": winding["integer_residual"],
                    "endpoint_joint_pass": endpoint["joint_pass"],
                    "endpoint_max_distance": max(endpoint["distances"]),
                    "endpoint_max_separation_ratio": max(endpoint["separation_ratios"]),
                    "edge_weight": endpoint["edge_weight"], "subspace_ipr": endpoint["subspace_ipr"],
                    "second_pair_subspace_ipr": endpoint["second_pair_subspace_ipr"],
                })


def merge_and_write():
    data = merge_checkpoints([checkpoint_path(strength) for strength in STRENGTHS])
    (ROOT / "disorder_results.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_csv(data, ROOT / "disorder_results.csv")
    return data


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--strength", type=float, choices=STRENGTHS)
    parser.add_argument("--seed", type=int, choices=SEEDS)
    parser.add_argument("--merge-only", action="store_true")
    args = parser.parse_args()
    try:
        if args.merge_only:
            data = merge_and_write()
            print("merged_realizations", len(data["realizations"]))
            print("summary", json.dumps(data["summary"], ensure_ascii=False))
            return 0
        strengths = (args.strength,) if args.strength is not None else STRENGTHS
        seeds = (args.seed,) if args.seed is not None else SEEDS
        for strength in strengths:
            data = run_strength_incremental(strength, seeds=seeds)
            path = checkpoint_path(strength)
            for row in data["rows"]:
                print(
                    f"N={row['n']} seed={row['seed']} r={row['strength']} kind={row['kind']} "
                    f"W0={row['zero']['nearest_integer']} Wpi={row['pi']['nearest_integer']} "
                    f"status0={row['zero']['status']} statuspi={row['pi']['status']}"
                )
            print("checkpoint", str(path), "rows", len(data["rows"]), "complete", data["complete"])
        return 0
    except (RuntimeError, ValueError, FileNotFoundError) as error:
        print("disorder_error", str(error))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
