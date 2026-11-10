"""Run the full preregistered chemical-kick disorder ensemble."""

import csv
import hashlib
import json
import platform
from pathlib import Path

import numpy as np
import scipy

from disorder_model import beta_sequence, disordered_floquet, observe_candidate
from convention_model import quasienergy_spectrum

ROOT = Path(__file__).resolve().parent
PARAMETERS = {"mu0": 2.5, "omega": 7.0, "gamma": 1.0, "delta": 1.0}
SIZES = [80, 160, 320]
STRENGTHS = [0.05, 0.1, 0.2]
SEED_COUNTS = {80: 16, 160: 16, 320: 4}


def evaluate(n, beta, strength):
    u, period = disordered_floquet(n, PARAMETERS["mu0"], beta, strength, PARAMETERS["omega"], PARAMETERS["gamma"], PARAMETERS["delta"])
    spectrum = quasienergy_spectrum(u, period)
    return u, {
        "unitarity_error": float(np.max(np.abs(u.T @ u - np.eye(2 * n)))),
        "zero": observe_candidate(spectrum, n, 1.0),
        "pi": observe_candidate(spectrum, n, -1.0),
    }


def summarize(realizations):
    rows = []
    for n in SIZES:
        for strength in STRENGTHS:
            for target in ("zero", "pi"):
                subset = [row[target] for row in realizations if row["n"] == n and row["strength"] == strength]
                pass_count = sum(row["joint_pass"] for row in subset)
                total = len(subset)
                rows.append({
                    "n": n,
                    "strength": strength,
                    "target": target,
                    "pass_count": pass_count,
                    "total": total,
                    "status": "full" if pass_count == total else "majority" if pass_count >= total - 1 else "not_supported",
                    "median_max_distance": float(np.median([max(row["distances"]) for row in subset])),
                    "worst_max_distance": float(max(max(row["distances"]) for row in subset)),
                    "median_edge_weight": float(np.median([row["edge_weight"] for row in subset])),
                    "minimum_edge_weight": float(min(row["edge_weight"] for row in subset)),
                    "median_subspace_ipr": float(np.median([row["subspace_ipr"] for row in subset])),
                    "median_second_pair_subspace_ipr": float(np.median([row["second_pair_subspace_ipr"] for row in subset])),
                })
    return rows


def main():
    realizations = []
    sequences = {}
    profiles = {}
    sequence_hashes = {}
    for n in SIZES:
        for seed in range(SEED_COUNTS[n]):
            beta = beta_sequence(seed, n)
            sequences[f"n{n}_seed{seed}"] = beta
            sequence_hashes[f"n{n}_seed{seed}"] = hashlib.sha256(beta.tobytes()).hexdigest()
    for n in SIZES:
        for seed in range(SEED_COUNTS[n]):
            beta = sequences[f"n{n}_seed{seed}"]
            for strength in STRENGTHS:
                _, observed = evaluate(n, beta, strength)
                row = {"n": n, "seed": seed, "strength": strength, "unitarity_error": observed["unitarity_error"]}
                for target in ("zero", "pi"):
                    observation = observed[target]
                    profile = observation.pop("profile")
                    profiles[f"n{n}_r{strength}_seed{seed}_{target}"] = profile
                    row[target] = observation
                realizations.append(row)
                print(f"N={n} seed={seed} r={strength}: zero_pass={row['zero']['joint_pass']}, pi_pass={row['pi']['joint_pass']}")

    clean = {}
    for n in SIZES:
        _, observed = evaluate(n, np.ones(n), 0.2)
        clean[str(n)] = observed
        for target in ("zero", "pi"):
            clean[str(n)][target].pop("profile")

    summary = summarize(realizations)
    main_rows = [row for row in summary if row["strength"] in (0.05, 0.1)]
    if all(row["status"] == "full" for row in main_rows):
        status = "supported"
    elif all(row["status"] in ("full", "majority") for row in main_rows):
        status = "partial"
    else:
        status = "not_supported"
    data = {
        "schema": "fock-checked-kicked-disorder-v1",
        "date": "2026-11-11",
        "parameters": PARAMETERS,
        "sizes": SIZES,
        "strengths": STRENGTHS,
        "seed_counts": {str(key): value for key, value in SEED_COUNTS.items()},
        "random_protocol": "default_rng(20261111+seed).random(320)[:N]; same beta across strengths and nested sizes",
        "sequence_hashes": sequence_hashes,
        "realizations": realizations,
        "clean_baseline": clean,
        "summary": summary,
        "assessment": {
            "status": status,
            "main_strengths": [0.05, 0.1],
            "stress_strength": 0.2,
            "rule": "supported: all main realizations pass; partial: at least 15/16 or 3/4 in each main combination; otherwise not_supported",
            "full_size_rule_status": "inconclusive_preserved",
        },
        "environment": {"python": platform.python_version(), "numpy": np.__version__, "scipy": scipy.__version__},
        "source": "Mondal et al., arXiv:2203.16353v3 Eq. (7), chemical-potential kick-only spatial disorder",
        "scope": {
            "all_realizations_retained": True,
            "disorder_winding_computed": False,
            "thermodynamic_limit_proof": False,
            "material_tc_prediction": False,
            "experimental_validation": False,
            "interactions": False,
            "dissipation": False,
        },
    }
    (ROOT / "results.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    np.savez_compressed(ROOT / "disorder_sequences.npz", **sequences)
    np.savez_compressed(ROOT / "profiles.npz", **profiles)
    with (ROOT / "realizations.csv").open("w", newline="", encoding="utf-8") as stream:
        fields = ["n", "seed", "strength", "target", "max_distance", "max_separation_ratio", "edge_weight", "subspace_ipr", "second_pair_subspace_ipr", "joint_pass"]
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for row in realizations:
            for target in ("zero", "pi"):
                observation = row[target]
                writer.writerow({
                    "n": row["n"], "seed": row["seed"], "strength": row["strength"], "target": target,
                    "max_distance": max(observation["distances"]), "max_separation_ratio": max(observation["separation_ratios"]),
                    "edge_weight": observation["edge_weight"], "subspace_ipr": observation["subspace_ipr"],
                    "second_pair_subspace_ipr": observation["second_pair_subspace_ipr"], "joint_pass": observation["joint_pass"],
                })
    print(json.dumps({"assessment": data["assessment"], "summary": summary}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
