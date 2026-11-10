"""Run finite-size localization analysis using only the Fock-corrected model."""

import csv
import hashlib
import json
import platform
import sys
from pathlib import Path

import numpy as np
import scipy

ROOT = Path(__file__).resolve().parent
CONVENTION = ROOT.parent / "floquet-bdg-convention"
sys.path.insert(0, str(CONVENTION))
from convention_model import candidate_modes, kicked_floquet, quasienergy_spectrum, site_weights  # noqa: E402
from localization_analysis import assess_short_chain, fit_envelope, subspace_metrics, tail_deficit_lengths  # noqa: E402

PARAMETERS = {"mu0": 2.5, "mu1": 0.2, "omega": 7.0, "gamma": 1.0, "delta": 1.0}
SIZES = [40, 80, 160, 320, 640]


def target_study(spectrum, n, target):
    candidate = candidate_modes(spectrum, n, target)
    indices = candidate["indices"]
    weights = site_weights(spectrum["eigenvectors"], n)
    probability = np.abs(spectrum["eigenvectors"]) ** 2
    distances = np.abs(spectrum["eigenvalues"] - target)
    second_indices = np.argsort(distances)[2:4]
    metrics = subspace_metrics(spectrum["eigenvectors"][:, indices], n)
    second_metrics = subspace_metrics(spectrum["eigenvectors"][:, second_indices], n)
    profile = metrics["profile"]
    edge_sites = max(1, int(np.ceil(0.1 * n)))
    edge_indices = np.r_[np.arange(edge_sites), np.arange(n - edge_sites, n)]
    edge_weight = float(profile[edge_indices].sum())
    return {
        "distances": [float(value) for value in candidate["distances"]],
        "separation_ratios": [float(value) for value in candidate["separation_ratios"]],
        "edge_weights": [edge_weight, edge_weight],
        "ipr": float(np.mean((probability[:, indices] ** 2).sum(axis=0))),
        "subspace_ipr": metrics["subspace_ipr"],
        "second_pair_ipr": float(np.mean((probability[:, second_indices] ** 2).sum(axis=0))),
        "second_pair_subspace_ipr": second_metrics["subspace_ipr"],
        "second_pair_max_distance": float(np.max(distances[second_indices])),
        "second_pair_min_edge_weight": float(np.min(weights[edge_indices][:, second_indices].sum(axis=0))),
        "profile": [float(value) for value in profile],
    }


def main():
    studies = []
    profiles = {}
    for n in SIZES:
        u, period = kicked_floquet(n, **PARAMETERS)
        spectrum = quasienergy_spectrum(u, period)
        row = {
            "n": n,
            "unitarity_error": float(np.max(np.abs(u.T @ u - np.eye(2 * n)))),
            "zero": target_study(spectrum, n, 1.0),
            "pi": target_study(spectrum, n, -1.0),
        }
        studies.append(row)
        profiles[f"n{n}_zero"] = np.array(row["zero"]["profile"])
        profiles[f"n{n}_pi"] = np.array(row["pi"]["profile"])
        print(f"N={n}: zero edge={row['zero']['edge_weights'][0]:.8f}, pi edge={row['pi']['edge_weights'][0]:.8f}, IPR=({row['zero']['ipr']:.8f},{row['pi']['ipr']:.8f})")

    tail_rows = {
        target: tail_deficit_lengths(SIZES, [study[target]["edge_weights"][0] for study in studies])
        for target in ("zero", "pi")
    }
    envelope_rows = {
        target: [fit_envelope(study[target]["profile"]) for study in studies]
        for target in ("zero", "pi")
    }
    data = {
        "schema": "fock-checked-floquet-localization-v1",
        "date": "2026-11-11",
        "parameters": PARAMETERS,
        "sizes": SIZES,
        "size_studies": studies,
        "tail_estimates": tail_rows,
        "envelope_fits": envelope_rows,
        "assessment": assess_short_chain(studies, tail_rows, envelope_rows),
        "convention_results_sha256": hashlib.sha256((CONVENTION / "results.json").read_bytes()).hexdigest(),
        "environment": {"python": platform.python_version(), "numpy": np.__version__, "scipy": scipy.__version__},
        "scope": {
            "fock_corrected_model": True,
            "full_size_rule_status_changed": False,
            "thermodynamic_limit_proof": False,
            "material_tc_prediction": False,
            "experimental_validation": False,
            "interactions": False,
            "dissipation": False,
        },
    }
    (ROOT / "results.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    np.savez_compressed(ROOT / "profiles.npz", **profiles)
    with (ROOT / "localization.csv").open("w", newline="", encoding="utf-8") as stream:
        fields = ["n", "target", "max_distance", "min_edge_weight", "ipr", "subspace_ipr", "second_pair_ipr", "second_pair_subspace_ipr", "second_pair_max_distance", "xi_env", "envelope_r_squared"]
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for index, study in enumerate(studies):
            for target in ("zero", "pi"):
                row = study[target]
                fit = envelope_rows[target][index]
                writer.writerow({
                    "n": study["n"], "target": target, "max_distance": max(row["distances"]), "min_edge_weight": min(row["edge_weights"]),
                    "ipr": row["ipr"], "subspace_ipr": row["subspace_ipr"], "second_pair_ipr": row["second_pair_ipr"],
                    "second_pair_subspace_ipr": row["second_pair_subspace_ipr"], "second_pair_max_distance": row["second_pair_max_distance"],
                    "xi_env": fit["xi_env"], "envelope_r_squared": fit["r_squared"],
                })
    print(json.dumps({"tail_estimates": tail_rows, "envelope_fits": envelope_rows, "assessment": data["assessment"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
