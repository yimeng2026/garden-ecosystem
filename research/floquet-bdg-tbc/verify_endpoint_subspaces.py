"""Independently reproduce pair projectors with SciPy eig and an inverse Gram matrix."""

import hashlib
import json
from pathlib import Path
import sys

import numpy as np
from scipy.linalg import eig

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / "floquet-bdg-disorder"))
from disorder_model import disordered_floquet  # noqa: E402


def main():
    stored = json.loads((ROOT / "endpoint_subspace_analysis.json").read_text(encoding="utf-8"))
    source_hash = hashlib.sha256((ROOT / "scale_diagnostic.json").read_bytes()).hexdigest()
    if stored["source_sha256"] != source_hash:
        raise ValueError("The source diagnostic changed after the pair analysis")
    rows = []
    for case in stored["cases"]:
        n, strength, seed = case["n"], case["strength"], case["seed"]
        beta = np.random.default_rng(20261111 + seed).random(n)
        u, _ = disordered_floquet(n, 2.5, beta, strength, 7.0, 1.0, 1.0)
        values, vectors = eig(u)
        order = np.argsort(np.abs(values - 1.0))
        pair_rows = []
        for pair in case["pairs"]:
            indices = order[2 * pair["pair_index"]:2 * pair["pair_index"] + 2]
            selected = vectors[:, indices]
            gram_inverse = np.linalg.inv(selected.conj().T @ selected)
            projector = selected @ gram_inverse @ selected.conj().T
            diagonal = np.real(np.diag(projector))
            profile = diagonal.reshape((n, 2)).sum(axis=1) / 2
            original = np.asarray(pair["profile"])
            edge_sites = pair["edge_sites_per_end"]
            edge_weight = float(profile[:edge_sites].sum() + profile[-edge_sites:].sum())
            pair_rows.append({
                "pair_index": pair["pair_index"],
                "spectrum_indices": [int(index) for index in indices],
                "max_profile_absolute_error": float(np.max(np.abs(profile - original))),
                "edge_weight_absolute_error": abs(edge_weight - pair["edge_weight"]),
            })
        rows.append({"n": n, "pairs": pair_rows})
    passed = all(
        pair["max_profile_absolute_error"] <= 1e-10 and pair["edge_weight_absolute_error"] <= 1e-10
        for case in rows for pair in case["pairs"]
    )
    result = {
        "schema": "floquet-bdg-endpoint-independent-v1",
        "source_sha256": source_hash,
        "analysis_sha256": hashlib.sha256((ROOT / "endpoint_subspace_analysis.json").read_bytes()).hexdigest(),
        "eigensolver": "scipy.linalg.eig",
        "projector": "direct_gram_inverse",
        "tolerance": 1e-10,
        "all_passed": passed,
        "cases": rows,
        "scope": "Independent numerical reproduction only; no new physics input and no retroactive endpoint recovery.",
    }
    (ROOT / "endpoint_subspace_independent.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
