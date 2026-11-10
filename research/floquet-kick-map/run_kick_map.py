"""Compute the fixed 45-point homogeneous kick map."""

import csv
import json
import platform
from pathlib import Path

import numpy as np
import scipy

from kick_map import evaluate_uniform, safe_endpoint_counts

ROOT = Path(__file__).resolve().parent
AMPLITUDES = [0.0, 0.025, 0.05, 0.075, 0.1, 0.125, 0.15, 0.175, 0.2, 0.22, np.pi / 14, 0.24, 0.25, 0.3]
LONG_CHAIN_AMPLITUDES = [0.05, 0.1, 0.2]
SIZES = [80, 160, 320, 640]


def contiguous_pass_islands(grid, n, target):
    rows = sorted((row for row in grid if row["n"] == n), key=lambda row: row["a"])
    islands = []
    current = []
    for row in rows:
        if row[target]["joint_pass"]:
            current.append(row)
        elif current:
            islands.append(current)
            current = []
        else:
            continue
    if current:
        islands.append(current)
    output = []
    for island in islands:
        output.append({
            "n": n,
            "target": target,
            "start": island[0]["a"],
            "end": island[-1]["a"],
            "a_values": [row["a"] for row in island],
            "endpoint_p0": sorted({row["endpoint"]["p0"] for row in island}, key=lambda value: -1 if value is None else value),
            "endpoint_p_pi": sorted({row["endpoint"]["p_pi"] for row in island}, key=lambda value: -1 if value is None else value),
            "selected_amplitudes_only": False,
            "interval_semantics": "grid_samples_not_a_precision_boundary",
        })
    return output


def main():
    grid = []
    profiles = {}
    for n in SIZES:
        amplitudes = LONG_CHAIN_AMPLITUDES if n == 640 else AMPLITUDES
        for a in amplitudes:
            observed = evaluate_uniform(n, a)
            row = {"n": n, "a": float(a), "endpoint": safe_endpoint_counts(a), "unitarity_error": observed["unitarity_error"]}
            for target in ("zero", "pi"):
                observation = observed[target]
                profiles[f"n{n}_a{a}_{target}"] = observation.pop("profile")
                row[target] = observation
            grid.append(row)
            print(f"N={n} a={a:.9f}: zero={row['zero']['joint_pass']}, pi={row['pi']['joint_pass']}, endpoint={row['endpoint']['status']}")

    islands = []
    for n in (80, 160, 320):
        for target in ("zero", "pi"):
            islands.extend(contiguous_pass_islands(grid, n, target))
    for target in ("zero", "pi"):
        for a in LONG_CHAIN_AMPLITUDES:
            row = next(row for row in grid if row["n"] == 640 and row["a"] == a)
            islands.append({
                "n": 640, "target": target, "start": a, "end": a, "a_values": [a],
                "endpoint_p0": [row["endpoint"]["p0"]], "endpoint_p_pi": [row["endpoint"]["p_pi"]],
                "selected_amplitudes_only": True,
                "interval_semantics": "selected_points_not_an_interval",
            })
    data = {
        "schema": "uniform-kick-parameter-map-v1",
        "date": "2026-11-11",
        "parameters": {"mu0": 2.5, "gamma": 1.0, "delta": 1.0, "omega": 7.0},
        "sizes": SIZES,
        "amplitudes": AMPLITUDES,
        "long_chain_amplitudes": LONG_CHAIN_AMPLITUDES,
        "analytic_singularities": [
            {"a": 0.0, "condition": "b_pi=2", "status": "gapless_or_undefined"},
            {"a": float(np.pi / 14), "condition": "b0=1", "status": "gapless_or_undefined"},
        ],
        "grid": grid,
        "pass_islands": islands,
        "environment": {"python": platform.python_version(), "numpy": np.__version__, "scipy": scipy.__version__},
        "scope": {
            "analytic_boundary_distinct_from_grid": True,
            "disorder_verdict_changed": False,
            "full_size_rule_status": "inconclusive_preserved",
            "disorder_winding_computed": False,
            "thermodynamic_limit_proof": False,
            "material_tc_prediction": False,
            "experimental_validation": False,
        },
    }
    (ROOT / "results.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    np.savez_compressed(ROOT / "profiles.npz", **profiles)
    with (ROOT / "uniform_grid.csv").open("w", newline="", encoding="utf-8") as stream:
        fields = ["n", "a", "target", "endpoint_status", "p0", "p_pi", "max_distance", "max_separation_ratio", "edge_weight", "subspace_ipr", "joint_pass"]
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for row in grid:
            for target in ("zero", "pi"):
                observation = row[target]
                writer.writerow({
                    "n": row["n"], "a": row["a"], "target": target, "endpoint_status": row["endpoint"]["status"],
                    "p0": row["endpoint"]["p0"], "p_pi": row["endpoint"]["p_pi"],
                    "max_distance": max(observation["distances"]), "max_separation_ratio": max(observation["separation_ratios"]),
                    "edge_weight": observation["edge_weight"], "subspace_ipr": observation["subspace_ipr"], "joint_pass": observation["joint_pass"],
                })
    print(json.dumps({"grid_count": len(grid), "pass_islands": islands}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
