"""Independently recheck every matrix-entry and singular-channel decomposition."""

import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PROTOCOL = ROOT / "overlap_matrix_response_protocol.json"
DATA = ROOT / "overlap_matrix_response_analysis.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sign(value):
    return 1 if value > 0 else -1 if value < 0 else 0


def main():
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    data = json.loads(DATA.read_text(encoding="utf-8"))
    sources = {
        name: json.loads((ROOT / f"matched_beta_batch_{name}_analysis.json").read_text(encoding="utf-8"))
        for name in ("a", "b", "c")
    }
    rows = sources["a"]["realizations"] + sources["b"]["realizations"] + sources["c"]["realizations"]
    by_key = {(row["seed"], row["strength"]): row for row in rows}
    max_delta_error = 0.0
    max_singular_delta_error = 0.0
    max_ratio_error = 0.0
    max_log2_ratio_error = 0.0
    driver_mismatch_count = 0
    agreement_mismatch_count = 0
    singular_count = 0
    entry_lookup = {}
    for stored in data["entry_transitions"]:
        seed, method, m, i, j = stored["seed"], stored["method"], stored["m"], stored["i"], stored["j"]
        before_row = by_key[(seed, stored["from_strength"])]
        after_row = by_key[(seed, stored["to_strength"])]
        before_grid = next(grid for grid in before_row["methods"][method]["grids"] if grid["m"] == m)
        after_grid = next(grid for grid in after_row["methods"][method]["grids"] if grid["m"] == m)
        before = before_grid["overlap_matrix"][i][j]
        after = after_grid["overlap_matrix"][i][j]
        delta = after["overlap"] - before["overlap"]
        max_delta_error = max(max_delta_error, abs(delta - stored["delta_overlap"]))
        expected_ratio = after["overlap"] / before["overlap"] if before["overlap"] else None
        if expected_ratio is None:
            if stored["ratio"] is not None or stored["log2_ratio"] is not None:
                raise ValueError("Non-null ratio with zero denominator")
        else:
            max_ratio_error = max(max_ratio_error, abs(expected_ratio - stored["ratio"]))
            max_log2_ratio_error = max(max_log2_ratio_error, abs(math.log2(expected_ratio) - stored["log2_ratio"]))
        expected_channels = []
        for k in range(2):
            delta_s_squared = after["singular_values"][k] ** 2 - before["singular_values"][k] ** 2
            expected_channels.append(delta_s_squared)
            max_singular_delta_error = max(max_singular_delta_error, abs(delta_s_squared - stored["singular_channels"][k]["delta_s_squared"]))
            singular_count += 1
        expected_driver = max((0, 1), key=lambda k: abs(expected_channels[k] / 2))
        if expected_driver != stored["dominant_singular_channel_index"]:
            driver_mismatch_count += 1
        entry_lookup[(seed, method, m, i, j)] = stored
    for stored in data["method_grid_transitions"]:
        seed, method, m = stored["seed"], stored["method"], stored["m"]
        before_row = by_key[(seed, stored["from_strength"])]
        after_row = by_key[(seed, stored["to_strength"])]
        before_grid = next(grid for grid in before_row["methods"][method]["grids"] if grid["m"] == m)
        after_grid = next(grid for grid in after_row["methods"][method]["grids"] if grid["m"] == m)
        delta_diagonal = after_grid["diagonal_score"] - before_grid["diagonal_score"]
        delta_swapped = after_grid["swapped_score"] - before_grid["swapped_score"]
        max_delta_error = max(max_delta_error, abs(delta_diagonal - stored["delta_diagonal_score"]), abs(delta_swapped - stored["delta_swapped_score"]))
        for group, pairs in (("diagonal", ((0, 0), (1, 1))), ("swapped", ((0, 1), (1, 0)))):
            expected_entry = max(pairs, key=lambda ij: abs(entry_lookup[(seed, method, m, *ij)]["score_contribution"]))
            if stored[f"dominant_{group}_entry"] != f"O{expected_entry[0]}{expected_entry[1]}":
                driver_mismatch_count += 1
        expected_diagonal_ratio = after_grid["diagonal_score"] / before_grid["diagonal_score"] if before_grid["diagonal_score"] else None
        expected_swapped_ratio = after_grid["swapped_score"] / before_grid["swapped_score"] if before_grid["swapped_score"] else None
        if expected_diagonal_ratio is not None:
            max_ratio_error = max(max_ratio_error, abs(expected_diagonal_ratio - stored["diagonal_score_ratio"]))
        if expected_swapped_ratio is not None:
            max_ratio_error = max(max_ratio_error, abs(expected_swapped_ratio - stored["swapped_score_ratio"]))
    for stored in data["representation_delta_agreements"]:
        seed, m, entry = stored["seed"], stored["m"], stored["entry"]
        i, j = int(entry[1]), int(entry[2])
        lp = entry_lookup[(seed, "linear_point", m, i, j)]
        ca = entry_lookup[(seed, "cell_average", m, i, j)]
        expected_lp, expected_ca = sign(lp["delta_overlap"]), sign(ca["delta_overlap"])
        if stored["linear_point_sign"] != expected_lp or stored["cell_average_sign"] != expected_ca or stored["agreement"] != (expected_lp == expected_ca):
            agreement_mismatch_count += 1
    independent_paths = [ROOT / f"matched_beta_batch_{name}_independent.json" for name in ("a", "b", "c")]
    independent_hashes = {path.name: sha(path) for path in independent_paths}
    source_all_passed = all(json.loads(path.read_text(encoding="utf-8")).get("all_passed") is True for path in independent_paths)
    result = {
        "schema": "floquet-bdg-overlap-matrix-response-independent-v1",
        "protocol_sha256": sha(PROTOCOL), "analysis_sha256": sha(DATA),
        "method_grid_transition_count": len(data["method_grid_transitions"]),
        "entry_transition_count": len(data["entry_transitions"]),
        "singular_channel_transition_count": singular_count,
        "representation_delta_comparison_count": len(data["representation_delta_agreements"]),
        "max_delta_absolute_error": max_delta_error,
        "max_singular_delta_absolute_error": max_singular_delta_error,
        "max_ratio_absolute_error": max_ratio_error,
        "max_log2_ratio_absolute_error": max_log2_ratio_error,
        "driver_mismatch_count": driver_mismatch_count,
        "agreement_mismatch_count": agreement_mismatch_count,
        "source_independent_rechecks_all_passed": source_all_passed,
        "source_independent_sha256": independent_hashes,
        "new_floquet_spectra_recomputed": False,
    }
    result["all_passed"] = (
        result["method_grid_transition_count"] == 48 and result["entry_transition_count"] == 192
        and singular_count == 384 and result["representation_delta_comparison_count"] == 96
        and max_delta_error <= 1e-15 and max_singular_delta_error <= 1e-15
        and max_ratio_error <= 1e-12 and max_log2_ratio_error <= 1e-12
        and driver_mismatch_count == 0 and agreement_mismatch_count == 0 and source_all_passed
    )
    (ROOT / "overlap_matrix_response_independent.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["all_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
