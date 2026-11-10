"""Run the preregistered kicked-Kitaev finite-size study."""

import csv
import json
import platform
from pathlib import Path

import numpy as np
import scipy
from scipy.sparse import csr_matrix
from scipy.sparse.linalg import eigs

from floquet_bdg import (
    ModelParameters,
    candidate_modes,
    endpoint_mode_counts,
    kicked_floquet,
    quasienergy_spectrum,
)

ROOT = Path(__file__).resolve().parent
PARAMETERS = ModelParameters()
SIZES = [40, 80, 160]


def serializable_candidate(candidate, spectrum, n):
    indices = candidate["indices"]
    return {
        "target": candidate["target"],
        "indices": indices,
        "eigenvalues_real": [float(spectrum["eigenvalues"][i].real) for i in indices],
        "eigenvalues_imag": [float(spectrum["eigenvalues"][i].imag) for i in indices],
        "phase": [float(spectrum["phase"][i]) for i in indices],
        "quasienergy": [float(spectrum["quasienergy"][i]) for i in indices],
        "distances": [float(x) for x in candidate["distances"]],
        "bulk_distance": candidate["bulk_distance"],
        "separation_ratios": [float(x) for x in candidate["separation_ratios"]],
        "edge_weights": [float(x) for x in candidate["edge_weights"]],
        "left_weights": [float(x) for x in candidate["left_weights"]],
        "right_weights": [float(x) for x in candidate["right_weights"]],
        "edge_sites_per_end": candidate["edge_sites_per_end"],
        "localized": [bool(x) for x in candidate["localized"]],
        "separated": [bool(x) for x in candidate["separated"]],
    }


def compute_chain(n, mu1):
    u, period = kicked_floquet(
        n,
        PARAMETERS.mu0,
        mu1,
        PARAMETERS.omega,
        PARAMETERS.gamma,
        PARAMETERS.delta,
    )
    spectrum = quasienergy_spectrum(u, period)
    return {
        "n": n,
        "period": period,
        "unitarity_error": float(np.max(np.abs(u.T @ u - np.eye(2 * n)))),
        "zero": serializable_candidate(candidate_modes(spectrum, n, 1.0), spectrum, n),
        "pi": serializable_candidate(candidate_modes(spectrum, n, -1.0), spectrum, n),
    }, spectrum


def sparse_crosscheck(n, dense_spectrum):
    # Rebuild U to avoid sharing eigenpairs between the two numerical methods.
    u, _ = kicked_floquet(n, PARAMETERS.mu0, PARAMETERS.mu1, PARAMETERS.omega, PARAMETERS.gamma, PARAMETERS.delta)
    sparse_u = csr_matrix(u)
    result = {}
    for label, target in (("zero", 1.0), ("pi", -1.0)):
        # A fixed nonzero start prevents irrelevant last-bit drift between runs.
        v0 = np.full(2 * n, 1 / np.sqrt(2 * n))
        values = eigs(sparse_u, k=6, sigma=target, which="LM", tol=1e-12, ncv=min(2 * n, 40), maxiter=10000, v0=v0, return_eigenvectors=False)
        dense_values = dense_spectrum["eigenvalues"]
        dense_pair = np.array(sorted(dense_values, key=lambda value: abs(value - target))[:2])
        sparse_pair = np.array(sorted(values, key=lambda value: abs(value - target))[:2])
        dense_pair = np.array(sorted(dense_pair, key=lambda value: (value.real, value.imag)))
        sparse_pair = np.array(sorted(sparse_pair, key=lambda value: (value.real, value.imag)))
        error = float(np.max(np.abs(dense_pair - sparse_pair)))
        result[label] = {
            "dense_pair_real": [float(value.real) for value in dense_pair],
            "dense_pair_imag": [float(value.imag) for value in dense_pair],
            "sparse_pair_real": [float(value.real) for value in sparse_pair],
            "sparse_pair_imag": [float(value.imag) for value in sparse_pair],
            "max_absolute_difference": error,
            "passed_tolerance_1e-8": bool(error < 1e-8),
        }
    result["method"] = "scipy.sparse.linalg.eigs shift-invert, k=6, sigma=±1, tol=1e-12, ncv=40"
    result["n"] = n
    return result


