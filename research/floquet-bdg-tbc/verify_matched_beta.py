"""Independently rebuild nested beta arrays and both Floquet spectra."""

import hashlib
import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / "floquet-bdg-disorder"))
from disorder_model import disordered_floquet  # noqa: E402
from convention_model import quasienergy_spectrum  # noqa: E402

PROTOCOL = ROOT / "matched_beta_control_protocol.json"
CANDIDATE = ROOT / "swap_candidate_spectrum_analysis.json"
DATA = ROOT / "matched_beta_control_analysis.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    data = json.loads(DATA.read_text(encoding="utf-8"))
    seed, strength, master_grid = protocol["seed"], protocol["strength"], protocol["master_grid"]
    master = np.random.default_rng(20261111 + seed).random(master_grid)
    master_error = float(np.max(np.abs(master - np.asarray(data["master_profile"]))))
    coarsening_error = 0.0
    spectrum_error = 0.0
    center_error = 0.0
    rows = []
    for stored in data["cells"]:
        n = stored["n"]
        beta = master.reshape(n, master_grid // n).mean(axis=1)
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
        rows.append({"n": n, "computed_pair_centers": pair_centers, "computed_first_six": [float(value) for value in computed_first_six]})
    result = {
        "schema": "floquet-bdg-matched-beta-independent-v1",
        "protocol_sha256": sha(PROTOCOL), "candidate_source_sha256": sha(CANDIDATE),
        "cell_count": len(rows), "max_master_profile_absolute_error": master_error,
        "max_coarsening_absolute_error": coarsening_error,
        "max_spectrum_absolute_error": spectrum_error,
        "max_pair_center_absolute_error": center_error,
        "new_winding_computed": False, "n640_computed": False,
        "cells": rows,
    }
    result["all_passed"] = (
        len(rows) == 2 and master_error == 0 and coarsening_error == 0
        and spectrum_error <= 1e-12 and center_error <= 1e-12
    )
    (ROOT / "matched_beta_independent.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["all_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
