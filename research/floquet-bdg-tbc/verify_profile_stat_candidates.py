"""Independent numerical and label recheck for profile-statistic candidates."""

import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "profile_stat_candidates_independent.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(name):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def master_statistics(x):
    d = np.diff(x)
    quantiles = {q: float(np.quantile(x, q)) for q in (0.01, 0.02, 0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95, 0.98, 0.99)}
    result = {
        "mean": float(np.mean(x)),
        "std": float(np.std(x, ddof=0)),
        "min": float(np.min(x)),
        "max": float(np.max(x)),
        "mad": float(np.median(np.abs(x - np.median(x)))),
        "iqr": quantiles[0.75] - quantiles[0.25],
        "low_frac_0p05": float(np.mean(x < 0.05)),
        "low_frac_0p1": float(np.mean(x < 0.1)),
        "low_frac_0p2": float(np.mean(x < 0.2)),
        "high_frac_0p8": float(np.mean(x > 0.8)),
        "high_frac_0p85": float(np.mean(x > 0.85)),
        "high_frac_0p9": float(np.mean(x > 0.9)),
        "high_frac_0p95": float(np.mean(x > 0.95)),
        "roughness_rms": float(np.sqrt(np.mean(d ** 2))),
        "total_variation": float(np.mean(np.abs(d))),
        "sign_changes": int(np.sum(np.signbit(d[1:]) != np.signbit(d[:-1]))),
    }
    result.update({f"q{int(q * 100):02d}": value for q, value in quantiles.items()})
    for lag in (1, 2, 3, 4):
        result[f"lag{lag}"] = float(np.corrcoef(x[:-lag], x[lag:])[0, 1])
    return result


