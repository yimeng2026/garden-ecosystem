"""Analyze original rank-two subspace profiles for recovery-scale evidence."""

import csv
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parent
SOURCE_DIR = ROOT.parent / "floquet-bdg-disorder"
sys.path.insert(0, str(ROOT.parent / "floquet-bdg-localization"))
from localization_analysis import fit_envelope  # noqa: E402
from scale_analysis import (  # noqa: E402
    assess_recovery,
    center_mass,
    coverage_lengths,
    fixed_width_masses,
)

REGISTRY = ((0.05, 0), (0.1, 0), (0.05, 2), (0.05, 3), (0.1, 2))
SIZES = (80, 160, 320)


def profile_key(n, strength, seed):
    return f"n{n}_r{strength}_seed{seed}_zero"


def analyze_all():
    archive_path = SOURCE_DIR / "profiles.npz"
    archive = np.load(archive_path)
    old = json.loads((SOURCE_DIR / "results.json").read_text(encoding="utf-8"))
    cases = []
    for strength, seed in REGISTRY:
        rows = []
        for n in SIZES:
            profile = np.asarray(archive[profile_key(n, strength, seed)], dtype=float)
            if profile.shape != (n,) or np.any(profile < 0) or not np.isclose(profile.sum(), 1.0, atol=1e-10):
                raise ValueError("invalid original subspace profile")
            original = next(row for row in old["realizations"] if row["n"] == n and row["strength"] == strength and row["seed"] == seed)
            observed = original["zero"]
            edge_sites = int(np.ceil(0.1 * n))
            computed_edge = float(profile[:edge_sites].sum() + profile[-edge_sites:].sum())
            if abs(computed_edge - observed["edge_weight"]) > 1e-10:
                raise ValueError("profile edge weight does not match original results")
            lengths = coverage_lengths(profile)
            masses = fixed_width_masses(profile)
            envelope = fit_envelope(profile)
            rows.append({
                "strength": strength, "seed": seed, "n": n,
                **lengths,
                "L50_fraction": lengths["L50"] / n,
                "mass5": masses["5"], "mass10": masses["10"], "mass20": masses["20"], "mass40": masses["40"],
                "center20_mass": center_mass(profile, fraction=0.2),
                "subspace_ipr": float(np.sum(profile**2)),
                "n_subspace_ipr": float(n * np.sum(profile**2)),
                "edge_weight": computed_edge,
                "separation": float(max(observed["separation_ratios"])),
                "joint_pass": bool(observed["joint_pass"]),
                "envelope": envelope,
                "profile_sha256": hashlib.sha256(profile.tobytes()).hexdigest(),
            })
        assessment = assess_recovery(rows)
        cases.append({"strength": strength, "seed": seed, "rows": rows, "assessment": assessment})
    return {
        "schema": "floquet-bdg-localization-recovery-scale-v1",
        "source_profiles_sha256": hashlib.sha256(archive_path.read_bytes()).hexdigest(),
        "source_results_sha256": hashlib.sha256((SOURCE_DIR / "results.json").read_bytes()).hexdigest(),
        "case_count": len(cases),
        "profile_count": sum(len(case["rows"]) for case in cases),
        "cases": cases,
        "scope": {
            "rank_two_subspace_profiles": True,
            "recovery_prediction": False,
            "n640_computation": False,
            "thermodynamic_limit_proof": False,
        },
    }


def write_csv(data):
    fields = [
        "strength", "seed", "n", "L50", "L90", "L99", "L50_fraction", "mass5", "mass10",
        "mass20", "mass40", "center20_mass", "subspace_ipr", "n_subspace_ipr", "edge_weight",
        "separation", "joint_pass", "xi_env", "r_squared", "background", "amplitude", "optimizer_success",
    ]
    with (ROOT / "localization_scale.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for case in data["cases"]:
            for row in case["rows"]:
                writer.writerow({
                    key: row["envelope"].get(key, row.get(key)) if key in ("xi_env", "r_squared", "background", "amplitude", "optimizer_success") else row.get(key)
                    for key in fields
                })


def main():
    data = analyze_all()
    (ROOT / "localization_scale.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_csv(data)
    for case in data["cases"]:
        assessment = case["assessment"]
        print(
            f"r={case['strength']} seed={case['seed']} status={assessment['status']} "
            f"next_size={assessment['next_size']} L50={[row['L50'] for row in case['rows']]} "
            f"L90={[row['L90'] for row in case['rows']]} "
            f"R2={[round(row['envelope']['r_squared'], 4) for row in case['rows']]}"
        )
    print("profiles", data["profile_count"], "cases", data["case_count"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
