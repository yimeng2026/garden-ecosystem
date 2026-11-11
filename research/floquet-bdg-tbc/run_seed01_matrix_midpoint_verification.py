"""Verify cross-seed midpoint paths, endpoint bindings and reviewed Word artifact."""

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
DOCX = ROOT / "Floquet-BdG-跨种子跳变窗口中点对照.docx"


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
    analysis_command = [sys.executable, str(ROOT / "analyze_seed01_matrix_midpoint.py")]
    if check_only:
        analysis_command.append("--check-only")
    commands = [
        ("seed01_matrix_midpoint_evidence_binding" if check_only else "seed01_matrix_midpoint_analysis", analysis_command),
        ("seed01_matrix_midpoint_independent_recheck", [sys.executable, str(ROOT / "verify_seed01_matrix_midpoint.py")]),
        ("docx_gate", [sys.executable, str(DOCX_PY), "validate", str(DOCX)]),
        ("visual_hash_binding", [sys.executable, str(ROOT / "record_seed01_matrix_midpoint_qa.py")]),
        ("report_contracts", [sys.executable, str(ROOT / "test_seed01_matrix_midpoint.py"), "-v"]),
    ]
    rows, logs = [], []
    for label, command in commands:
        completed = subprocess.run(command, cwd=WORKTREE, env=env, text=True, encoding="utf-8", capture_output=True, timeout=180)
        output = completed.stdout + completed.stderr
        logs.extend([f"$ {label}: {' '.join(command)}", output.rstrip(), f"exit_code={completed.returncode}"])
        rows.append({"label": label, "command": command, "exit_code": completed.returncode})
        if completed.returncode != 0:
            break
    qa = json.loads((ROOT / "seed01-matrix-midpoint-word-qa.json").read_text(encoding="utf-8"))
    independent = json.loads((ROOT / "seed01_matrix_midpoint_independent.json").read_text(encoding="utf-8"))
    data = json.loads((ROOT / "seed01_matrix_midpoint_analysis.json").read_text(encoding="utf-8"))
    summary = data["summary"]
    endpoint = data["endpoint_binding"]
    passed = (
        len(rows) == len(commands) and all(row["exit_code"] == 0 for row in rows)
        and independent.get("all_passed", False)
        and independent.get("cell_count") == 52
        and independent.get("cross_size_path_matrix_count") == 156
        and independent.get("native_adjacent_link_count") == 48
        and independent.get("entry_link_count") == 576
        and independent.get("max_coarsening_absolute_error") == 0
        and independent.get("max_spectrum_absolute_error") <= 1e-12
        and independent.get("max_pair_center_absolute_error") <= 1e-12
        and independent.get("max_matrix_absolute_error") <= 1e-12
        and independent.get("max_singular_absolute_error") <= 1e-12
        and independent.get("max_entry_delta_absolute_error") <= 1e-12
        and independent.get("max_native_link_absolute_error") <= 1e-12
        and independent.get("max_representation_fidelity_absolute_error") <= 1e-12
        and independent.get("driver_mismatch_count") == 0
        and independent.get("endpoint_binding", {}).get("max_matrix_absolute_error") <= 1e-12
        and independent.get("endpoint_binding", {}).get("max_singular_absolute_error") <= 1e-12
        and independent.get("endpoint_binding", {}).get("max_spectrum_absolute_error") <= 1e-12
        and qa.get("visualReview", {}).get("status") == "passed"
        and qa.get("visualReview", {}).get("pagesReviewed") == 5
        and qa.get("visualReview", {}).get("contactSheetRead") is True
        and qa.get("visualReview", {}).get("docxSha256") == sha(DOCX)
        and len(data["cells"]) == 52 and len(data["path_matrices"]) == 156
        and len(data["links"]) == 48 and len(data["method_grid_links"]) == 144
        and len(data["entry_links"]) == 576 and len(data["entry_extrema"]) == 16
        and len(data["original_entry_extrema"]) == 16 and len(data["jump_comparisons"]) == 16
        and len(data["driver_comparisons"]) == 8 and len(data["cross_seed_extremum_agreement"]) == 8
        and len(data["representation_fidelity"]) == 312 and len(data["rank_controls"]) == 364
        and data["new_control_cells"] == 52 and data["evaluated_control_cells"] == 52
        and data["not_merged_into_batch_counts"] and not data["reference_seed6_recomputed"]
        and data["new_seed_count"] == 0 and data["all_preregistered_results_retained"]
        and summary["max_direction_absolute_error"] <= 1e-12
        and summary["max_representation_direction_absolute_error"] <= 1e-12
        and summary["max_native_off_diagonal"] <= 1e-12
        and summary["max_cell_average_off_diagonal"] <= 1e-12
        and endpoint["max_matrix_absolute_error"] <= 1e-12
        and endpoint["max_singular_absolute_error"] <= 1e-12
        and endpoint["max_spectrum_absolute_error"] <= 1e-12
        and not data["normalization_correction_applied"] and not data["representation_invariant_claim"]
        and not data["statistical_significance_claim"] and not data["continuous_path_proof"]
        and not data["spectral_crossing_proven"] and not data["avoided_crossing_claim"]
        and not data["state_exchange_proven"] and not data["causal_mechanism_proven"]
        and not data["thermodynamic_limit_proof"] and not data["new_taxonomy_claim"]
        and not data["new_winding_computed"] and not data["n640_computed"]
        and data["old_candidate_is_different_realization"] and data["difference_from_original_is_not_size_effect"]
        and data["reference_seed6_analysis_sha256"] == sha(ROOT / "seed6_matrix_midpoint_analysis.json")
        and data["batch_a_analysis_sha256"] == sha(ROOT / "matched_beta_batch_a_analysis.json")
        and data["batch_c_analysis_sha256"] == sha(ROOT / "matched_beta_batch_c_analysis.json")
    )
    (ROOT / "seed01_matrix_midpoint_run.log").write_text("\n".join(logs) + "\n", encoding="utf-8")
    artifacts = [
        "seed01_matrix_midpoint_protocol.json", "seed01_matrix_midpoint_analysis.json", "seed01_matrix_midpoint_independent.json",
        "seed01-matrix-midpoint.png", "SEED01_MATRIX_MIDPOINT.md", "Floquet-BdG-跨种子跳变窗口中点对照.docx",
        "seed01-matrix-midpoint-word-qa.json", "seed01-matrix-midpoint-word-render/report.json", "seed01_matrix_midpoint_verification.json",
        "seed01_matrix_midpoint_run.log", "analyze_seed01_matrix_midpoint.py", "verify_seed01_matrix_midpoint.py",
        "build_seed01_matrix_midpoint_report.js", "record_seed01_matrix_midpoint_qa.py", "test_seed01_matrix_midpoint.py",
        "run_seed01_matrix_midpoint_verification.py", "seed6_matrix_midpoint_analysis.json",
        "matched_beta_batch_a_analysis.json", "matched_beta_batch_c_analysis.json",
    ]
    record = {
        "schema": "floquet-bdg-seed01-matrix-midpoint-verification-v1",
        "recorded_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "all_passed": passed, "test_count": 10 if passed else None, "check_only": check_only,
        "independent_recheck_passed": independent.get("all_passed"),
        "independent_max_spectrum_absolute_error": independent.get("max_spectrum_absolute_error"),
        "independent_max_matrix_absolute_error": independent.get("max_matrix_absolute_error"),
        "independent_max_entry_delta_absolute_error": independent.get("max_entry_delta_absolute_error"),
        "independent_max_native_link_absolute_error": independent.get("max_native_link_absolute_error"),
        "visual_review_status": qa.get("visualReview", {}).get("status"),
        "rendered_pages": qa.get("visualReview", {}).get("pagesReviewed"),
        "commands": rows,
        "sha256": {name: sha(ROOT / name) for name in artifacts if (ROOT / name).exists()},
        "scope": {
            "seed01_matrix_midpoint_analysis_evaluated": passed,
            "new_seed_paths": 2, "reference_seed": 6,
            "new_control_cells": 52, "cross_size_path_matrices": 156,
            "native_adjacent_links": 48, "entry_links": 576,
            "not_merged_into_batch_counts": True, "reference_seed6_recomputed": False,
            "cross_size_assignment_counts": summary["cross_size_assignment_counts"],
            "method_grid_assignment_change_count": summary["method_grid_assignment_change_count"],
            "summary_by_seed": data["summary_by_seed"],
            "same_min_strength_across_all_count": summary["same_min_strength_across_all_count"],
            "same_max_strength_across_all_count": summary["same_max_strength_across_all_count"],
            "same_max_jump_link_across_all_count": summary["same_max_jump_link_across_all_count"],
            "endpoint_binding": endpoint,
            "min_representation_fidelity": summary["min_representation_fidelity"],
            "max_representation_fidelity": summary["max_representation_fidelity"],
            "max_linear_point_off_diagonal": summary["max_linear_point_off_diagonal"],
            "max_cell_average_off_diagonal": summary["max_cell_average_off_diagonal"],
            "normalization_correction_applied": False, "representation_invariant_claim": False,
            "statistical_significance_claim": False, "continuous_path_proof": False,
            "spectral_crossing_proven": False, "avoided_crossing_claim": False,
            "state_exchange_proven": False, "causal_mechanism_proven": False,
            "new_winding_computed": False, "n640_computed": False,
            "thermodynamic_limit_proof": False,
            "old_candidate_is_different_realization": True,
            "difference_from_original_is_not_size_effect": True,
        },
        "log": "seed01_matrix_midpoint_run.log",
    }
    (ROOT / "seed01_matrix_midpoint_verification.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("\n".join(logs))
    print("seed01_matrix_midpoint_overall", "passed" if passed else "failed", "check_only", check_only)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