def block_statistics(block):
    means = np.mean(block, axis=1)
    stds = np.std(block, axis=1, ddof=0)
    n = len(means)
    return {
        "block_mean_min": float(np.min(means)),
        "block_mean_max": float(np.max(means)),
        "block_mean_std": float(np.std(means, ddof=0)),
        "block_std_max": float(np.max(stds)),
        "block_std_mean": float(np.mean(stds)),
        "low_block_frac_0p1": float(np.mean(means < 0.1)),
        "high_block_frac_0p8": float(np.mean(means > 0.8)),
        "left_right_delta": float(np.mean(means[:n // 2]) - np.mean(means[n // 2:])),
        "endpoint_delta": float(means[0] - means[-1]),
    }


def direction(values):
    v = {int(seed): float(value) for seed, value in values.items()}
    if v[1] < v[0] < v[6]:
        return "same_as_jump_changes"
    if v[1] > v[0] > v[6]:
        return "opposite_to_jump_changes"
    return "unordered"


def unique_count(values):
    return len({round(float(value), 15) for value in values.values()})


def main():
    protocol = load("profile_stat_candidates_protocol.json")
    stored = load("profile_stat_candidates_analysis.json")
    source_maps = []
    for name in ("matched_beta_batch_a_analysis.json", "matched_beta_batch_b_analysis.json"):
        source_maps.append({int(row["seed"]): np.asarray(row["master_profile"], dtype=float) for row in load(name)["realizations"]})

    expected_profiles = {}
    expected_master_metrics = {}
    expected_block_metrics = {}
    expected_beta = {}
    max_master_error = 0.0
    max_beta_error = 0.0
    max_metric_error = 0.0
    source_mismatches = []
    profile_mismatches = []

    stored_profiles = {int(row["seed"]): row for row in stored["profiles"]}
    for seed in range(8):
        master = np.random.default_rng(20261111 + seed).random(4800)
        beta = {400: master.reshape(400, 12).mean(axis=1), 600: master.reshape(600, 8).mean(axis=1)}
        expected_profiles[seed] = master
        expected_beta[seed] = beta
        expected_master_metrics[seed] = master_statistics(master)
        expected_block_metrics[seed] = {n: block_statistics(master.reshape(n, 4800 // n)) for n in (400, 600)}
        row = stored_profiles[seed]
        stored_master = np.asarray(row["master_profile"], dtype=float)
        master_error = float(np.max(np.abs(stored_master - master)))
        max_master_error = max(max_master_error, master_error)
        if not np.array_equal(stored_master, master):
            profile_mismatches.append(seed)
        if hashlib.sha256(master.tobytes()).hexdigest() != row["master_profile_sha256"]:
            source_mismatches.append(f"profile hash seed={seed}")
        containing_sources = [source for source in source_maps if seed in source]
        if len(containing_sources) != 1:
            source_mismatches.append(f"source count seed={seed}: {len(containing_sources)}")
        for source in containing_sources:
            if not np.array_equal(source[seed], master):
                source_mismatches.append(f"source profile seed={seed}")
        for n in (400, 600):
            error = float(np.max(np.abs(np.asarray(row[f"beta{n}"], dtype=float) - beta[n])))
            max_beta_error = max(max_beta_error, error)
        for metric in protocol["master_metrics"]:
            error = abs(float(row["master_metrics"][metric]) - expected_master_metrics[seed][metric])
            max_metric_error = max(max_metric_error, error)
        for n in (400, 600):
            for metric in protocol["block_metrics"]:
                error = abs(float(row["block_metrics"][f"n{n}"][metric]) - expected_block_metrics[seed][n][metric])
                max_metric_error = max(max_metric_error, error)

    expected_records = []
    for metric in protocol["master_metrics"]:
        values = {str(seed): expected_master_metrics[seed][metric] for seed in range(8)}
        expected_records.append({
            "metric": metric, "level": "master", "values": values,
            "unique_count": unique_count(values), "direction": direction(values),
            "coarsening_direction": "not_applicable",
        })
    for metric in protocol["block_metrics"]:
        values_by_n = {
            f"n{n}": {str(seed): expected_block_metrics[seed][n][metric] for seed in range(8)}
            for n in (400, 600)
        }
        directions = {level: direction(values) for level, values in values_by_n.items()}
        if directions["n400"] == directions["n600"] and directions["n400"] != "unordered":
            coarsening = "both_same"
        elif directions["n400"] != directions["n600"]:
            coarsening = "different"
        else:
            coarsening = "unordered"
        expected_records.append({
            "metric": metric, "level": "block", "values": values_by_n["n400"],
            "values_by_n": values_by_n, "unique_count": unique_count(values_by_n["n400"]),
            "direction": directions["n400"], "direction_by_n": directions,
            "coarsening_direction": coarsening,
        })
    for row in expected_records:
        row["candidate"] = row["unique_count"] >= 6 and row["direction"] != "unordered"

    stored_records = {(row["level"], row["metric"]): row for row in stored["metric_records"]}
    label_mismatches = []
    for expected in expected_records:
        key = (expected["level"], expected["metric"])
        actual = stored_records.get(key)
        if actual is None:
            label_mismatches.append(f"missing {key}")
            continue
        for field in ("unique_count", "direction", "coarsening_direction", "candidate"):
            if actual[field] != expected[field]:
                label_mismatches.append(f"{key} {field}: {actual[field]} != {expected[field]}")
        for level, values in (("values", expected["values"]),):
            for seed, value in values.items():
                error = abs(float(actual[level][seed]) - value)
                max_metric_error = max(max_metric_error, error)
        if expected["level"] == "block":
            for n, values in expected["values_by_n"].items():
                for seed, value in values.items():
                    error = abs(float(actual["values_by_n"][n][seed]) - value)
                    max_metric_error = max(max_metric_error, error)
            if actual["direction_by_n"] != expected["direction_by_n"]:
                label_mismatches.append(f"{key} direction_by_n")

    expected_candidates = [(row["level"], row["metric"]) for row in expected_records if row["candidate"]]
    stored_candidates = [(row["level"], row["metric"]) for row in stored["candidate_metrics"]]
    candidate_mismatches = []
    if expected_candidates != stored_candidates:
        candidate_mismatches.append({"expected": expected_candidates, "stored": stored_candidates})
    for row in stored["metric_records"]:
        if (row["level"], row["metric"]) not in {(r["level"], r["metric"]) for r in expected_records}:
            candidate_mismatches.append(f"unexpected record {row['level']} {row['metric']}")

    all_passed = (
        stored.get("protocol_sha256") == sha(ROOT / "profile_stat_candidates_protocol.json")
        and len(stored_profiles) == 8 and len(stored_records) == 40
        and not source_mismatches and not profile_mismatches
        and max_master_error == 0.0 and max_beta_error == 0.0
        and max_metric_error <= 1e-12 and not label_mismatches and not candidate_mismatches
        and stored["new_floquet_cells_computed"] == 0
        and not stored["predictive_model_fitted"]
        and not stored["correlation_claim"]
        and not stored["statistical_significance_claim"]
    )
    result = {
        "schema": "floquet-bdg-profile-stat-candidates-independent-v1",
        "protocol_sha256": sha(ROOT / "profile_stat_candidates_protocol.json"),
        "analysis_sha256": sha(ROOT / "profile_stat_candidates_analysis.json"),
        "profile_count": len(stored_profiles),
        "metric_record_count": len(stored_records),
        "candidate_count": len(stored_candidates),
        "candidate_names": [metric for _, metric in stored_candidates],
        "max_master_absolute_error": max_master_error,
        "max_beta_absolute_error": max_beta_error,
        "max_metric_absolute_error": max_metric_error,
        "source_mismatch_count": len(source_mismatches),
        "profile_mismatch_count": len(profile_mismatches),
        "label_mismatch_count": len(label_mismatches),
        "candidate_mismatch_count": len(candidate_mismatches),
        "source_mismatches": source_mismatches,
        "profile_mismatches": profile_mismatches,
        "label_mismatches": label_mismatches,
        "candidate_mismatches": candidate_mismatches,
        "new_floquet_spectra_recomputed": False,
        "predictive_model_fitted": False,
        "correlation_computed": False,
        "p_values_computed": False,
        "all_passed": all_passed,
    }
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if all_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
