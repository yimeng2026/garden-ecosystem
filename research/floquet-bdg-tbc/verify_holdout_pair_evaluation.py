"""Independently replay all 400 candidate-pair records without new spectra."""

import hashlib
import itertools
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PROTOCOL = ROOT / "remaining_seed_outcome_protocol.json"
CANDIDATES = ROOT / "profile_stat_candidates_analysis.json"
DATA = ROOT / "holdout_pair_evaluation_analysis.json"
OUT = ROOT / "holdout_pair_evaluation_independent.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sign(value):
    return 1 if value > 0 else -1 if value < 0 else 0


def main():
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    candidates = json.loads(CANDIDATES.read_text(encoding="utf-8"))
    stored = json.loads(DATA.read_text(encoding="utf-8"))
    source_paths = {
        "seed01_matrix_midpoint_analysis.json": ROOT / "seed01_matrix_midpoint_analysis.json",
        "seed6_matrix_midpoint_analysis.json": ROOT / "seed6_matrix_midpoint_analysis.json",
        **{f"remaining_seed{seed}_path_outcome_analysis.json": ROOT / f"remaining_seed{seed}_path_outcome_analysis.json" for seed in (2, 3, 4, 5, 7)},
    }
    seed01 = json.loads(source_paths["seed01_matrix_midpoint_analysis.json"].read_text(encoding="utf-8"))
    seed6 = json.loads(source_paths["seed6_matrix_midpoint_analysis.json"].read_text(encoding="utf-8"))
    jumps = {str(row["seed"]): row["jump_change_count"] for row in seed01["summary_by_seed"]}
    jumps["6"] = seed6["summary"]["jump_change_count"]
    for seed in (2, 3, 4, 5, 7):
        row = json.loads(source_paths[f"remaining_seed{seed}_path_outcome_analysis.json"].read_text(encoding="utf-8"))
        jumps[str(seed)] = row["summary"]["jump_change_count"]

    source_mismatches = []
    if stored["jump_counts"] != jumps:
        source_mismatches.append({"expected": jumps, "stored": stored["jump_counts"]})
    for name, path in source_paths.items():
        if stored["path_outcome_sources"].get(name) != sha(path):
            source_mismatches.append(f"hash:{name}")
    comparison = set(protocol["comparison_seed_values"])
    pairs = [(a, b) for a, b in itertools.combinations(range(8), 2) if not (a in comparison and b in comparison)]
    expected_records = []
    expected_summaries = []
    for candidate in candidates["candidate_metrics"]:
        metric = candidate["metric"]
        direction = candidate["direction"]
        local = []
        for pair_index, (a, b) in enumerate(pairs, start=1):
            jump_delta = jumps[str(b)] - jumps[str(a)]
            value_a = candidate["values"][str(a)]
            value_b = candidate["values"][str(b)]
            candidate_delta = value_b - value_a
            informative = jump_delta != 0
            expected_sign = sign(jump_delta) if direction == "same_as_jump_changes" else -sign(jump_delta)
            actual_sign = sign(candidate_delta)
            consistent = (actual_sign == expected_sign and actual_sign != 0) if informative else None
            reason = "uninformative_jump_tie" if not informative else "direction_consistent" if consistent else "candidate_tie_not_strict" if actual_sign == 0 else "direction_inconsistent"
            row = {
                "evaluation_index": len(expected_records) + 1, "pair_index": pair_index,
                "metric": metric, "level": candidate["level"], "direction": direction,
                "seed_a": a, "seed_b": b, "jump_a": jumps[str(a)], "jump_b": jumps[str(b)],
                "jump_delta": jump_delta, "value_a": value_a, "value_b": value_b,
                "candidate_delta": candidate_delta, "informative": informative,
                "expected_sign": expected_sign if informative else 0, "actual_sign": actual_sign,
                "consistent": consistent, "reason": reason,
            }
            expected_records.append(row)
            local.append(row)
        informative_rows = [row for row in local if row["informative"]]
        consistent_count = sum(row["consistent"] is True for row in informative_rows)
        inconsistent_count = sum(row["consistent"] is False for row in informative_rows)
        all_consistent = bool(informative_rows) and inconsistent_count == 0
        expected_summaries.append({
            "metric": metric, "level": candidate["level"], "direction": direction,
            "consistent_pair_count": consistent_count,
            "inconsistent_pair_count": inconsistent_count,
            "uninformative_pair_count": sum(not row["informative"] for row in local),
            "candidate_tie_count": sum(row["actual_sign"] == 0 for row in informative_rows),
            "all_informative_pairs_consistent": all_consistent,
            "assessment": "all_informative_pairs_consistent" if all_consistent else "not_all_informative_pairs_consistent",
        })

    pair_mismatches = []
    max_value_error = 0.0
    for index, (expected, actual) in enumerate(zip(expected_records, stored["pair_evaluations"])):
        mismatch = False
        for field, value in expected.items():
            if field in ("value_a", "value_b", "candidate_delta"):
                error = abs(float(actual[field]) - float(value))
                max_value_error = max(max_value_error, error)
                mismatch = mismatch or error != 0.0
            elif actual.get(field) != value:
                mismatch = True
        if mismatch:
            pair_mismatches.append(index)
    summary_mismatches = []
    for expected, actual in zip(expected_summaries, stored["candidate_summaries"]):
        if expected != actual:
            summary_mismatches.append(expected["metric"])
    informative_count = sum(row["informative"] for row in expected_records[:25])
    result = {
        "schema": "floquet-bdg-holdout-pair-evaluation-independent-v1",
        "protocol_sha256": sha(PROTOCOL), "analysis_sha256": sha(DATA),
        "candidate_source_analysis_sha256": sha(CANDIDATES),
        "candidate_count": len(expected_summaries), "pair_record_count": len(expected_records),
        "informative_pair_count": informative_count,
        "uninformative_pair_count": len(pairs) - informative_count,
        "all_informative_pairs_consistent_count": sum(row["all_informative_pairs_consistent"] for row in expected_summaries),
        "source_outcome_mismatch_count": len(source_mismatches),
        "pair_record_mismatch_count": len(pair_mismatches),
        "summary_mismatch_count": len(summary_mismatches),
        "max_value_absolute_error": max_value_error,
        "source_mismatches": source_mismatches,
        "pair_mismatch_indices": pair_mismatches,
        "summary_mismatches": summary_mismatches,
        "new_floquet_spectra_recomputed": False,
        "new_floquet_cells_computed": 0,
        "predictive_model_fitted": False,
        "correlation_computed": False,
        "p_values_computed": False,
    }
    result["all_passed"] = (
        stored["protocol_sha256"] == sha(PROTOCOL)
        and stored["candidate_source_analysis_sha256"] == sha(CANDIDATES)
        and len(expected_summaries) == 16 and len(expected_records) == 400
        and len(stored["pair_evaluations"]) == 400 and len(stored["candidate_summaries"]) == 16
        and informative_count == 20 and len(pairs) - informative_count == 5
        and not source_mismatches and not pair_mismatches and not summary_mismatches
        and max_value_error == 0.0
        and stored["unfiltered_pair_record_count"] == 400
        and stored["all_preregistered_results_retained"]
        and not stored["failed_pairs_removed"] and not stored["tie_pairs_removed"]
        and stored["directional_screen_completed"] and stored["candidate_evaluation_completed"]
        and not stored["predictive_validation_completed"] and stored["pair_evaluation_is_not_prediction"]
        and not stored["pristine_external_holdout_claim"] and not stored["predictive_model_fitted"]
        and not stored["correlation_claim"] and not stored["predictive_accuracy_computed"]
        and not stored["statistical_significance_claim"] and stored["new_floquet_cells_computed"] == 0
    )
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["all_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
