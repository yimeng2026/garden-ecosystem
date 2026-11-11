"""Minimal worst-case check of embedding-induced same-N rank leakage."""

import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from analyze_subspace_overlap import SOURCE, compute_subspaces, embedded_orthonormal_basis, overlap_entry, source_cell  # noqa: E402
from analyze_embedding_robustness import embedded_cell_average_basis  # noqa: E402


def off_diagonal(first, second):
    return {
        "off01": overlap_entry(first, second)["overlap"],
        "off10": overlap_entry(second, first)["overlap"],
        "self00": overlap_entry(first, first)["overlap"],
        "self11": overlap_entry(second, second)["overlap"],
    }


def main():
    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    stored = source_cell(source, 400, 0.1, 0)
    pair_records, subspaces = compute_subspaces(400, 0.1, 0, stored)
    if max(row["max_profile_absolute_error"] for row in pair_records) > 1e-10:
        raise ValueError("Frozen profile gate failed")
    native = [np.linalg.qr(subspace.reshape((800, 2)), mode="reduced")[0] for subspace in subspaces]
    linear = [embedded_orthonormal_basis(subspace, 2400) for subspace in subspaces]
    cell = [embedded_cell_average_basis(subspace, 2400) for subspace in subspaces]
    result = {
        "seed": 0, "strength": 0.1, "n": 400, "m": 2400,
        "native_qr": off_diagonal(*native),
        "linear_point": off_diagonal(*linear),
        "cell_average": off_diagonal(*cell),
        "hypothesis": "linear interpolation does not preserve the native cross-pair Gram matrix; nested cell repetition preserves its zero off-diagonal blocks up to a scalar factor",
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
