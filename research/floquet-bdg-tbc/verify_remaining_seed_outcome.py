"""Independently rebuild one remaining-seed path and its raw outcomes."""

import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from analyze_seed6_matrix_path import build_links, driver_summary, entry_extrema, evaluate_path  # noqa: E402
from analyze_seed6_matrix_midpoint import driver_comparisons, jump_comparisons  # noqa: E402

PROTOCOL = ROOT / "remaining_seed_outcome_protocol.json"
CANDIDATES = ROOT / "profile_stat_candidates_analysis.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def endpoint_recheck(seed, cells, matrices, protocol):
    errors = {"max_matrix_absolute_error": 0.0, "max_singular_absolute_error": 0.0, "max_spectrum_absolute_error": 0.0}
    for strength_text, filename in protocol["endpoint_sources_by_seed"][str(seed)].items():
        strength = float(strength_text)
        source = json.loads((ROOT / filename).read_text(encoding="utf-8"))
        source_row = next(row for row in source["realizations"] if row["seed"] == seed and row["strength"] == strength)
        for method in protocol["methods"]:
            for m in protocol["common_grids"]:
                actual = next(row for row in matrices if row["strength"] == strength and row["method"] == method and row["m"] == m)
                expected = next(row for row in source_row["methods"][method]["grids"] if row["m"] == m)
                for i in range(2):
                    for j in range(2):
                        a = actual["overlap_matrix"][i][j]
                        e = expected["overlap_matrix"][i][j]
                        errors["max_matrix_absolute_error"] = max(errors["max_matrix_absolute_error"], abs(a["overlap"] - e["overlap"]))
                        errors["max_singular_absolute_error"] = max(errors["max_singular_absolute_error"], max(abs(x - y) for x, y in zip(a["singular_values"], e["singular_values"])))
        for n in protocol["n_values"]:
            actual = next(cell for cell in cells if cell["strength"] == strength and cell["n"] == n)
            expected = next(cell for cell in source_row["cells"] if cell["n"] == n)
            errors["max_spectrum_absolute_error"] = max(errors["max_spectrum_absolute_error"], max(abs(x - y) for x, y in zip(actual["spectrum_first_six"], expected["spectrum_first_six"])))
    return errors


