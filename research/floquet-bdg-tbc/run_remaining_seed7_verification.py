"""Verify seed-7 outcomes, independent reconstruction and reviewed native Word."""

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
DATA = ROOT / "remaining_seed7_path_outcome_analysis.json"
DOCX = ROOT / "Floquet-BdG-seed7-剩余种子路径结局.docx"


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
    analysis_command = [sys.executable, str(ROOT / "analyze_remaining_seed_outcome.py"), "--seed", "7"]
    if check_only:
        analysis_command.append("--check-only")
    commands = [
        ("remaining_seed7_outcome_binding" if check_only else "remaining_seed7_outcome_analysis", analysis_command),
        ("remaining_seed7_independent_recheck", [sys.executable, str(ROOT / "verify_remaining_seed_outcome.py"), "--seed", "7"]),
        ("docx_gate", [sys.executable, str(DOCX_PY), "validate", str(DOCX)]),
        ("visual_hash_binding", [sys.executable, str(ROOT / "record_remaining_seed_outcome_qa.py"), "--seed", "7"]),
        ("report_contracts", [sys.executable, str(ROOT / "test_remaining_seed7_outcome.py"), "-v"]),
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
    independent = json.loads((ROOT / "remaining_seed7_path_outcome_independent.json").read_text(encoding="utf-8"))
    qa = json.loads((ROOT / "remaining-seed7-outcome-word-qa.json").read_text(encoding="utf-8"))
    endpoint = data["endpoint_binding"]
    passed = (
        len(rows) == len(commands) and all(row["exit_code"] == 0 for row in rows)
        and independent.get("all_passed", False)
        and independent.get("seed") == 7 and independent.get("cell_count") == 26
        and independent.get("cross_size_path_matrix_count") == 78
        and independent.get("native_adjacent_link_count") == 24
        and independent.get("entry_link_count") == 288
        and independent.get("jump_change_count") == data["summary"]["jump_change_count"]
        and independent.get("driver_comparison_change_count") == data["summary"]["driver_comparison_change_count"]
        and independent.get("max_master_absolute_error") == 0.0
        and independent.get("max_beta_absolute_error") == 0.0
        and independent.get("max_spectrum_absolute_error") == 0.0
        and independent.get("max_matrix_absolute_error") <= 1e-12
        and independent.get("max_singular_absolute_error") <= 1e-12
        and independent.get("max_entry_delta_absolute_error") <= 1e-12
        and independent.get("max_native_link_absolute_error") <= 1e-12
        and independent.get("max_representation_fidelity_absolute_error") <= 1e-12
        and independent.get("jump_outcome_mismatch_count") == 0
        and independent.get("driver_outcome_mismatch_count") == 0
        and independent.get("entry_driver_mismatch_count") == 0
        and independent.get("additional_unregistered_floquet_spectra") == 0
        and not independent.get("new_floquet_spectra_recomputed")
        and not independent.get("candidate_evaluation_performed")
        and qa.get("visualReview", {}).get("status") == "passed"
        and qa.get("visualReview", {}).get("pagesReviewed") == 4
        and qa.get("visualReview", {}).get("contactSheetRead") is True
        and qa.get("visualReview", {}).get("nearBlankPages") == []
        and qa.get("visualReview", {}).get("clippedPages") == []
        and qa.get("visualReview", {}).get("docxSha256") == sha(DOCX)
        and endpoint["max_matrix_absolute_error"] <= 1e-12
        and endpoint["max_singular_absolute_error"] <= 1e-12
        and endpoint["max_spectrum_absolute_error"] <= 1e-12
        and data["seed"] == 7 and len(data["cells"]) == 26 and len(data["path_matrices"]) == 78
        and len(data["links"]) == 24 and len(data["entry_links"]) == 288
        and len(data["jump_comparisons"]) == 8 and len(data["driver_comparisons"]) == 4
        and data["new_control_cells"] == 26 and data["new_floquet_cells_computed"] == 26
        and data["new_path_seed_count"] == 1 and data["new_disorder_realization_count"] == 0
        and data["all_preregistered_results_retained"] and data["candidate_evaluation_deferred"]
        and not data["candidate_validation_completed"] and data["holdout_pair_evaluations"] == []
        and not data["pristine_external_holdout_claim"] and not data["predictive_model_fitted"]
        and not data["correlation_claim"] and not data["statistical_significance_claim"]
        and not data["causal_mechanism_proven"] and not data["continuous_path_proof"]
        and not data["spectral_crossing_proven"] and not data["state_exchange_proven"]
        and not data["new_taxonomy_claim"] and not data["new_winding_computed"] and not data["n640_computed"]
        and data["protocol_sha256"] == sha(ROOT / "remaining_seed_outcome_protocol.json")
        and data["candidate_source_analysis_sha256"] == sha(ROOT / "profile_stat_candidates_analysis.json")
        and data["batch_b_analysis_sha256"] == sha(ROOT / "matched_beta_batch_b_analysis.json")
        and data["batch_c_analysis_sha256"] == sha(ROOT / "matched_beta_batch_c_analysis.json")
        and all((ROOT / f"remaining_seed{seed}_path_outcome_analysis.json").is_file() for seed in (2, 3, 4, 5))
    )
    (ROOT / "remaining_seed7_outcome_run.log").write_text("\n".join(logs) + "\n", encoding="utf-8")
    artifacts = [
        "remaining_seed_outcome_protocol.json", "remaining_seed7_path_outcome_analysis.json", "remaining_seed7_path_outcome_independent.json",
        "remaining-seed7-outcome.png", "REMAINING_SEED7_OUTCOME.md", DOCX.name,
        "remaining-seed7-outcome-word-qa.json", "remaining-seed7-outcome-word-render/report.json", "remaining_seed7_outcome_verification.json",
        "remaining_seed7_outcome_run.log", "analyze_remaining_seed_outcome.py", "verify_remaining_seed_outcome.py",
        "build_remaining_seed_outcome_report.js", "record_remaining_seed_outcome_qa.py", "test_remaining_seed7_outcome.py",
        "run_remaining_seed7_verification.py",
    ]
    record = {
        "schema": "floquet-bdg-remaining-seed7-outcome-verification-v1",
        "recorded_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "all_passed": passed, "test_count": 8 if passed else None, "check_only": check_only,
        "independent_recheck_passed": independent.get("all_passed"),
        "independent_max_matrix_absolute_error": independent.get("max_matrix_absolute_error"),
        "independent_max_entry_delta_absolute_error": independent.get("max_entry_delta_absolute_error"),
        "independent_max_native_link_absolute_error": independent.get("max_native_link_absolute_error"),
        "visual_review_status": qa.get("visualReview", {}).get("status"),
        "rendered_pages": qa.get("visualReview", {}).get("pagesReviewed"),
        "commands": rows,
        "sha256": {name: sha(ROOT / name) for name in artifacts if (ROOT / name).exists()},
        "scope": {
            "remaining_seed7_outcome_analysis_evaluated": passed,
            "seed": 7, "completed_remaining_outcome_seeds": [2, 3, 4, 5, 7],
            "remaining_outcome_seeds_pending": [],
            "all_remaining_path_outcomes_exist": True,
            "new_control_cells": 26, "cross_size_path_matrices": 78,
            "native_adjacent_links": 24, "entry_links": 288,
            "jump_change_count": data["summary"]["jump_change_count"],
            "driver_comparison_change_count": data["summary"]["driver_comparison_change_count"],
            "new_extrema_midpoint_count": data["summary"]["new_extrema_midpoint_count"],
            "new_disorder_realization_count": 0,
            "candidate_evaluation_deferred": True, "candidate_validation_completed": False,
            "holdout_pair_evaluations": [], "pristine_external_holdout_claim": False,
            "predictive_model_fitted": False, "correlation_claim": False,
            "statistical_significance_claim": False, "causal_mechanism_proven": False,
            "continuous_path_proof": False, "spectral_crossing_proven": False,
            "state_exchange_proven": False, "new_winding_computed": False, "n640_computed": False,
            "new_taxonomy_claim": False,
        },
        "log": "remaining_seed7_outcome_run.log",
    }
    (ROOT / "remaining_seed7_outcome_verification.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("\n".join(logs))
    print("remaining_seed7_outcome_overall", "passed" if passed else "failed", "check_only", check_only)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
