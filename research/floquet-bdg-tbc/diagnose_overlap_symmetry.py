"""Localize reported common-grid overlap asymmetry without changing scientific evidence."""

import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from analyze_subspace_overlap import (  # noqa: E402
    SOURCE, compute_subspaces, embedded_orthonormal_basis, overlap_entry, source_cell,
)
from analyze_embedding_robustness import embedded_cell_average_basis  # noqa: E402


def directional_metrics(first, second):
    forward = overlap_entry(first, second)
    reverse = overlap_entry(second, first)
    direct_forward = float(np.linalg.norm(first.conj().T @ second, "fro") ** 2 / 2)
    direct_reverse = float(np.linalg.norm(second.conj().T @ first, "fro") ** 2 / 2)
    return {
        "forward": forward["overlap"],
        "reverse": reverse["overlap"],
        "direction_absolute_error": abs(forward["overlap"] - reverse["overlap"]),
        "svd_direct_forward_absolute_error": abs(forward["overlap"] - direct_forward),
        "svd_direct_reverse_absolute_error": abs(reverse["overlap"] - direct_reverse),
        "forward_singular_values": forward["singular_values"],
        "reverse_singular_values": reverse["singular_values"],
        "first_orthonormality_error": float(np.linalg.norm(first.conj().T @ first - np.eye(first.shape[1]), "fro")),
        "second_orthonormality_error": float(np.linalg.norm(second.conj().T @ second - np.eye(second.shape[1]), "fro")),
    }


def main():
    rng = np.random.default_rng(20261111)
    random_basis = []
    for _ in range(4):
        raw = rng.normal(size=(40, 2)) + 1j * rng.normal(size=(40, 2))
        random_basis.append(np.linalg.qr(raw, mode="reduced")[0])
    random_result = directional_metrics(random_basis[0], random_basis[1])
    print(json.dumps({"deterministic_complex_qr": random_result}, ensure_ascii=False, indent=2))

    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    computed = {}
    layout_error = 0.0
    for n in (400, 600):
        stored = source_cell(source, n, 0.05, 6)
        pair_records, subspaces = compute_subspaces(n, 0.05, 6, stored)
        if max(row["max_profile_absolute_error"] for row in pair_records) > 1e-10:
            raise ValueError(f"Frozen profile gate failed for N={n}")
        for subspace in subspaces:
            restored = subspace.reshape((2 * n, 2)).reshape((n, 2, 2))
            layout_error = max(layout_error, float(np.max(np.abs(restored - subspace))))
        computed[n] = subspaces

    results = []
    for name, embedding in (("linear_point", embedded_orthonormal_basis), ("cell_average", embedded_cell_average_basis)):
        q400 = [embedding(subspace, 1200) for subspace in computed[400]]
        q600 = [embedding(subspace, 1200) for subspace in computed[600]]
        entries = [[directional_metrics(q400[i], q600[j]) for j in range(2)] for i in range(2)]
        result = {
            "method": name,
            "n400_n600_m": [400, 600, 1200],
            "reshape_roundtrip_absolute_error": layout_error,
            "entries": entries,
            "O01_minus_O10": entries[0][1]["forward"] - entries[1][0]["forward"],
            "max_direction_absolute_error": max(entry["direction_absolute_error"] for row in entries for entry in row),
            "max_svd_direct_absolute_error": max(max(entry["svd_direct_forward_absolute_error"], entry["svd_direct_reverse_absolute_error"]) for row in entries for entry in row),
            "max_orthonormality_error": max(max(entry["first_orthonormality_error"], entry["second_orthonormality_error"]) for row in entries for entry in row),
        }
        results.append(result)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    summary = {
        "diagnosis_scope": "direction_reversal_is_required; O01_equals_O10_is_not_required_for_four_distinct_subspaces",
        "max_direction_absolute_error": max(result["max_direction_absolute_error"] for result in results),
        "max_svd_direct_absolute_error": max(result["max_svd_direct_absolute_error"] for result in results),
        "max_orthonormality_error": max(result["max_orthonormality_error"] for result in results),
        "reshape_roundtrip_absolute_error": layout_error,
    }
    record = {
        "schema": "floquet-bdg-overlap-symmetry-diagnostic-v1",
        "seed": 6, "strength": 0.05, "common_grid": 1200,
        "production_formula_changed": False, "scientific_scores_changed": False,
        "deterministic_complex_qr": random_result, "methods": results, "summary": summary,
    }
    (ROOT / "overlap_symmetry_diagnostic.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print("generated overlap_symmetry_diagnostic.json")


if __name__ == "__main__":
    main()
