"""Decompose stored disorder into exact mean drive and fluctuation outcomes."""

import csv
import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
import sys
sys.path.insert(0, str(ROOT.parent / "floquet-bdg-disorder"))
from disorder_model import beta_sequence  # noqa: E402

SOURCE = ROOT.parent / "floquet-bdg-disorder" / "results.json"
DATA = json.loads(SOURCE.read_text(encoding="utf-8"))
DISORDER = {(row["n"], row["seed"], row["strength"]): row for row in DATA["realizations"]}
UNIFORM = {(row["n"], row["seed"], row["strength"]): row for row in DATA["mean_matched"]}


def category(uniform_pass, disorder_pass):
    if uniform_pass and disorder_pass:
        return "both_pass"
    if uniform_pass and not disorder_pass:
        return "fluctuation_sensitive"
    if not uniform_pass and not disorder_pass:
        return "uniform_fails"
    return "fluctuation_assisted"


def decompose_realization(n, seed, strength, target):
    beta = beta_sequence(seed, n)
    disorder = DISORDER[(n, seed, strength)][target]
    uniform = UNIFORM[(n, seed, strength)][target]
    fluctuation = strength * (beta - beta.mean())
    return {
        "n": n,
        "seed": seed,
        "strength": strength,
        "target": target,
        "mean_beta": float(beta.mean()),
        "mean_amplitude": float(strength * beta.mean()),
        "fluctuation_rms": float(np.sqrt(np.mean(fluctuation**2))),
        "distance_delta": float(max(disorder["distances"]) - max(uniform["distances"])),
        "edge_delta": float(disorder["edge_weight"] - uniform["edge_weight"]),
        "subspace_ipr_delta": float(disorder["subspace_ipr"] - uniform["subspace_ipr"]),
        "uniform_joint_pass": uniform["joint_pass"],
        "disorder_joint_pass": disorder["joint_pass"],
        "category": category(uniform["joint_pass"], disorder["joint_pass"]),
    }


def main():
    rows = []
    for n in (80, 160, 320):
        for seed in range(16 if n < 320 else 4):
            for strength in (0.05, 0.1, 0.2):
                for target in ("zero", "pi"):
                    row = decompose_realization(n, seed, strength, target)
                    beta = beta_sequence(seed, n)
                    np.testing.assert_allclose(strength * beta, row["mean_amplitude"] + strength * (beta - beta.mean()), atol=1e-14)
                    rows.append(row)
    summary = []
    for n in (80, 160, 320):
        for strength in (0.05, 0.1, 0.2):
            for target in ("zero", "pi"):
                for name in ("both_pass", "fluctuation_sensitive", "uniform_fails", "fluctuation_assisted"):
                    subset = [row for row in rows if row["n"] == n and row["strength"] == strength and row["target"] == target and row["category"] == name]
                    if not subset:
                        continue
                    summary.append({
                        "n": n,
                        "strength": strength,
                        "target": target,
                        "category": name,
                        "count": len(subset),
                        "median_abs_distance_delta": float(np.median([abs(row["distance_delta"]) for row in subset])),
                        "median_abs_edge_delta": float(np.median([abs(row["edge_delta"]) for row in subset])),
                        "median_abs_subspace_ipr_delta": float(np.median([abs(row["subspace_ipr_delta"]) for row in subset])),
                        "outcome_change_count": sum(row["uniform_joint_pass"] != row["disorder_joint_pass"] for row in subset),
                    })
    data = {
        "schema": "disorder-mean-fluctuation-decomposition-v1",
        "date": "2026-11-11",
        "source_results_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "source_modified": False,
        "rows": rows,
        "summary": summary,
        "category_semantics": "Mechanical joint-rule outcomes only; not topological creation or destruction",
        "original_assessment": DATA["assessment"]["status"],
        "full_size_rule_status": "inconclusive_preserved",
        "scope": {
            "source_modified": False,
            "disorder_winding_computed": False,
            "thermodynamic_limit_proof": False,
            "material_tc_prediction": False,
            "experimental_validation": False,
        },
    }
    (ROOT / "sensitivity.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with (ROOT / "sensitivity.csv").open("w", newline="", encoding="utf-8") as stream:
        fields = ["n", "seed", "strength", "target", "mean_beta", "mean_amplitude", "fluctuation_rms", "distance_delta", "edge_delta", "subspace_ipr_delta", "uniform_joint_pass", "disorder_joint_pass", "category"]
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    print(json.dumps({"row_count": len(rows), "summary": summary}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
