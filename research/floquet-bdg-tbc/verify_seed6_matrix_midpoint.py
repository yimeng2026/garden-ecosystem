"""Independently rebuild midpoint path and verify original-path binding."""

import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from analyze_seed6_matrix_path import build_links, evaluate_path  # noqa: E402
from analyze_seed6_matrix_midpoint import original_path_binding  # noqa: E402

PROTOCOL = ROOT / "seed6_matrix_midpoint_protocol.json"
DATA = ROOT / "seed6_matrix_midpoint_analysis.json"
ORIGINAL = ROOT / "seed6_matrix_path_analysis.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    stored = json.loads(DATA.read_text(encoding="utf-8"))
    original = json.loads(ORIGINAL.read_text(encoding="utf-8"))
    cells, bases_by_key, matrices, fidelity, rank_controls, max_direction = evaluate_path(protocol)
    links, method_grid_links, entry_links = build_links(protocol, cells, bases_by_key, matrices)
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
    binding = original_path_binding(cells, matrices, original)
    result = {
        "schema": "floquet-bdg-seed6-matrix-midpoint-independent-v1",
        "protocol_sha256": sha(PROTOCOL), "analysis_sha256": sha(DATA), "original_path_analysis_sha256": sha(ORIGINAL),
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
        "max_direction_absolute_error": max_direction,
        "driver_mismatch_count": driver_mismatch_count,
        "original_path_binding": binding,
        "new_winding_computed": False, "n640_computed": False,
    }
    result["all_passed"] = (
        len(cells) == 26 and len(matrices) == 78 and len(links) == 24 and len(entry_links) == 288
        and max_coarsening_error == 0 and max_spectrum_error <= 1e-12 and max_center_error <= 1e-12
        and max_matrix_error <= 1e-12 and max_singular_error <= 1e-12 and max_entry_delta_error <= 1e-12
        and max_native_link_error <= 1e-12 and max_fidelity_error <= 1e-12
        and max_direction <= 1e-12 and driver_mismatch_count == 0
        and binding["original_cell_count"] == 18 and binding["original_matrix_count"] == 54
        and binding["max_matrix_absolute_error"] <= 1e-12
        and binding["max_singular_absolute_error"] <= 1e-12
        and binding["max_spectrum_absolute_error"] <= 1e-12
    )
    (ROOT / "seed6_matrix_midpoint_independent.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["all_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
