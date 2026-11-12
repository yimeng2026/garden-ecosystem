"""Verify descriptive profile statistics, reviewed Word evidence and scope limits."""

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
DOCX = ROOT / "Floquet-BdG-无序剖面候选统计指标.docx"


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
    analysis_command = [sys.executable, str(ROOT / "analyze_profile_stat_candidates.py")]
    if check_only:
        analysis_command.append("--check-only")
    commands = [
        ("profile_stat_candidates_evidence_binding" if check_only else "profile_stat_candidates_analysis", analysis_command),
        ("profile_stat_candidates_independent_recheck", [sys.executable, str(ROOT / "verify_profile_stat_candidates.py")]),
        ("docx_gate", [sys.executable, str(DOCX_PY), "validate", str(DOCX)]),
        ("visual_hash_binding", [sys.executable, str(ROOT / "record_profile_stat_candidates_qa.py")]),
        ("report_contracts", [sys.executable, str(ROOT / "test_profile_stat_candidates.py"), "-v"]),
    ]
    rows, logs = [], []
    for label, command in commands:
        completed = subprocess.run(command, cwd=WORKTREE, env=env, text=True, encoding="utf-8", capture_output=True, timeout=180)
        output = completed.stdout + completed.stderr
        logs.extend([f"$ {label}: {' '.join(command)}", output.rstrip(), f"exit_code={completed.returncode}"])
        rows.append({"label": label, "command": command, "exit_code": completed.returncode})
        if completed.returncode != 0:
            break
    qa = json.loads((ROOT / "profile-stat-candidates-word-qa.json").read_text(encoding="utf-8"))
    independent = json.loads((ROOT / "profile_stat_candidates_independent.json").read_text(encoding="utf-8"))
    data = json.loads((ROOT / "profile_stat_candidates_analysis.json").read_text(encoding="utf-8"))
    protocol = json.loads((ROOT / "profile_stat_candidates_protocol.json").read_text(encoding="utf-8"))
    candidate_names = [row["metric"] for row in data["candidate_metrics"]]
    passed = (
        len(rows) == len(commands) and all(row["exit_code"] == 0 for row in rows)
        and independent.get("all_passed", False)
        and independent.get("profile_count") == 8
        and independent.get("metric_record_count") == 40
        and independent.get("candidate_count") == len(candidate_names)
        and independent.get("max_master_absolute_error") == 0.0
        and independent.get("max_beta_absolute_error") == 0.0
        and independent.get("max_metric_absolute_error") <= 1e-12
        and independent.get("source_mismatch_count") == 0
        and independent.get("profile_mismatch_count") == 0
        and independent.get("label_mismatch_count") == 0
        and independent.get("candidate_mismatch_count") == 0
        and not independent.get("new_floquet_spectra_recomputed")
        and qa.get("visualReview", {}).get("status") == "passed"
        and qa.get("visualReview", {}).get("pagesReviewed") == 5
        and qa.get("visualReview", {}).get("contactSheetRead") is True
        and qa.get("visualReview", {}).get("nearBlankPages") == []
        and qa.get("visualReview", {}).get("clippedPages") == []
        and qa.get("visualReview", {}).get("docxSha256") == sha(DOCX)
        and len(data["profiles"]) == 8 and len(data["metric_records"]) == 40
        and len(protocol["master_metrics"]) == 31 and len(protocol["block_metrics"]) == 9
        and data["path_jump_counts"] == {"0": 4, "1": 0, "6": 6}
        and data["path_driver_counts"] == {"0": 4, "1": 4, "6": 4}
        and data["new_floquet_cells_computed"] == 0 and data["new_seed_count"] == 0
        and data["all_preregistered_results_retained"]
        and not data["predictive_model_fitted"] and not data["correlation_claim"]
        and not data["statistical_significance_claim"] and not data["causal_mechanism_proven"]
        and not data["universal_size_law_claim"] and not data["thermodynamic_limit_proof"]
        and not data["new_taxonomy_claim"] and not data["categories_changed"]
        and not data["new_winding_computed"] and not data["n640_computed"]
        and data["protocol_sha256"] == sha(ROOT / "profile_stat_candidates_protocol.json")
        and data["seed01_analysis_sha256"] == sha(ROOT / "seed01_matrix_midpoint_analysis.json")
        and data["seed6_analysis_sha256"] == sha(ROOT / "seed6_matrix_midpoint_analysis.json")
        and data["batch_a_analysis_sha256"] == sha(ROOT / "matched_beta_batch_a_analysis.json")
        and data["batch_b_analysis_sha256"] == sha(ROOT / "matched_beta_batch_b_analysis.json")
    )
    (ROOT / "profile_stat_candidates_run.log").write_text("\n".join(logs) + "\n", encoding="utf-8")
    artifacts = [
        "profile_stat_candidates_protocol.json", "profile_stat_candidates_analysis.json", "profile_stat_candidates_independent.json",
        "profile-stat-candidates.png", "PROFILE_STAT_CANDIDATES.md", "Floquet-BdG-无序剖面候选统计指标.docx",
        "profile-stat-candidates-word-qa.json", "profile-stat-candidates-word-render/report.json", "profile_stat_candidates_verification.json",
        "profile_stat_candidates_run.log", "analyze_profile_stat_candidates.py", "verify_profile_stat_candidates.py",
        "build_profile_stat_candidates_report.js", "record_profile_stat_candidates_qa.py", "test_profile_stat_candidates.py",
        "run_profile_stat_candidates_verification.py",
    ]
    record = {
        "schema": "floquet-bdg-profile-stat-candidates-verification-v1",
        "recorded_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "all_passed": passed, "test_count": 8 if passed else None, "check_only": check_only,
        "independent_recheck_passed": independent.get("all_passed"),
        "independent_max_master_absolute_error": independent.get("max_master_absolute_error"),
        "independent_max_beta_absolute_error": independent.get("max_beta_absolute_error"),
        "independent_max_metric_absolute_error": independent.get("max_metric_absolute_error"),
        "visual_review_status": qa.get("visualReview", {}).get("status"),
        "rendered_pages": qa.get("visualReview", {}).get("pagesReviewed"),
        "commands": rows,
        "sha256": {name: sha(ROOT / name) for name in artifacts if (ROOT / name).exists()},
        "scope": {
            "profile_stat_candidates_analysis_evaluated": passed,
            "profile_count": 8, "metric_record_count": 40,
            "master_metric_count": 31, "block_metric_count": 9,
            "candidate_count": len(candidate_names), "candidate_names": candidate_names,
            "candidate_labels_are_exploratory_only": True,
            "remaining_seed_preregistration_required_before_use": True,
            "path_jump_counts": data["path_jump_counts"],
            "path_driver_counts": data["path_driver_counts"],
            "new_floquet_cells": 0, "new_seed_count": 0,
            "new_floquet_spectra_recomputed": False,
            "predictive_model_fitted": False, "correlation_claim": False,
            "statistical_significance_claim": False, "causal_mechanism_proven": False,
            "universal_size_law_claim": False, "thermodynamic_limit_proof": False,
            "new_winding_computed": False, "n640_computed": False,
            "new_taxonomy_claim": False, "categories_changed": False,
        },
        "log": "profile_stat_candidates_run.log",
    }
    (ROOT / "profile_stat_candidates_verification.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("\n".join(logs))
    print("profile_stat_candidates_overall", "passed" if passed else "failed", "check_only", check_only)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
