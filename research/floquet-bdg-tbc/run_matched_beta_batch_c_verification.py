"""Verify r=0.2 batch C, three-batch coverage and the reviewed Word artifact."""

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
DOCX = ROOT / "Floquet-BdG-共同无序剖面第三批高强度配对.docx"


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
    analysis_command = [sys.executable, str(ROOT / "analyze_matched_beta_batch_c.py")]
    if check_only:
        analysis_command.append("--check-only")
    commands = [
        ("matched_beta_batch_c_evidence_binding" if check_only else "matched_beta_batch_c_analysis", analysis_command),
        ("matched_beta_batch_c_independent_recheck", [sys.executable, str(ROOT / "verify_matched_beta_batch_c.py")]),
        ("docx_gate", [sys.executable, str(DOCX_PY), "validate", str(DOCX)]),
        ("visual_hash_binding", [sys.executable, str(ROOT / "record_matched_beta_batch_c_qa.py")]),
        ("report_contracts", [sys.executable, str(ROOT / "test_matched_beta_batch_c.py"), "-v"]),
    ]
    rows, logs = [], []
    for label, command in commands:
        completed = subprocess.run(command, cwd=WORKTREE, env=env, text=True, encoding="utf-8", capture_output=True, timeout=180)
        output = completed.stdout + completed.stderr
        logs.extend([f"$ {label}: {' '.join(command)}", output.rstrip(), f"exit_code={completed.returncode}"])
        rows.append({"label": label, "command": command, "exit_code": completed.returncode})
        if completed.returncode != 0:
            break
    qa = json.loads((ROOT / "matched-beta-batch-c-word-qa.json").read_text(encoding="utf-8"))
    independent = json.loads((ROOT / "matched_beta_batch_c_independent.json").read_text(encoding="utf-8"))
    data = json.loads((ROOT / "matched_beta_batch_c_analysis.json").read_text(encoding="utf-8"))
    summary = data["summary"]
    combined = data["combined_with_batches_a_b"]
    counts_complete = all(sum(summary["assignment_counts"][method].values()) == 24 for method in ("linear_point", "cell_average"))
    combined_counts_complete = all(sum(combined["assignment_counts"][method].values()) == 72 for method in ("linear_point", "cell_average"))
    passed = (
        len(rows) == len(commands) and all(row["exit_code"] == 0 for row in rows)
        and independent.get("all_passed", False)
        and independent.get("realization_count") == 8 and independent.get("cell_count") == 16
        and independent.get("new_rebuilt_cell_count") == 16 and independent.get("anchor_rechecked_cell_count") == 0
        and independent.get("max_master_profile_absolute_error") == 0
        and independent.get("max_coarsening_absolute_error") == 0
        and independent.get("max_spectrum_absolute_error") <= 1e-12
        and independent.get("max_pair_center_absolute_error") <= 1e-12
        and qa.get("visualReview", {}).get("status") == "passed"
        and qa.get("visualReview", {}).get("pagesReviewed") == 5
        and qa.get("visualReview", {}).get("contactSheetRead") is True
        and qa.get("visualReview", {}).get("docxSha256") == sha(DOCX)
        and len(data["realizations"]) == 8 and data["new_realization_count"] == 8
        and data["new_control_cells"] == 16 and data["reused_anchor_realizations_in_new_batch"] == 0
        and not data["prior_results_recomputed_for_pairing"]
        and data["max_coarsening_absolute_error"] == 0 and counts_complete
        and len(data["strength_pair_comparisons"]) == 8
        and all(row["identical_master_profile"] and row["from_strength"] == 0.1 and row["to_strength"] == 0.2 for row in data["strength_pair_comparisons"])
        and combined["realization_count"] == 24 and combined["control_cells"] == 48
        and combined["unique_seed_strength_keys"] and combined["reused_anchor_count"] == 1
        and combined_counts_complete
        and summary["max_direction_absolute_error"] <= 1e-12
        and summary["max_representation_direction_absolute_error"] <= 1e-12
        and summary["max_native_off_diagonal"] <= 1e-12
        and summary["max_cell_average_off_diagonal"] <= 1e-12
        and data["new_seed_count"] == 0 and data["all_preregistered_results_retained"]
        and data["common_disorder_profile_control_computed"]
        and data["size_effect_separated"] == "matched_nested_profile_descriptive_only"
        and data["old_candidate_is_different_realization"] and data["difference_from_original_is_not_size_effect"]
        and data["batch_a_analysis_sha256"] == sha(ROOT / "matched_beta_batch_a_analysis.json")
        and data["batch_b_analysis_sha256"] == sha(ROOT / "matched_beta_batch_b_analysis.json")
        and not data["normalization_correction_applied"] and not data["representation_invariant_claim"]
        and not data["universal_size_law_claim"] and not data["continuous_path_proof"]
        and not data["spectral_crossing_proven"] and not data["avoided_crossing_claim"]
        and not data["state_exchange_proven"] and not data["second_pair_topological_claim"]
        and not data["statistical_significance_claim"] and not data["thermodynamic_limit_proof"]
        and not data["new_taxonomy_claim"] and not data["new_winding_computed"] and not data["n640_computed"]
    )
    (ROOT / "matched_beta_batch_c_run.log").write_text("\n".join(logs) + "\n", encoding="utf-8")
    artifacts = [
        "matched_beta_batch_c_protocol.json", "matched_beta_batch_c_analysis.json", "matched_beta_batch_c_independent.json",
        "matched-beta-batch-c.png", "MATCHED_BETA_BATCH_C.md", "Floquet-BdG-共同无序剖面第三批高强度配对.docx",
        "matched-beta-batch-c-word-qa.json", "matched-beta-batch-c-word-render/report.json", "matched_beta_batch_c_verification.json",
        "matched_beta_batch_c_run.log", "analyze_matched_beta_batch_c.py", "verify_matched_beta_batch_c.py",
        "build_matched_beta_batch_c_report.js", "record_matched_beta_batch_c_qa.py", "test_matched_beta_batch_c.py",
        "run_matched_beta_batch_c_verification.py", "matched_beta_batch_a_analysis.json",
        "matched_beta_batch_b_analysis.json", "swap_candidate_spectrum_analysis.json",
    ]
    record = {
        "schema": "floquet-bdg-matched-beta-batch-c-verification-v1",
        "recorded_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "all_passed": passed, "test_count": 9 if passed else None, "check_only": check_only,
        "independent_recheck_passed": independent.get("all_passed"),
        "independent_max_spectrum_absolute_error": independent.get("max_spectrum_absolute_error"),
        "independent_max_pair_center_absolute_error": independent.get("max_pair_center_absolute_error"),
        "visual_review_status": qa.get("visualReview", {}).get("status"),
        "rendered_pages": qa.get("visualReview", {}).get("pagesReviewed"),
        "commands": rows,
        "sha256": {name: sha(ROOT / name) for name in artifacts if (ROOT / name).exists()},
        "scope": {
            "matched_beta_batch_c_analysis_evaluated": passed,
            "new_realizations": 8, "new_control_cells": 16,
            "reused_anchor_realizations_in_new_batch": 0,
            "combined_realizations": 24, "combined_control_cells": 48,
            "coarsening_max_absolute_error": 0,
            "assignment_counts": summary["assignment_counts"],
            "combined_assignment_counts": combined["assignment_counts"],
            "same_rank_all_grids_both_methods_count": summary["same_rank_all_grids_both_methods_count"],
            "method_agreement_all_grids_count": summary["method_agreement_all_grids_count"],
            "high_strength_summary": data["high_strength_summary"],
            "min_representation_fidelity": summary["min_representation_fidelity"],
            "max_representation_fidelity": summary["max_representation_fidelity"],
            "center_separation_delta_range": summary["center_separation_delta_range"],
            "combined_center_separation_delta_range": combined["center_separation_delta_range"],
            "prior_results_recomputed_for_pairing": False,
            "unique_combined_seed_strength_keys": True,
            "common_disorder_profile_control_computed": True,
            "size_effect_separated": "matched_nested_profile_descriptive_only",
            "old_candidate_is_different_realization": True,
            "difference_from_original_is_not_size_effect": True,
            "all_preregistered_results_retained": True,
            "normalization_correction_applied": False,
            "max_native_off_diagonal": summary["max_native_off_diagonal"],
            "max_cell_average_off_diagonal": summary["max_cell_average_off_diagonal"],
            "max_linear_point_off_diagonal": summary["max_linear_point_off_diagonal"],
            "universal_size_law_claim": False, "continuous_path_proof": False,
            "spectral_crossing_proven": False, "avoided_crossing_claim": False,
            "state_exchange_proven": False, "second_pair_topological_claim": False,
            "new_winding_computed": False, "n640_computed": False,
            "statistical_significance_claim": False, "thermodynamic_limit_proof": False,
        },
        "log": "matched_beta_batch_c_run.log",
    }
    (ROOT / "matched_beta_batch_c_verification.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("\n".join(logs))
    print("matched_beta_batch_c_overall", "passed" if passed else "failed", "check_only", check_only)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
