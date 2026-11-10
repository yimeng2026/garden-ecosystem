"""Run corrected Bloch and open-chain Floquet diagnostics without altering legacy evidence."""

import csv
import hashlib
import json
import platform
from pathlib import Path

import numpy as np
import scipy

from bloch_topology import bloch_floquet, effective_vector, endpoint_counts, logm_direction, winding_convergence
from convention_model import candidate_modes, kicked_floquet, quasienergy_spectrum, site_weights

ROOT = Path(__file__).resolve().parent
PARAMETERS = {"mu0": 2.5, "mu1": 0.2, "omega": 7.0, "gamma": 1.0, "delta": 1.0}
LEGACY_RESULTS = ROOT.parent / "floquet-bdg" / "results.json"


def candidate_record(candidate, spectrum):
    indices = candidate["indices"]
    return {
        "indices": indices,
        "eigenvalues_real": [float(spectrum["eigenvalues"][i].real) for i in indices],
        "eigenvalues_imag": [float(spectrum["eigenvalues"][i].imag) for i in indices],
        "distances": [float(value) for value in candidate["distances"]],
        "bulk_distance": candidate["bulk_distance"],
        "separation_ratios": [float(value) for value in candidate["separation_ratios"]],
        "edge_weights": [float(value) for value in candidate["edge_weights"]],
        "left_weights": [float(value) for value in candidate["left_weights"]],
        "right_weights": [float(value) for value in candidate["right_weights"]],
        "localized": [bool(value) for value in candidate["localized"]],
        "separated": [bool(value) for value in candidate["separated"]],
    }


def nearest_pairs(spectrum, n, target, pair_count=4):
    distances = np.abs(spectrum["eigenvalues"] - target)
    order = np.argsort(distances)[: 2 * pair_count]
    weights = site_weights(spectrum["eigenvectors"], n)
    edge_sites = max(1, int(np.ceil(0.1 * n)))
    edge_indices = np.r_[np.arange(edge_sites), np.arange(n - edge_sites, n)]
    pairs = []
    for rank in range(pair_count):
        indices = order[2 * rank : 2 * rank + 2]
        values = spectrum["eigenvalues"][indices]
        conjugate_error = float(min(np.max(np.abs(values[0] - values[1].conj())), np.max(np.abs(values[0] - values[1]))))
        probability = np.abs(spectrum["eigenvectors"][:, indices]) ** 2
        pairs.append({
            "rank": rank,
            "indices": [int(i) for i in indices],
            "eigenvalues_real": [float(value.real) for value in values],
            "eigenvalues_imag": [float(value.imag) for value in values],
            "distances": [float(value) for value in distances[indices]],
            "max_distance": float(np.max(distances[indices])),
            "conjugate_or_degenerate_error": conjugate_error,
            "edge_weights": [float(value) for value in weights[edge_indices][:, indices].sum(axis=0)],
            "left_weights": [float(value) for value in weights[:edge_sites][:, indices].sum(axis=0)],
            "right_weights": [float(value) for value in weights[n - edge_sites :][:, indices].sum(axis=0)],
            "ipr": [float(value) for value in (probability**2).sum(axis=0)],
        })
    return pairs


def open_chain(n, parameters):
    u, period = kicked_floquet(n, **parameters)
    spectrum = quasienergy_spectrum(u, period)
    return {
        "n": n,
        "unitarity_error": float(np.max(np.abs(u.T @ u - np.eye(2 * n)))),
        "zero": candidate_record(candidate_modes(spectrum, n, 1.0), spectrum),
        "pi": candidate_record(candidate_modes(spectrum, n, -1.0), spectrum),
        "zero_nearest_pairs": nearest_pairs(spectrum, n, 1.0),
        "pi_nearest_pairs": nearest_pairs(spectrum, n, -1.0),
    }, spectrum


def convergence(studies, target):
    distances = [max(study[target]["distances"]) for study in studies]
    reduction = distances[0] / distances[-1] if distances[-1] else float("inf")
    decreasing = all(left > right for left, right in zip(distances, distances[1:]))
    separated = all(all(study[target]["separated"]) for study in studies)
    localized = all(all(study[target]["localized"]) for study in studies)
    return {
        "max_candidate_distances_by_size": distances,
        "strictly_decreasing": decreasing,
        "first_to_last_reduction_factor": reduction,
        "all_candidates_separated": separated,
        "all_candidates_localized": localized,
        "finite_size_status": "supported_finite_size" if decreasing and reduction >= 2 and separated and localized else "inconclusive",
        "thermodynamic_limit_proof": False,
    }