def main(seed):
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    data_path = ROOT / f"remaining_seed{seed}_path_outcome_analysis.json"
    stored = json.loads(data_path.read_text(encoding="utf-8"))
    master = np.random.default_rng(20261111 + seed).random(protocol["master_grid"])
    stored_master = np.asarray(stored["master_profile"], dtype=float)
    max_master_error = float(np.max(np.abs(master - stored_master)))
    cells, bases, matrices, fidelity, rank_controls, _ = evaluate_path(dict(protocol, seed=seed))
    links, method_links, entry_links = build_links(dict(protocol, seed=seed), cells, bases, matrices)
    for collection in (cells, matrices, links, method_links, entry_links, fidelity, rank_controls):
        for row in collection:
            row["seed"] = seed

    max_spectrum_error = 0.0
    max_beta_error = 0.0
    max_center_error = 0.0
    for actual, expected in zip(cells, stored["cells"]):
        max_spectrum_error = max(max_spectrum_error, max(abs(x - y) for x, y in zip(actual["spectrum_first_six"], expected["spectrum_first_six"])))
        max_beta_error = max(max_beta_error, max(abs(x - y) for x, y in zip(actual["beta"], expected["beta"])))
        max_center_error = max(max_center_error, max(abs(actual["pairs"][k]["center"] - expected["pairs"][k]["center"]) for k in (0, 1)))
    max_matrix_error = 0.0
    max_singular_error = 0.0
    for actual, expected in zip(matrices, stored["path_matrices"]):
        for i in range(2):
            for j in range(2):
                a, e = actual["overlap_matrix"][i][j], expected["overlap_matrix"][i][j]
                max_matrix_error = max(max_matrix_error, abs(a["overlap"] - e["overlap"]))
                max_singular_error = max(max_singular_error, max(abs(x - y) for x, y in zip(a["singular_values"], e["singular_values"])))
    max_entry_error = 0.0
    entry_driver_mismatches = 0
    for actual, expected in zip(entry_links, stored["entry_links"]):
        max_entry_error = max(max_entry_error, abs(actual["delta_overlap"] - expected["delta_overlap"]))
        for a, e in zip(actual["singular_channels"], expected["singular_channels"]):
            max_entry_error = max(max_entry_error, abs(a["delta_s_squared"] - e["delta_s_squared"]))
        entry_driver_mismatches += actual["dominant_singular_channel_index"] != expected["dominant_singular_channel_index"]
    for actual, expected in zip(method_links, stored["method_grid_links"]):
        for group in ("diagonal", "swapped"):
            entry_driver_mismatches += actual[f"dominant_{group}_entry"] != expected[f"dominant_{group}_entry"]
    max_native_error = 0.0
    for actual, expected in zip(links, stored["links"]):
        for i in range(2):
            for j in range(2):
                max_native_error = max(max_native_error, abs(actual["overlap_matrix"][i][j]["overlap"] - expected["overlap_matrix"][i][j]["overlap"]))
    max_fidelity_error = max(abs(a["forward"] - e["forward"]) for a, e in zip(fidelity, stored["representation_fidelity"]))

    midpoints = set(protocol["new_midpoint_strengths"])
    original_matrices = [row for row in matrices if row["strength"] not in midpoints]
    original_method_links = [row for row in method_links if row["from"] not in midpoints and row["to"] not in midpoints]
    original_entry_links = [row for row in entry_links if row["from"] not in midpoints and row["to"] not in midpoints]
    original_extrema = entry_extrema(original_matrices, original_entry_links)
    extrema = entry_extrema(matrices, entry_links)
    original_drivers = driver_summary(original_method_links)
    drivers = driver_summary(method_links)
    jumps = jump_comparisons(original_extrema, extrema, protocol["new_midpoint_strengths"])
    jump_mismatches = 0
    jump_fields = ("method", "entry", "old_max_adjacent_absolute_jump", "refined_max_adjacent_absolute_jump", "old_jump_from", "old_jump_to", "refined_jump_from", "refined_jump_to", "jump_changed")
    for actual, expected in zip(jumps, stored["jump_comparisons"]):
        transformed = dict(expected)
        transformed["old_max_adjacent_absolute_jump"] = expected["original_max_adjacent_absolute_jump"]
        transformed["old_jump_from"] = expected["original_jump_from"]
        transformed["old_jump_to"] = expected["original_jump_to"]
        jump_mismatches += any(actual[field] != transformed[field] for field in jump_fields)
    jump_mismatches += sum(row["jump_changed"] for row in jumps) != stored["summary"]["jump_change_count"]
    driver_changes = driver_comparisons(original_drivers, drivers)
    driver_mismatches = 0
    for actual, expected in zip(driver_changes, stored["driver_comparisons"]):
        for field in ("method", "score_group", "driver_counts_changed"):
            driver_mismatches += actual[field] != expected[field]
        driver_mismatches += actual["old_dominant_entry_counts"] != expected["original_dominant_entry_counts"]
        driver_mismatches += actual["refined_dominant_entry_counts"] != expected["refined_dominant_entry_counts"]
    driver_mismatches += sum(row["driver_counts_changed"] for row in driver_changes) != stored["summary"]["driver_comparison_change_count"]

    endpoint = endpoint_recheck(seed, cells, matrices, protocol)
    result = {
        "schema": "floquet-bdg-remaining-seed-path-outcome-independent-v1",
        "seed": seed, "protocol_sha256": sha(PROTOCOL), "analysis_sha256": sha(data_path),
        "candidate_source_analysis_sha256": sha(CANDIDATES),
        "cell_count": len(cells), "cross_size_path_matrix_count": len(matrices),
        "native_adjacent_link_count": len(links), "entry_link_count": len(entry_links),
        "jump_change_count": sum(row["jump_changed"] for row in jumps),
        "driver_comparison_change_count": sum(row["driver_counts_changed"] for row in driver_changes),
        "max_master_absolute_error": max_master_error,
        "max_beta_absolute_error": max_beta_error,
        "max_spectrum_absolute_error": max_spectrum_error,
        "max_pair_center_absolute_error": max_center_error,
        "max_matrix_absolute_error": max_matrix_error,
        "max_singular_absolute_error": max_singular_error,
        "max_entry_delta_absolute_error": max_entry_error,
        "max_native_link_absolute_error": max_native_error,
        "max_representation_fidelity_absolute_error": max_fidelity_error,
        "entry_driver_mismatch_count": entry_driver_mismatches,
        "jump_outcome_mismatch_count": jump_mismatches,
        "driver_outcome_mismatch_count": driver_mismatches,
        "endpoint_binding": endpoint,
        "preregistered_floquet_cells_recomputed": 26,
        "additional_unregistered_floquet_spectra": 0,
        "new_floquet_spectra_recomputed": False,
        "new_winding_computed": False, "n640_computed": False,
        "candidate_evaluation_performed": False,
    }
    result["all_passed"] = (
        stored["protocol_sha256"] == sha(PROTOCOL)
        and stored["candidate_source_analysis_sha256"] == sha(CANDIDATES)
        and stored["seed"] == seed
        and len(cells) == 26 and len(matrices) == 78 and len(links) == 24 and len(entry_links) == 288
        and max_master_error == 0.0 and max_beta_error == 0.0 and max_spectrum_error == 0.0
        and max_center_error <= 1e-12 and max_matrix_error <= 1e-12 and max_singular_error <= 1e-12
        and max_entry_error <= 1e-12 and max_native_error <= 1e-12 and max_fidelity_error <= 1e-12
        and entry_driver_mismatches == 0 and jump_mismatches == 0 and driver_mismatches == 0
        and all(value <= 1e-12 for value in endpoint.values())
        and stored["candidate_evaluation_deferred"] and not stored["candidate_validation_completed"]
        and stored["holdout_pair_evaluations"] == []
    )
    out = ROOT / f"remaining_seed{seed}_path_outcome_independent.json"
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["all_passed"] else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, required=True, choices=[2, 3, 4, 5, 7])
    args = parser.parse_args()
    raise SystemExit(main(args.seed))