def main():
    invariant = endpoint_mode_counts(PARAMETERS.mu0, PARAMETERS.mu1, PARAMETERS.gamma, PARAMETERS.omega)
    studies = []
    spectra = {}
    for n in SIZES:
        study, spectrum = compute_chain(n, PARAMETERS.mu1)
        studies.append(study)
        spectra[n] = spectrum
        print(f"N={n}: zero distances={study['zero']['distances']}, pi distances={study['pi']['distances']}")
        print(f"  zero edge={study['zero']['edge_weights']}, pi edge={study['pi']['edge_weights']}")

    convergence = {}
    for target in ("zero", "pi"):
        distances = [max(study[target]["distances"]) for study in studies]
        reduction = distances[0] / distances[-1] if distances[-1] > 0 else float("inf")
        decreasing = all(left > right for left, right in zip(distances, distances[1:]))
        separated = all(all(study[target]["separated"]) for study in studies)
        localized = all(all(study[target]["localized"]) for study in studies)
        convergence[target] = {
            "max_candidate_distances_by_size": distances,
            "strictly_decreasing": decreasing,
            "first_to_last_reduction_factor": reduction,
            "all_candidates_separated": separated,
            "all_candidates_localized": localized,
            "finite_size_status": "supported_finite_size" if decreasing and reduction >= 2 and separated and localized else "inconclusive",
            "thermodynamic_limit_proof": False,
        }

    control, _ = compute_chain(160, mu1=0.0)
    comparison = sparse_crosscheck(160, spectra[160])
    data = {
        "schema": "finite-kicked-kitaev-floquet-v1",
        "date": "2026-11-11",
        "model": "Open quadratic Kitaev chain, Majorana basis, symmetric exact free/kick/free evolution",
        "parameters": {
            "gamma": PARAMETERS.gamma,
            "delta": PARAMETERS.delta,
            "mu0": PARAMETERS.mu0,
            "mu1": PARAMETERS.mu1,
            "omega": PARAMETERS.omega,
        },
        "sizes": SIZES,
        "endpoint_invariants": invariant,
        "size_studies": studies,
        "convergence": convergence,
        "static_trivial_control": control,
        "dense_sparse_comparison": comparison,
        "candidate_rule": {
            "per_target_count": 2,
            "separation_threshold": 0.1,
            "edge_weight_threshold": 0.5,
            "edge_sites_per_end": "ceil(0.1*N)",
            "finite_size_reduction_threshold": 2.0,
            "rule_fixed_before_results": True,
        },
        "environment": {"python": platform.python_version(), "numpy": np.__version__, "scipy": scipy.__version__},
        "scope": {
            "exact_piecewise_matrix_exponential": True,
            "fourier_truncation_applicable": False,
            "interactions": False,
            "dissipation": False,
            "self_consistent_pairing": False,
            "material_tc_prediction": False,
            "experimental_validation": False,
            "thermodynamic_limit_proof": False,
        },
    }
    (ROOT / "results.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    with (ROOT / "candidates.csv").open("w", newline="", encoding="utf-8") as stream:
        fields = ["n", "target", "candidate", "eigenvalue_real", "eigenvalue_imag", "distance", "bulk_distance", "separation_ratio", "edge_weight", "left_weight", "right_weight", "localized", "separated"]
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for study in studies:
            for target in ("zero", "pi"):
                row = study[target]
                for index in range(2):
                    writer.writerow({
                        "n": study["n"], "target": target, "candidate": index,
                        "eigenvalue_real": row["eigenvalues_real"][index],
                        "eigenvalue_imag": row["eigenvalues_imag"][index],
                        "distance": row["distances"][index], "bulk_distance": row["bulk_distance"],
                        "separation_ratio": row["separation_ratios"][index], "edge_weight": row["edge_weights"][index],
                        "left_weight": row["left_weights"][index], "right_weight": row["right_weights"][index],
                        "localized": row["localized"][index], "separated": row["separated"][index],
                    })
    np.savez_compressed(
        ROOT / "spectra.npz",
        **{f"n{n}_eigenvalues": spectra[n]["eigenvalues"] for n in SIZES},
        **{f"n{n}_phase": spectra[n]["phase"] for n in SIZES},
    )
    print(json.dumps({"convergence": convergence, "dense_sparse": comparison}, indent=2))


if __name__ == "__main__":
    main()
