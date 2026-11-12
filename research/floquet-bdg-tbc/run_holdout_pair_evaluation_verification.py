"""Verify all pair records, independent replay and the five-page native report."""

import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
WORKTREE = ROOT.parents[1]
CACHE = Path("D:/kimi-cache/tbc")
DOCX_PY = Path("C:/Users/一梦/AppData/Roaming/kimi-desktop/daimon-share/daimon/runtime/kimi-code/home/plugins/managed/kimi-word/skills/kimi-word/scripts/docx.py")
DATA = ROOT / "holdout_pair_evaluation_analysis.json"
DOCX = ROOT / "Floquet-BdG-剩余种子候选逐对方向检验.docx"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    check_only = "--check-only" in sys.argv
    env = os.environ.copy()
    env.update({
        "TMP": str(CACHE / "tmp"), "TEMP": str(CACHE / "tmp"),
        "PYTHONPYCACHEPREFIX": str(CACHE / "pycache"), "MPLCONFIGDIR": str(CACHE / "matplotlib"),
        "OPENBLAS_NUM_THREADS": "1", "OMP_NUM_THREADS": "1",
        "PATH": r"C:\Program Files\nodejs" + os.pathsep + env.get("PATH", ""),
    })
    analysis_command = [sys.executable, str(ROOT / "analyze_holdout_pair_evaluation.py")]
    if check_only:
        analysis_command.append("--check-only")
    commands = [
        ("holdout_pair_evaluation_binding" if check_only else "holdout_pair_evaluation_analysis", analysis_command),
        ("holdout_pair_independent_recheck", [sys.executable, str(ROOT / "verify_holdout_pair_evaluation.py")]),
        ("docx_gate", [sys.executable, str(DOCX_PY), "validate", str(DOCX)]),
        ("visual_hash_binding", [sys.executable, str(ROOT / "record_holdout_pair_evaluation_qa.py")]),
        ("report_contracts", [sys.executable, str(ROOT / "test_holdout_pair_evaluation.py"), "-v"]),
    ]
    rows, logs = [], []
    for label, command in commands:
        completed = subprocess.run(command, cwd=WORKTREE, env=env, text=True, encoding="utf-8", capture_output=True, timeout=240)
        output = completed.stdout + completed.stderr
        logs.extend([f"$ {label}: {' '.join(command)}", output.rstrip(), f"exit_code={completed.returncode}"])
        rows.append({"label": label, "command": command, "exit_code": completed.returncode})
        if completed.returncode != 0:
            break
    data = json.loads(DATA.read_text(encoding="utf-8"))
    independent = json.loads((ROOT / "holdout_pair_evaluation_independent.json").read_text(encoding="utf-8"))
    qa = json.loads((ROOT / "holdout-pair-evaluation-word-qa.json").read_text(encoding="utf-8"))
    consistent_names = [row["metric"] for row in data["candidate_summaries"] if row["all_informative_pairs_consistent"]]
    source_names = ["seed01_matrix_midpoint_analysis.json", "seed6_matrix_midpoint_analysis.json", *(f"remaining_seed{seed}_path_outcome_analysis.json" for seed in (2, 3, 4, 5, 7))]
    passed = (
        len(rows) == len(commands) and all(row["exit_code"] == 0 for row in rows)
        and independent.get("all_passed", False)
        and independent.get("candidate_count") == 16 and independent.get("pair_record_count") == 400
        and independent.get("informative_pair_count") == 20 and independent.get("uninformative_pair_count") == 5
        and independent.get("source_outcome_mismatch_count") == 0
        and independent.get("pair_record_mismatch_count") == 0
        and independent.get("summary_mismatch_count") == 0
        and independent.get("max_value_absolute_error") == 0.0
        and not independent.get("new_floquet_spectra_recomputed")
        and independent.get("all_informative_pairs_consistent_count") == len(consistent_names)
        and qa.get("visualReview", {}).get("status") == "passed"
        and qa.get("visualReview", {}).get("pagesReviewed") == 5
        and qa.get("visualReview", {}).get("contactSheetRead") is True
        and qa.get("visualReview", {}).get("nearBlankPages") == []
        and qa.get("visualReview", {}).get("clippedPages") == []
        and qa.get("visualReview", {}).get("docxSha256") == sha(DOCX)
        and data["candidate_count"] == 16 and data["pair_count_per_candidate"] == 25
        and data["unfiltered_pair_record_count"] == 400 and len(data["pair_evaluations"]) == 400
        and len(data["candidate_summaries"]) == 16
        and data["informative_pair_count"] == 20 and data["uninformative_pair_count"] == 5
        and data["training_only_pair_count_excluded"] == 3
        and data["jump_counts"] == {"0": 4, "1": 0, "2": 2, "3": 0, "4": 0, "5": 6, "6": 6, "7": 2}
        and data["all_remaining_path_outcomes_exist"] and data["all_preregistered_results_retained"]
        and not data["failed_pairs_removed"] and not data["tie_pairs_removed"]
        and data["directional_screen_completed"] and data["candidate_evaluation_completed"]
        and not data["predictive_validation_completed"] and data["pair_evaluation_is_not_prediction"]
        and not data["pristine_external_holdout_claim"] and not data["predictive_model_fitted"]
        and not data["correlation_claim"] and not data["predictive_accuracy_computed"]
        and not data["statistical_significance_claim"] and not data["causal_mechanism_proven"]
        and not data["continuous_path_proof"] and not data["spectral_crossing_proven"]
        and not data["state_exchange_proven"] and not data["new_taxonomy_claim"]
        and data["new_floquet_cells_computed"] == 0 and not data["new_winding_computed"] and not data["n640_computed"]
        and data["protocol_sha256"] == sha(ROOT / "remaining_seed_outcome_protocol.json")
        and data["candidate_source_analysis_sha256"] == sha(ROOT / "profile_stat_candidates_analysis.json")
        and all(data["path_outcome_sources"][name] == sha(ROOT / name) for name in source_names)
    )
    (ROOT / "holdout_pair_evaluation_run.log").write_text("\n".join(logs) + "\n", encoding="utf-8")
    artifacts = [
        "holdout_pair_evaluation_analysis.json", "holdout_pair_evaluation_independent.json",
        "holdout-pair-evaluation.png", "HOLDOUT_PAIR_EVALUATION.md", DOCX.name,
        "holdout-pair-evaluation-word-qa.json", "holdout-pair-evaluation-word-render/report.json", "holdout_pair_evaluation_verification.json",
        "holdout_pair_evaluation_run.log", "analyze_holdout_pair_evaluation.py", "verify_holdout_pair_evaluation.py",
        "build_holdout_pair_evaluation_report.js", "record_holdout_pair_evaluation_qa.py", "test_holdout_pair_evaluation.py",
        "run_holdout_pair_evaluation_verification.py",
    ]
    record = {
        "schema": "floquet-bdg-holdout-pair-evaluation-verification-v1",
        "recorded_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "all_passed": passed, "test_count": 8 if passed else None, "check_only": check_only,
        "independent_recheck_passed": independent.get("all_passed"),
        "independent_pair_record_mismatch_count": independent.get("pair_record_mismatch_count"),
        "independent_summary_mismatch_count": independent.get("summary_mismatch_count"),
        "visual_review_status": qa.get("visualReview", {}).get("status"),
        "rendered_pages": qa.get("visualReview", {}).get("pagesReviewed"),
        "commands": rows,
        "sha256": {name: sha(ROOT / name) for name in artifacts if (ROOT / name).exists()},
        "scope": {
            "holdout_pair_evaluation_analysis_evaluated": passed,
            "candidate_count": 16, "pair_count_per_candidate": 25,
            "unfiltered_pair_record_count": 400, "informative_pair_count": 20,
            "uninformative_pair_count": 5, "training_only_pair_count_excluded": 3,
            "all_informative_pairs_consistent_count": len(consistent_names),
            "all_informative_pairs_consistent_names": consistent_names,
            "candidate_consistency": {row["metric"]: [row["consistent_pair_count"], row["inconsistent_pair_count"]] for row in data["candidate_summaries"]},
            "failed_pairs_removed": False, "tie_pairs_removed": False,
            "directional_screen_completed": True, "candidate_evaluation_completed": True,
            "predictive_validation_completed": False, "pair_evaluation_is_not_prediction": True,
            "pristine_external_holdout_claim": False, "predictive_model_fitted": False,
            "correlation_claim": False, "predictive_accuracy_computed": False,
            "statistical_significance_claim": False, "causal_mechanism_proven": False,
            "new_floquet_cells_computed": 0, "new_floquet_spectra_recomputed": False,
            "new_winding_computed": False, "n640_computed": False, "new_taxonomy_claim": False,
        },
        "log": "holdout_pair_evaluation_run.log",
    }
    (ROOT / "holdout_pair_evaluation_verification.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("\n".join(logs))
    print("holdout_pair_evaluation_overall", "passed" if passed else "failed", "check_only", check_only)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
