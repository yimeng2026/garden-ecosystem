"""Verify the full overlap-confounding audit and its reviewed native Word report."""

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
DOCX = ROOT / "Floquet-BdG-重叠差异混杂审计.docx"


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
    analysis_command = [sys.executable, str(ROOT / "analyze_overlap_confounding.py")]
    if check_only:
        analysis_command.append("--check-only")
    commands = [
        ("overlap_confounding_evidence_binding" if check_only else "overlap_confounding_analysis", analysis_command),
        ("native_rank_leakage_worst_case", [sys.executable, str(ROOT / "diagnose_same_n_rank_leakage.py")]),
        ("docx_gate", [sys.executable, str(DOCX_PY), "validate", str(DOCX)]),
        ("visual_hash_binding", [sys.executable, str(ROOT / "record_overlap_confounding_qa.py")]),
        ("report_contracts", [sys.executable, str(ROOT / "test_overlap_confounding.py"), "-v"]),
    ]
    rows, logs = [], []
    for label, command in commands:
        completed = subprocess.run(command, cwd=WORKTREE, env=env, text=True, encoding="utf-8", capture_output=True, timeout=180)
        output = completed.stdout + completed.stderr
        logs.extend([f"$ {label}: {' '.join(command)}", output.rstrip(), f"exit_code={completed.returncode}"])
        rows.append({"label": label, "command": command, "exit_code": completed.returncode})
        if completed.returncode != 0:
            break
    original = json.loads((ROOT / "multi_seed_independent.json").read_text(encoding="utf-8"))
    independent = json.loads((ROOT / "category_new_cells_independent.json").read_text(encoding="utf-8"))
    qa = json.loads((ROOT / "overlap-confounding-word-qa.json").read_text(encoding="utf-8"))
    data = json.loads((ROOT / "overlap_confounding_analysis.json").read_text(encoding="utf-8"))
    summary = data["summary"]
    passed = (
        len(rows) == len(commands) and all(row["exit_code"] == 0 for row in rows)
        and original.get("all_passed", False) and independent.get("all_passed", False)
        and qa.get("visualReview", {}).get("status") == "passed"
        and qa.get("visualReview", {}).get("pagesReviewed") == 4
        and qa.get("visualReview", {}).get("contactSheetRead") is True
        and len(data["cases"]) == 16 and len(data["cells"]) == 32
        and summary["method_grid_count"] == 96
        and summary["same_n_rank_control_count"] == 192
        and summary["native_same_n_rank_control_count"] == 32
        and summary["representation_fidelity_count"] == 192
        and summary["beta_profile_comparison_count"] == 96
        and summary["assignment_counts"] == {"diagonal": 90, "swapped": 6}
        and data["max_cross_size_reproduction_error"] <= 1e-12
        and data["max_profile_absolute_error"] <= 1e-10
        and summary["max_same_n_self_error"] <= 1e-12
        and abs(summary["max_same_n_off_diagonal"] - 3.2111372980829987e-06) < 1e-17
        and summary["max_native_same_n_off_diagonal"] <= 1e-12
        and summary["max_cell_average_same_n_off_diagonal"] <= 1e-12
        and summary["max_linear_point_same_n_off_diagonal"] > 1e-12
        and data["same_n_embedding_rank_gate_passed"] is False
        and data["native_control_added_after_observed_leakage"] is True
        and summary["max_representation_direction_absolute_error"] <= 1e-12
        and abs(summary["min_representation_fidelity"] - 0.9872555832052331) < 1e-12
        and abs(summary["max_representation_fidelity"] - 0.995831326702762) < 1e-12
        and abs(summary["min_beta_rms_absolute_difference"] - 0.3135955056912623) < 1e-12
        and abs(summary["max_beta_rms_absolute_difference"] - 0.42817819353493874) < 1e-12
        and abs(summary["max_absolute_beta_pearson_correlation"] - 0.09818342371891696) < 1e-12
        and summary["beta_rms_below_0p1_count"] == 0
        and data["new_physics_cells"] == 0 and data["new_seed_count"] == 0
        and not data["new_winding_computed"] and not data["n640_computed"]
        and not data["normalization_correction_applied"] and not data["size_effect_separated"]
        and not data["same_disorder_realization"] and not data["common_disorder_profile_control_computed"]
        and not data["representation_invariant_claim"] and not data["same_physics_state_tracking_claim"]
        and not data["rank_exchange_proven"] and not data["second_pair_topological_claim"]
        and not data["new_taxonomy_claim"] and not data["statistical_significance_claim"]
        and not data["thermodynamic_limit_proof"]
    )
    (ROOT / "overlap_confounding_run.log").write_text("\n".join(logs) + "\n", encoding="utf-8")
    artifacts = [
        "overlap_confounding_protocol.json", "overlap_confounding_analysis.json", "overlap-confounding-audit.png",
        "OVERLAP_CONFOUNDING_AUDIT.md", "Floquet-BdG-重叠差异混杂审计.docx", "overlap-confounding-word-qa.json",
        "overlap-confounding-word-render/report.json", "overlap_confounding_run.log", "analyze_overlap_confounding.py",
        "build_overlap_confounding_report.js", "record_overlap_confounding_qa.py", "test_overlap_confounding.py",
        "diagnose_same_n_rank_leakage.py", "embedding_census_analysis.json", "multi_seed_independent.json",
        "category_new_cells_independent.json",
    ]
    record = {
        "schema": "floquet-bdg-overlap-confounding-verification-v1",
        "recorded_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "all_passed": passed, "test_count": 6 if passed else None, "check_only": check_only,
        "original_independent_projectors_passed": original.get("all_passed"),
        "new_independent_projectors_passed": independent.get("all_passed"),
        "visual_review_status": qa.get("visualReview", {}).get("status"),
        "rendered_pages": qa.get("visualReview", {}).get("pagesReviewed"),
        "commands": rows,
        "sha256": {name: sha(ROOT / name) for name in artifacts if (ROOT / name).exists()},
        "scope": {
            "overlap_confounding_analysis_evaluated": passed, "cases": 16, "cells": 32,
            "method_grid_count": 96, "same_n_rank_controls": 192, "native_rank_controls": 32,
            "representation_fidelity_count": 192, "beta_profile_comparisons": 96,
            "same_n_embedding_rank_gate_passed": False,
            "max_linear_point_same_n_off_diagonal": summary["max_linear_point_same_n_off_diagonal"],
            "max_native_same_n_off_diagonal": summary["max_native_same_n_off_diagonal"],
            "max_cell_average_same_n_off_diagonal": summary["max_cell_average_same_n_off_diagonal"],
            "min_representation_fidelity": summary["min_representation_fidelity"],
            "min_beta_rms_absolute_difference": summary["min_beta_rms_absolute_difference"],
            "normalization_correction_applied": False, "size_effect_separated": False,
            "same_disorder_realization": False, "common_disorder_profile_control_computed": False,
            "next_control": "common_beta_x_sampling",
            "new_physics_cells": 0, "new_winding_computed": False, "n640_computed": False,
            "new_taxonomy_claim": False, "statistical_significance_claim": False,
            "thermodynamic_limit_proof": False,
        },
        "log": "overlap_confounding_run.log",
    }
    (ROOT / "overlap_confounding_verification.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("\n".join(logs))
    print("overlap_confounding_overall", "passed" if passed else "failed", "check_only", check_only)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
