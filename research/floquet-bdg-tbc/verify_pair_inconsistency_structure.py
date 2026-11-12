"""Independently recompute pair summaries, failure sets and all 120 overlaps."""

import hashlib
import itertools
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PROTOCOL = ROOT / "pair_inconsistency_structure_protocol.json"
SOURCE = ROOT / "holdout_pair_evaluation_analysis.json"
DATA = ROOT / "pair_inconsistency_structure_analysis.json"
OUT = ROOT / "pair_inconsistency_structure_independent.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    stored = json.loads(DATA.read_text(encoding="utf-8"))
    records = source["pair_evaluations"]
    metrics = [row["metric"] for row in source["candidate_summaries"]]
    informative_pairs = [(row["seed_a"], row["seed_b"]) for row in records[:25] if row["informative"]]
    pair_summaries = []
    for a, b in informative_pairs:
        local = [row for row in records if row["seed_a"] == a and row["seed_b"] == b]
        consistent_names = [row["metric"] for row in local if row["consistent"] is True]
        inconsistent_names = [row["metric"] for row in local if row["consistent"] is False]
        zero_names = [row["metric"] for row in local if row["actual_sign"] == 0]
        pair_summaries.append({
            "seed_a": a, "seed_b": b, "jump_a": local[0]["jump_a"], "jump_b": local[0]["jump_b"],
            "consistent_count": len(consistent_names), "inconsistent_count": len(inconsistent_names),
            "zero_diff_count": len(zero_names), "consistent_metric_names": consistent_names,
            "inconsistent_metric_names": inconsistent_names, "candidate_zero_diff_names": zero_names,
            "all_candidates_inconsistent": len(inconsistent_names) == 16,
            "all_candidates_consistent": len(inconsistent_names) == 0,
        })
    failure_sets = []
    lookup = {}
    for metric in metrics:
        local = [row for row in records if row["metric"] == metric and row["informative"]]
        failing = [[row["seed_a"], row["seed_b"]] for row in local if row["consistent"] is False]
        zero = [[row["seed_a"], row["seed_b"]] for row in local if row["actual_sign"] == 0]
        failure_sets.append({"metric": metric, "failing_pairs": failing, "zero_diff_pairs": zero})
        lookup[metric] = {tuple(pair) for pair in failing}
    spectrum = []
    for k in range(17):
        pairs = [[row["seed_a"], row["seed_b"]] for row in pair_summaries if row["inconsistent_count"] == k]
        spectrum.append({"inconsistent_candidate_count": k, "pair_count": len(pairs), "pairs": pairs})
    overlap = []
    for a, b in itertools.combinations(metrics, 2):
        set_a, set_b = lookup[a], lookup[b]
        shared = set_a & set_b
        union = set_a | set_b
        overlap.append({
            "metric_a": a, "metric_b": b,
            "intersection_count": len(shared), "union_count": len(union),
            "only_a_count": len(set_a - set_b), "only_b_count": len(set_b - set_a),
            "shared_pairs": [list(pair) for pair in sorted(shared)],
            "only_a_pairs": [list(pair) for pair in sorted(set_a - set_b)],
            "only_b_pairs": [list(pair) for pair in sorted(set_b - set_a)],
            "jaccard": len(shared) / len(union) if union else None,
        })
    closest = next(row for row in overlap if row["metric_a"] == "q99" and row["metric_b"] == "block_std_max")
    total = sum(row["inconsistent_pair_count"] for row in source["candidate_summaries"])
    mismatches = {
        "pair_summary_mismatch_count": int(pair_summaries != stored["pair_summaries"]),
        "failure_set_mismatch_count": sum(a != b for a, b in zip(failure_sets, stored["candidate_failure_sets"])),
        "overlap_mismatch_count": sum(a != b for a, b in zip(overlap, stored["overlap_records"])),
        "spectrum_mismatch_count": int(spectrum != stored["shared_failure_spectrum"]),
        "closest_comparison_mismatch_count": int(closest != stored["closest_candidate_comparison"]),
    }
    result = {
        "schema": "floquet-bdg-pair-inconsistency-structure-independent-v1",
        "protocol_sha256": sha(PROTOCOL), "analysis_sha256": sha(DATA),
        "source_pair_evaluation_sha256": sha(SOURCE),
        "pair_summary_count": len(pair_summaries), "overlap_record_count": len(overlap),
        "total_inconsistent_assignments": total,
        "all_candidates_inconsistent_pairs": [[row["seed_a"], row["seed_b"]] for row in pair_summaries if row["all_candidates_inconsistent"]],
        "all_candidates_consistent_pairs": [[row["seed_a"], row["seed_b"]] for row in pair_summaries if row["all_candidates_consistent"]],
        "max_pair_inconsistent_candidate_count": max(row["inconsistent_count"] for row in pair_summaries),
        "closest_candidate_comparison": closest,
        **mismatches,
        "new_floquet_spectra_recomputed": False,
        "new_floquet_cells_computed": 0,
        "predictive_model_fitted": False,
        "correlation_computed": False,
        "p_values_computed": False,
    }
    result["all_passed"] = (
        stored["protocol_sha256"] == sha(PROTOCOL)
        and stored["source_pair_evaluation_sha256"] == sha(SOURCE)
        and len(pair_summaries) == 20 and len(overlap) == 120 and total == 104
        and stored["total_inconsistent_assignments"] == total
        and len(stored["pair_summaries"]) == 20 and len(stored["overlap_records"]) == 120
        and len(stored["candidate_failure_sets"]) == 16
        and all(value == 0 for value in mismatches.values())
        and stored["source_records_unchanged"] and stored["all_preregistered_results_retained"]
        and not stored["strict_rule_changed"] and not stored["failed_pairs_removed"]
        and not stored["tie_pairs_removed"] and not stored["new_metric_proposed"]
        and not stored["ensemble_rule_proposed"] and stored["structure_is_descriptive_only"]
        and not stored["causal_attribution_completed"] and not stored["predictive_validation_completed"]
        and not stored["predictive_model_fitted"] and not stored["correlation_claim"]
        and not stored["predictive_accuracy_computed"] and not stored["statistical_significance_claim"]
        and stored["new_floquet_cells_computed"] == 0
    )
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["all_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
