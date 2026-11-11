"""Rebuild all batch-B spectra while distinguishing new cells from the reused anchor."""

import hashlib
import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / "floquet-bdg-disorder"))
from disorder_model import disordered_floquet  # noqa: E402
from convention_model import quasienergy_spectrum  # noqa: E402

PROTOCOL = ROOT / "matched_beta_batch_b_protocol.json"
DATA = ROOT / "matched_beta_batch_b_analysis.json"
ANCHOR_INDEPENDENT = ROOT / "matched_beta_independent.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    data = json.loads(DATA.read_text(encoding="utf-8"))
    anchor_independent = json.loads(ANCHOR_INDEPENDENT.read_text(encoding="utf-8"))
    master_error = 0.0
    coarsening_error = 0.0
    spectrum_error = 0.0
    center_error = 0.0
    realizations = []
    new_rebuilt_cell_count = 0
    anchor_rechecked_cell_count = 0
    for stored_realization in data["realizations"]:
        seed = stored_realization["seed"]
        strength = stored_realization["strength"]
        role = stored_realization["evidence_role"]
        master = np.random.default_rng(20261111 + seed).random(protocol["master_grid"])
        realization_master_error = float(np.max(np.abs(master - np.asarray(stored_realization["master_profile"]))))
        master_error = max(master_error, realization_master_error)
        cells = []
        for stored in stored_realization["cells"]:
            n = stored["n"]
            beta = master.reshape(n, protocol["master_grid"] // n).mean(axis=1)
            beta_difference = beta - np.asarray(stored["beta"])
            coarsening_error = max(coarsening_error, float(np.max(np.abs(beta_difference))))
            u, period = disordered_floquet(n, 2.5, beta, strength, 7.0, 1.0, 1.0)
            spectrum = quasienergy_spectrum(u, period)
            distances = np.abs(spectrum["eigenvalues"] - 1.0)
            order = np.argsort(distances)
            computed_first_six = distances[order[:6]]
            spectrum_difference = computed_first_six - np.asarray(stored["spectrum_first_six"])
            spectrum_error = max(spectrum_error, float(np.max(np.abs(spectrum_difference))))
            pair_centers = [float(np.mean(distances[order[2 * index:2 * index + 2]])) for index in (0, 1)]
            for pair_index, center in enumerate(pair_centers):
                center_error = max(center_error, abs(center - stored["pairs"][pair_index]["center"]))
            cells.append({"n": n, "computed_pair_centers": pair_centers, "computed_first_six": [float(value) for value in computed_first_six]})
            if role == "reused_anchor":
                anchor_rechecked_cell_count += 1
            else:
                new_rebuilt_cell_count += 1
        realizations.append({
            "seed": seed, "strength": strength, "evidence_role": role,
            "master_profile_sha256": hashlib.sha256(master.tobytes()).hexdigest(),
            "max_master_profile_absolute_error": realization_master_error,
            "cells": cells,
        })
    result = {
        "schema": "floquet-bdg-matched-beta-batch-b-independent-v1",
        "protocol_sha256": sha(PROTOCOL), "analysis_sha256": sha(DATA),
        "anchor_independent_source_sha256": sha(ANCHOR_INDEPENDENT),
        "anchor_independent_source_all_passed": anchor_independent.get("all_passed") is True,
        "realization_count": len(realizations), "cell_count": new_rebuilt_cell_count + anchor_rechecked_cell_count,
        "new_rebuilt_cell_count": new_rebuilt_cell_count,
        "anchor_rechecked_cell_count": anchor_rechecked_cell_count,
        "max_master_profile_absolute_error": master_error,
        "max_coarsening_absolute_error": coarsening_error,
        "max_spectrum_absolute_error": spectrum_error,
        "max_pair_center_absolute_error": center_error,
        "new_winding_computed": False, "n640_computed": False,
        "realizations": realizations,
    }
    result["all_passed"] = (
        len(realizations) == 8 and result["cell_count"] == 16
        and new_rebuilt_cell_count == 14 and anchor_rechecked_cell_count == 2
        and result["anchor_independent_source_all_passed"]
        and master_error == 0 and coarsening_error == 0
        and spectrum_error <= 1e-12 and center_error <= 1e-12
    )
    (ROOT / "matched_beta_batch_b_independent.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in result.items() if key != "realizations"}, ensure_ascii=False, indent=2))
    return 0 if result["all_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
