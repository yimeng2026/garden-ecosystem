"""Verify overlap-matrix response decomposition and its reviewed Word artifact."""

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
DOCX = ROOT / "Floquet-BdG-重叠矩阵响应分解.docx"


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
    analysis_command = [sys.executable, str(ROOT / "analyze_overlap_matrix_response.py")]
    if check_only:
        analysis_command.append("--check-only")
    commands = [
        ("overlap_matrix_response_evidence_binding" if check_only else "overlap_matrix_response_analysis", analysis_command),
        ("overlap_matrix_response_independent_recheck", [sys.executable, str(ROOT / "verify_overlap_matrix_response.py")]),
        ("docx_gate", [sys.executable, str(DOCX_PY), "validate", str(DOCX)]),
        ("visual_hash_binding", [sys.executable, str(ROOT / "record_overlap_matrix_response_qa.py")]),
        ("report_contracts", [sys.executable, str(ROOT / "test_overlap_matrix_response.py"), "-v"]),
    ]
    rows, logs = [], []
    for label, command in commands:
        completed = subprocess.run(command, cwd=WORKTREE, env=env, text=True, encoding="utf-8", capture_output=True, timeout=180)
        output = completed.stdout + completed.stderr
        logs.extend([f"$ {label}: {' '.join(command)}", output.rstrip(), f"exit_code={completed.returncode}"])
        rows.append({"label": label, "command": command, "exit_code": completed.returncode})
        if completed.returncode != 0:
            break
    qa = json.loads((ROOT / "overlap-matrix-response-word-qa.json").read_text(encoding="utf-8"))
    independent = json.loads((ROOT / "overlap_matrix_response_independent.json").read_text(encoding="utf-8"))
    data = json.loads((ROOT / "overlap_matrix_response_analysis.json").read_text(encoding="utf-8"))
    summary = data["summary"]
    passed = (
        len(rows) == len(commands) and all(row["exit_code"] == 0 for row in rows)
        and independent.get("all_passed", False)
        and independent.get("method_grid_transition_count") == 48
        and independent.get("entry_transition_count") == 192
        and independent.get("singular_channel_transition_count") == 384
        and independent.get("representation_delta_comparison_count") == 96
        and independent.get("max_delta_absolute_error") <= 1e-15
        and independent.get("max_singular_delta_absolute_error") <= 1e-15
        and independent.get("max_ratio_absolute_error") <= 1e-12
        and independent.get("max_log2_ratio_absolute_error") <= 1e-12
        and independent.get("driver_mismatch_count") == 0
        and independent.get("agreement_mismatch_count") == 0
        and independent.get("source_independent_rechecks_all_passed") is True
        and not independent.get("new_floquet_spectra_recomputed", True)
        and qa.get("visualReview", {}).get("status") == "passed"
        and qa.get("visualReview", {}).get("pagesReviewed") == 5
        and qa.get("visualReview", {}).get("contactSheetRead") is True
        and qa.get("visualReview", {}).get("docxSha256") == sha(DOCX)
        and len(data["method_grid_transitions"]) == 48
        and len(data["entry_transitions"]) == 192
        and len(data["entry_summary"]) == 24
        and len(data["representation_delta_agreements"]) == 96
        and data["new_floquet_cells_computed"] == 0 and data["new_seed_count"] == 0
        and data["source_independent_rechecks_all_passed"]
        and summary["representation_sign_agreement_count"] + summary["representation_sign_disagreement_count"] == 96
        and data["all_preregistered_results_retained"]
        and not data["normalization_correction_applied"] and not data["representation_invariant_claim"]
        and not data["causal_mechanism_proven"] and not data["statistical_significance_claim"]
        and not data["universal_size_law_claim"] and not data["continuous_path_proof"]
        and not data["spectral_crossing_proven"] and not data["state_exchange_proven"]
        and not data["thermodynamic_limit_proof"] and not data["new_taxonomy_claim"]
        and not data["new_winding_computed"] and not data["n640_computed"]
        and data["old_candidate_is_different_realization"] and data["difference_from_original_is_not_size_effect"]
        and all(data[f"batch_{name}_analysis_sha256"] == sha(ROOT / f"matched_beta_batch_{name}_analysis.json") for name in ("a", "b", "c"))
    )
    (ROOT / "overlap_matrix_response_run.log").write_text("\n".join(logs) + "\n", encoding="utf-8")
    artifacts = [
        "overlap_matrix_response_protocol.json", "overlap_matrix_response_analysis.json", "overlap_matrix_response_independent.json",
        "overlap-matrix-response.png", "OVERLAP_MATRIX_RESPONSE.md", "Floquet-BdG-重叠矩阵响应分解.docx",
        "overlap-matrix-response-word-qa.json", "overlap-matrix-response-word-render/report.json", "overlap_matrix_response_verification.json",
        "overlap_matrix_response_run.log", "analyze_overlap_matrix_response.py", "verify_overlap_matrix_response.py",
        "build_overlap_matrix_response_report.js", "record_overlap_matrix_response_qa.py", "test_overlap_matrix_response.py",
        "run_overlap_matrix_response_verification.py", "matched_beta_batch_a_analysis.json", "matched_beta_batch_b_analysis.json",
        "matched_beta_batch_c_analysis.json", "matched_beta_batch_a_independent.json", "matched_beta_batch_b_independent.json",
        "matched_beta_batch_c_independent.json", "swap_candidate_spectrum_analysis.json",
    ]
    record = {
        "schema": "floquet-bdg-overlap-matrix-response-verification-v1",
        "recorded_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "all_passed": passed, "test_count": 8 if passed else None, "check_only": check_only,
        "independent_recheck_passed": independent.get("all_passed"),
        "independent_max_delta_absolute_error": independent.get("max_delta_absolute_error"),
        "independent_max_singular_delta_absolute_error": independent.get("max_singular_delta_absolute_error"),
        "independent_max_ratio_absolute_error": independent.get("max_ratio_absolute_error"),
        "visual_review_status": qa.get("visualReview", {}).get("status"),
        "rendered_pages": qa.get("visualReview", {}).get("pagesReviewed"),
        "commands": rows,
        "sha256": {name: sha(ROOT / name) for name in artifacts if (ROOT / name).exists()},
        "scope": {
            "overlap_matrix_response_analysis_evaluated": passed,
            "method_grid_transitions": 48, "entry_transitions": 192,
            "singular_channel_transitions": 384, "representation_delta_comparisons": 96,
            "new_floquet_cells_computed": 0,
            "method_grid_assignment_change_count": summary["method_grid_assignment_change_count"],
            "representation_sign_agreement_count": summary["representation_sign_agreement_count"],
            "representation_sign_disagreement_count": summary["representation_sign_disagreement_count"],
            "entry_ratio_range_by_method": summary["entry_ratio_range_by_method"],
            "high_strength_controls": summary["high_strength_controls"],
            "near_zero_denominator_caution_required": True,
            "normalization_correction_applied": False,
            "representation_invariant_claim": False,
            "causal_mechanism_proven": False,
            "statistical_significance_claim": False,
            "universal_size_law_claim": False, "continuous_path_proof": False,
            "spectral_crossing_proven": False, "state_exchange_proven": False,
            "new_winding_computed": False, "n640_computed": False,
            "thermodynamic_limit_proof": False,
            "old_candidate_is_different_realization": True,
            "difference_from_original_is_not_size_effect": True,
        },
        "log": "overlap_matrix_response_run.log",
    }
    (ROOT / "overlap_matrix_response_verification.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("\n".join(logs))
    print("overlap_matrix_response_overall", "passed" if passed else "failed", "check_only", check_only)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
