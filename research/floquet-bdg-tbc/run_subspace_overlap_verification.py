"""Verify common-grid subspace diagnostics and the exact reviewed Word artifact."""

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
DOCX = ROOT / "Floquet-BdG-跨尺寸子空间重叠.docx"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    env = os.environ.copy()
    env.update({
        "TMP": str(CACHE / "tmp"), "TEMP": str(CACHE / "tmp"),
        "PYTHONPYCACHEPREFIX": str(CACHE / "pycache"), "MPLCONFIGDIR": str(CACHE / "matplotlib"),
        "OPENBLAS_NUM_THREADS": "1", "OMP_NUM_THREADS": "1",
        "PATH": r"C:\Program Files\nodejs" + os.pathsep + env.get("PATH", ""),
    })
    commands = [
        ("subspace_overlap_analysis", [sys.executable, str(ROOT / "analyze_subspace_overlap.py")]),
        ("overlap_symmetry_diagnostic", [sys.executable, str(ROOT / "diagnose_overlap_symmetry.py")]),
        ("docx_gate", [sys.executable, str(DOCX_PY), "validate", str(DOCX)]),
        ("visual_hash_binding", [sys.executable, str(ROOT / "record_subspace_overlap_qa.py")]),
        ("report_contracts", [sys.executable, str(ROOT / "test_subspace_overlap.py"), "-v"]),
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
    qa = json.loads((ROOT / "subspace-overlap-word-qa.json").read_text(encoding="utf-8"))
    data = json.loads((ROOT / "subspace_overlap_analysis.json").read_text(encoding="utf-8"))
    symmetry = json.loads((ROOT / "overlap_symmetry_diagnostic.json").read_text(encoding="utf-8"))
    passed = (
        len(rows) == len(commands) and all(row["exit_code"] == 0 for row in rows)
        and original.get("all_passed", False) and independent.get("all_passed", False)
        and qa.get("visualReview", {}).get("status") == "passed"
        and len(data["cases"]) == 3 and len(data["cells"]) == 6
        and all(len(case["grids"]) == 3 for case in data["cases"])
        and data["finest_assignment_counts"] == {"diagonal": 3}
        and all(grid["dominant_assignment"] == "diagonal" for case in data["cases"] for grid in case["grids"])
        and all(case["grids"][-1]["diagonal_score"] < 0.05 for case in data["cases"])
        and data["max_profile_absolute_error"] <= 1e-10
        and symmetry["summary"]["max_direction_absolute_error"] <= 1e-12
        and symmetry["summary"]["max_svd_direct_absolute_error"] <= 1e-12
        and symmetry["summary"]["max_orthonormality_error"] <= 1e-12
        and symmetry["summary"]["reshape_roundtrip_absolute_error"] == 0.0
        and not symmetry["production_formula_changed"] and not symmetry["scientific_scores_changed"]
        and data["new_physics_cells"] == 0 and not data["new_winding_computed"] and not data["n640_computed"]
        and not data["same_physics_state_tracking_claim"] and not data["rank_exchange_proven"]
        and not data["second_pair_topological_claim"] and not data["grid_convergence_proof"]
        and not data["new_taxonomy_claim"] and not data["categories_changed"]
    )
    (ROOT / "subspace_overlap_run.log").write_text("\n".join(logs) + "\n", encoding="utf-8")
    artifacts = [
        "subspace_overlap_protocol.json", "repeated_category_analysis.json", "pair_response_analysis.json",
        "multi_seed_independent.json", "category_new_cells_independent.json", "subspace_overlap_analysis.json",
        "subspace-overlap.png", "SUBSPACE_OVERLAP.md", "Floquet-BdG-跨尺寸子空间重叠.docx",
        "subspace-overlap-word-qa.json", "subspace-overlap-word-render/report.json", "analyze_subspace_overlap.py",
        "build_subspace_overlap_report.js", "record_subspace_overlap_qa.py", "test_subspace_overlap.py", "subspace_overlap_run.log",
        "diagnose_overlap_symmetry.py", "overlap_symmetry_diagnostic.json",
    ]
    record = {
        "schema": "floquet-bdg-subspace-overlap-verification-v1",
        "recorded_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "all_passed": passed, "test_count": 9 if passed else None,
        "original_independent_projectors_passed": original.get("all_passed"),
        "new_independent_projectors_passed": independent.get("all_passed"),
        "visual_review_status": qa.get("visualReview", {}).get("status"),
        "rendered_pages": qa.get("visualReview", {}).get("pagesReviewed"),
        "commands": rows,
        "sha256": {name: sha(ROOT / name) for name in artifacts if (ROOT / name).exists()},
        "max_direction_absolute_error": symmetry["summary"]["max_direction_absolute_error"],
        "max_svd_direct_absolute_error": symmetry["summary"]["max_svd_direct_absolute_error"],
        "scope": {
            "subspace_overlap_analysis_evaluated": passed, "cases": 3, "cells": 6,
            "common_grids": [1200, 2400, 4800], "finest_assignment_counts": {"diagonal": 3},
            "absolute_overlap_is_weak": True, "relative_rank_advantage_is_not_state_tracking": True,
            "direction_reversal_symmetric_within_1e_12": True,
            "full_common_space_overlap_symmetric": True,
            "rectangular_cross_size_block_symmetry_required": False,
            "production_formula_changed": False, "scientific_scores_changed": False,
            "same_physics_state_tracking_claim": False, "rank_exchange_proven": False,
            "grid_convergence_proof": False, "second_pair_topological_claim": False,
            "new_physics_cells": 0, "categories_changed": False, "new_taxonomy_claim": False,
            "n640_automatically_justified": False, "thermodynamic_limit_proof": False,
        },
        "log": "subspace_overlap_run.log",
    }
    (ROOT / "subspace_overlap_verification.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("\n".join(logs))
    print("subspace_overlap_overall", "passed" if passed else "failed")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
