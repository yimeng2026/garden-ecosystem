"""Add mean-kick-matched and zero-kick controls without changing the ensemble verdict."""

import csv
import json
from pathlib import Path

import numpy as np

from run_disorder import PARAMETERS, SEED_COUNTS, SIZES, STRENGTHS, evaluate, summarize

ROOT = Path(__file__).resolve().parent


def strip_profiles(observed):
    for target in ("zero", "pi"):
        observed[target].pop("profile")
    return observed


def main():
    path = ROOT / "results.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    sequences = np.load(ROOT / "disorder_sequences.npz")
    controls = []
    for n in SIZES:
        for seed in range(SEED_COUNTS[n]):
            beta = sequences[f"n{n}_seed{seed}"]
            for strength in STRENGTHS:
                _, observed = evaluate(n, np.full(n, beta.mean()), strength)
                row = {"n": n, "seed": seed, "strength": strength, "unitarity_error": observed["unitarity_error"]}
                for target in ("zero", "pi"):
                    row[target] = observed[target]
                    row[target].pop("profile")
                controls.append(row)
        print(f"mean-matched controls completed: N={n}")

    zero_reference = {}
    for n in SIZES:
        _, observed = evaluate(n, np.zeros(n), 0.0)
        zero_reference[str(n)] = strip_profiles(observed)

    mean_summary = summarize(controls)
    comparisons = []
    for n in SIZES:
        for strength in STRENGTHS:
            for target in ("zero", "pi"):
                disordered = [row for row in data["realizations"] if row["n"] == n and row["strength"] == strength]
                uniform = [row for row in controls if row["n"] == n and row["strength"] == strength]
                disordered.sort(key=lambda row: row["seed"])
                uniform.sort(key=lambda row: row["seed"])
                agreement = sum(d[target]["joint_pass"] == u[target]["joint_pass"] for d, u in zip(disordered, uniform))
                comparisons.append({
                    "n": n,
                    "strength": strength,
                    "target": target,
                    "disorder_pass_count": sum(row[target]["joint_pass"] for row in disordered),
                    "uniform_mean_pass_count": sum(row[target]["joint_pass"] for row in uniform),
                    "outcome_agreement_count": agreement,
                    "total": len(disordered),
                    "median_disorder_edge_weight": float(np.median([row[target]["edge_weight"] for row in disordered])),
                    "median_uniform_edge_weight": float(np.median([row[target]["edge_weight"] for row in uniform])),
                    "median_disorder_subspace_ipr": float(np.median([row[target]["subspace_ipr"] for row in disordered])),
                    "median_uniform_subspace_ipr": float(np.median([row[target]["subspace_ipr"] for row in uniform])),
                })
    data["mean_matched"] = controls
    data["mean_matched_summary"] = mean_summary
    data["zero_kick_reference"] = zero_reference
    data["comparisons"] = comparisons
    data["mean_control"] = {
        "protocol": "uniform a_n=r*mean(beta) for each realization; same free evolution and period",
        "original_assessment_unchanged": True,
        "interpretation_boundary": "Failure in both disordered and uniform chains cannot be attributed to spatial disorder alone.",
    }
    data["scope"]["mean_matched_control_included"] = True
    data["scope"]["zero_kick_reference_included"] = True
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    with (ROOT / "mean_matched.csv").open("w", newline="", encoding="utf-8") as stream:
        fields = ["n", "seed", "strength", "target", "max_distance", "max_separation_ratio", "edge_weight", "subspace_ipr", "second_pair_subspace_ipr", "joint_pass"]
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for row in controls:
            for target in ("zero", "pi"):
                observation = row[target]
                writer.writerow({
                    "n": row["n"], "seed": row["seed"], "strength": row["strength"], "target": target,
                    "max_distance": max(observation["distances"]), "max_separation_ratio": max(observation["separation_ratios"]),
                    "edge_weight": observation["edge_weight"], "subspace_ipr": observation["subspace_ipr"],
                    "second_pair_subspace_ipr": observation["second_pair_subspace_ipr"], "joint_pass": observation["joint_pass"],
                })
    print(json.dumps({"assessment": data["assessment"], "comparisons": comparisons}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