def main():
    grid_sizes = [512, 1024, 2048, 4096]
    winding_rows = []
    curves = {}
    for row in winding_convergence(PARAMETERS, grid_sizes):
        winding_rows.append({key: value for key, value in row.items() if key not in ("k_values", "alpha_unwrapped", "n_y", "n_z")})
        if row["nk"] == 4096:
            curves = {key: row[key] for key in ("k_values", "alpha_unwrapped", "n_y", "n_z")}
    controls = {}
    for name, parameters in {
        "static_trivial_omega17": dict(PARAMETERS, mu1=0.0, omega=17.0),
        "static_topological_mu0": dict(PARAMETERS, mu0=0.0, mu1=0.0),
    }.items():
        row = winding_convergence(parameters, [2048])[0]
        controls[name] = {key: value for key, value in row.items() if key not in ("k_values", "alpha_unwrapped", "n_y", "n_z")}
    log_checks = []
    for k in (-0.731, 0.217, 1.13):
        vector = effective_vector(bloch_floquet(k, **PARAMETERS))
        logged = logm_direction(bloch_floquet(k, **PARAMETERS))
        log_checks.append({"k": k, "direction_dot": vector["n_y"] * logged["n_y"] + vector["n_z"] * logged["n_z"]})

    sizes = [40, 80, 160]
    studies = []
    spectra = {}
    while True:
        for n in sizes[len(studies) :]:
            study, spectrum = open_chain(n, PARAMETERS)
            studies.append(study)
            spectra[n] = spectrum
            print(f"N={n}: zero={study['zero']['distances']}/{study['zero']['separation_ratios']}, pi={study['pi']['distances']}/{study['pi']['separation_ratios']}")
        latest = studies[-1]
        needs_extension = any(
            max(latest[target]["separation_ratios"]) >= 0.1 or min(latest[target]["edge_weights"]) <= 0.5
            for target in ("zero", "pi")
        )
        if needs_extension and sizes[-1] < 320:
            sizes.append(320)
            continue
        break

    control, _ = open_chain(160, dict(PARAMETERS, mu1=0.0, omega=17.0))
    data = {
        "schema": "fock-checked-floquet-bdg-topology-v1",
        "date": "2026-11-11",
        "parameters": PARAMETERS,
        "convention": {
            "fock_contract": "passed via test_convention.py; single-site Heisenberg and two-site full-matrix equality",
            "k_onsite": "-mu/2",
            "k_hopping": "(delta-gamma)/4 and -(delta+gamma)/4",
            "legacy_results_sha256": hashlib.sha256(LEGACY_RESULTS.read_bytes()).hexdigest(),
            "legacy_results_modified": False,
            "legacy_conclusions_inherited": False,
        },
        "endpoint_invariants": endpoint_counts(**PARAMETERS),
        "winding": {
            "rows": winding_rows,
            "all_near_integer_within_1e-6": all(abs(row["winding"] - row["nearest_integer"]) < 1e-6 for row in winding_rows),
            "max_adjacent_difference": max(abs(right["winding"] - left["winding"]) for left, right in zip(winding_rows, winding_rows[1:])),
            "controls": controls,
            "logm_direction_checks": log_checks,
        },
        "sizes": sizes,
        "size_studies": studies,
        "convergence": {target: convergence(studies, target) for target in ("zero", "pi")},
        "static_trivial_control": control,
        "environment": {"python": platform.python_version(), "numpy": np.__version__, "scipy": scipy.__version__},
        "scope": {
            "fock_convention_checked": True,
            "interactions": False,
            "dissipation": False,
            "self_consistent_pairing": False,
            "material_tc_prediction": False,
            "experimental_validation": False,
            "thermodynamic_limit_proof": False,
            "legacy_results_overwritten": False,
        },
    }
    (ROOT / "results.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    np.savez_compressed(ROOT / "bloch_curve.npz", **curves)
    np.savez_compressed(ROOT / "spectra.npz", **{f"n{n}_eigenvalues": spectra[n]["eigenvalues"] for n in sizes}, **{f"n{n}_phase": spectra[n]["phase"] for n in sizes})
    with (ROOT / "candidates.csv").open("w", newline="", encoding="utf-8") as stream:
        fields = ["n", "target", "pair_rank", "max_distance", "min_edge_weight", "max_edge_weight", "min_ipr", "max_ipr", "conjugate_or_degenerate_error"]
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for study in studies:
            for target in ("zero", "pi"):
                for pair in study[f"{target}_nearest_pairs"]:
                    writer.writerow({
                        "n": study["n"], "target": target, "pair_rank": pair["rank"], "max_distance": pair["max_distance"],
                        "min_edge_weight": min(pair["edge_weights"]), "max_edge_weight": max(pair["edge_weights"]),
                        "min_ipr": min(pair["ipr"]), "max_ipr": max(pair["ipr"]),
                        "conjugate_or_degenerate_error": pair["conjugate_or_degenerate_error"],
                    })
    print(json.dumps({"winding": winding_rows, "convergence": data["convergence"]}, indent=2))


if __name__ == "__main__":
    main()
