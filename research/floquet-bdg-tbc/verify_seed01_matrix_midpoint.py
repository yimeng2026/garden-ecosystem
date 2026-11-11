"""Independently rebuild seed-0/1 midpoint paths and endpoint bindings."""

import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from analyze_seed6_matrix_path import build_links, evaluate_path  # noqa: E402
from analyze_seed01_matrix_midpoint import endpoint_binding  # noqa: E402

PROTOCOL = ROOT / "seed01_matrix_midpoint_protocol.json"
DATA = ROOT / "seed01_matrix_midpoint_analysis.json"
REFERENCE = ROOT / "seed6_matrix_midpoint_analysis.json"
BATCH_A = ROOT / "matched_beta_batch_a_analysis.json"
BATCH_C = ROOT / "matched_beta_batch_c_analysis.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    stored = json.loads(DATA.read_text(encoding="utf-8"))
    cells, matrices, links, method_grid_links, entry_links, fidelity, rank_controls = [], [], [], [], [], [], []
    for seed in protocol["seed_values"]:
        seed_cells, bases_by_key, seed_matrices, seed_fidelity, seed_rank, max_direction = evaluate_path(dict(protocol, seed=seed))
        seed_links, seed_method_links, seed_entry_links = build_links(dict(protocol, seed=seed), seed_cells, bases_by_key, seed_matrices)
        for collection in (seed_cells, seed_matrices, seed_links, seed_method_links, seed_entry_links, seed_fidelity, seed_rank):
            for row in collection:
                row["seed"] = seed
        cells.extend(seed_cells)
        matrices.extend(seed_matrices)
        links.extend(seed_links)
        method_grid_links.extend(seed_method_links)
        entry_links.extend(seed_entry_links)
        fidelity.extend(seed_fidelity)
        rank_controls.extend(seed_rank)
    max_spectrum_error = 0.0
    max_center_error = 0.0
    max_coarsening_error = 0.0
    for actual, expected in zip(cells, stored["cells"]):
        max_spectrum_error = max(max_spectrum_error, max(abs(x - y) for x, y in zip(actual["spectrum_first_six"], expected["spectrum_first_six"])))
        max_center_error = max(max_center_error, abs(actual["pairs"][0]["center"] - expected["pairs"][0]["center"]), abs(actual["pairs"][1]["center"] - expected["pairs"][1]["center"]))
        max_coarsening_error = max(max_coarsening_error, max(abs(x - y) for x, y in zip(actual["beta"], expected["beta"])))
    max_matrix_error = 0.0
    max_singular_error = 0.0
    for actual, expected in zip(matrices, stored["path_matrices"]):
        for i in range(2):
            for j in range(2):
                a, e = actual["overlap_matrix"][i][j], expected["overlap_matrix"][i][j]
                max_matrix_error = max(max_matrix_error, abs(a["overlap"] - e["overlap"]))
                max_singular_error = max(max_singular_error, max(abs(x - y) for x, y in zip(a["singular_values"], e["singular_values"])))
    max_entry_delta_error = 0.0
    driver_mismatch_count = 0
    for actual, expected in zip(entry_links, stored["entry_links"]):
        max_entry_delta_error = max(max_entry_delta_error, abs(actual["delta_overlap"] - expected["delta_overlap"]))
        for a, e in zip(actual["singular_channels"], expected["singular_channels"]):
            max_entry_delta_error = max(max_entry_delta_error, abs(a["delta_s_squared"] - e["delta_s_squared"]))
        if actual["dominant_singular_channel_index"] != expected["dominant_singular_channel_index"]:
            driver_mismatch_count += 1
    for actual, expected in zip(method_grid_links, stored["method_grid_links"]):
        for group in ("diagonal", "swapped"):
            if actual[f"dominant_{group}_entry"] != expected[f"dominant_{group}_entry"]:
                driver_mismatch_count += 1
    max_native_link_error = 0.0
    for actual, expected in zip(links, stored["links"]):
        for i in range(2):
            for j in range(2):
                max_native_link_error = max(max_native_link_error, abs(actual["overlap_matrix"][i][j]["overlap"] - expected["overlap_matrix"][i][j]["overlap"]))
    max_fidelity_error = max(abs(a["forward"] - e["forward"]) for a, e in zip(fidelity, stored["representation_fidelity"]))
    binding = endpoint_binding(cells, matrices, json.loads(BATCH_A.read_text(encoding="utf-8")), json.loads(BATCH_C.read_text(encoding="utf-8")))
    result = {
        "schema": "floquet-bdg-seed01-matrix-midpoint-independent-v1",
        "protocol_sha256": sha(PROTOCOL), "analysis_sha256": sha(DATA),
        "reference_seed6_analysis_sha256": sha(REFERENCE),
        "batch_a_analysis_sha256": sha(BATCH_A), "batch_c_analysis_sha256": sha(BATCH_C),
        "cell_count": len(cells), "cross_size_path_matrix_count": len(matrices),
        "native_adjacent_link_count": len(links), "entry_link_count": len(entry_links),
        "max_coarsening_absolute_error": max_coarsening_error,
        "max_spectrum_absolute_error": max_spectrum_error,
        "max_pair_center_absolute_error": max_center_error,
        "max_matrix_absolute_error": max_matrix_error,
        "max_singular_absolute_error": max_singular_error,
        "max_entry_delta_absolute_error": max_entry_delta_error,
        "max_native_link_absolute_error": max_native_link_error,
        "max_representation_fidelity_absolute_error": max_fidelity_error,
        "driver_mismatch_count": driver_mismatch_count,
        "endpoint_binding": binding,
        "new_winding_computed": False, "n640_computed": False,
    }
    result["all_passed"] = (
        len(cells) == 52 and len(matrices) == 156 and len(links) == 48 and len(entry_links) == 576
        and max_coarsening_error == 0 and max_spectrum_error <= 1e-12 and max_center_error <= 1e-12
        and max_matrix_error <= 1e-12 and max_singular_error <= 1e-12 and max_entry_delta_error <= 1e-12
        and max_native_link_error <= 1e-12 and max_fidelity_error <= 1e-12
        and driver_mismatch_count == 0
        and binding["max_matrix_absolute_error"] <= 1e-12
        and binding["max_singular_absolute_error"] <= 1e-12
        and binding["max_spectrum_absolute_error"] <= 1e-12
    )
    (ROOT / "seed01_matrix_midpoint_independent.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["all_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
