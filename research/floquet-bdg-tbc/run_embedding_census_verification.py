"""Verify the full embedding census; optionally bind evidence without recomputing."""

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
DOCX = ROOT / "Floquet-BdG-全样本共同表示审计.docx"


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
    analysis_command = [sys.executable, str(ROOT / "analyze_embedding_census.py")]
    if check_only:
        analysis_command.append("--check-only")
    commands = [
        ("embedding_census_evidence_binding" if check_only else "embedding_census_analysis", analysis_command),
        ("docx_gate", [sys.executable, str(DOCX_PY), "validate", str(DOCX)]),
        ("visual_hash_binding", [sys.executable, str(ROOT / "record_embedding_census_qa.py")]),
        ("report_contracts", [sys.executable, str(ROOT / "test_embedding_census.py"), "-v"]),
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
    qa = json.loads((ROOT / "embedding-census-word-qa.json").read_text(encoding="utf-8"))
    data = json.loads((ROOT / "embedding_census_analysis.json").read_text(encoding="utf-8"))
    summary = data["summary"]
    candidate = next(case for case in data["cases"] if case["label"] == "seed_6_r_0p05")
    passed = (
        len(rows) == len(commands) and all(row["exit_code"] == 0 for row in rows)
        and original.get("all_passed", False) and independent.get("all_passed", False)
        and qa.get("visualReview", {}).get("status") == "passed"
        and len(data["cases"]) == 16 and len(data["cells"]) == 32
        and summary["method_grid_count"] == 96 and summary["diagonal_dominant_count"] == 90
        and summary["same_assignment_count"] == 48 and summary["finest_same_assignment_count"] == 16
        and summary["fully_diagonal_case_count"] == 15
        and summary["swapped_candidate_cases"] == ["seed_6_r_0p05"]
        and summary["method_assignment_counts"]["linear_point"] == {"diagonal": 45, "swapped": 3}
        and summary["method_assignment_counts"]["cell_average"] == {"diagonal": 45, "swapped": 3}
        and all(grid["dominant_assignment"] == "swapped" for method in candidate["methods"].values() for grid in method["grids"])
        and data["previous_linear_reproduction_error"] <= 1e-12 and data["previous_cell_reproduction_error"] <= 1e-12
        and data["max_profile_absolute_error"] <= 1e-10
        and data["new_physics_cells"] == 0 and not data["new_winding_computed"] and not data["n640_computed"]
        and not data["representation_invariant_claim"] and not data["same_physics_state_tracking_claim"]
        and not data["rank_exchange_proven"] and not data["embedding_convergence_proof"]
        and not data["second_pair_topological_claim"] and not data["new_taxonomy_claim"]
    )
    (ROOT / "embedding_census_run.log").write_text("\n".join(logs) + "\n", encoding="utf-8")
    artifacts = [
        "embedding_census_protocol.json", "repeated_category_analysis.json", "subspace_overlap_analysis.json",
        "embedding_robustness_analysis.json", "multi_seed_independent.json", "category_new_cells_independent.json",
        "embedding_census_analysis.json", "embedding-census.png", "EMBEDDING_CENSUS.md",
        "Floquet-BdG-全样本共同表示审计.docx", "embedding-census-word-qa.json", "embedding-census-word-render/report.json",
        "analyze_embedding_census.py", "build_embedding_census_report.js", "record_embedding_census_qa.py",
        "test_embedding_census.py", "embedding_census_run.log",
    ]
    record = {
        "schema": "floquet-bdg-embedding-census-verification-v1",
        "recorded_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "all_passed": passed, "test_count": 6 if passed else None,
        "check_only": check_only,
        "original_independent_projectors_passed": original.get("all_passed"),
        "new_independent_projectors_passed": independent.get("all_passed"),
        "visual_review_status": qa.get("visualReview", {}).get("status"),
        "rendered_pages": qa.get("visualReview", {}).get("pagesReviewed"),
        "commands": rows,
        "sha256": {name: sha(ROOT / name) for name in artifacts if (ROOT / name).exists()},
        "scope": {
            "embedding_census_analysis_evaluated": passed, "contrasts": 16, "cells": 32,
            "method_grid_count": 96, "diagonal_dominant_count": 90,
            "same_assignment_count": 48, "finest_same_assignment_count": 16,
            "fully_diagonal_case_count": 15, "swapped_candidate_cases": ["seed_6_r_0p05"],
            "candidate_is_not_state_exchange_proof": True,
            "representation_invariant_claim": False, "same_physics_state_tracking_claim": False,
            "rank_exchange_proven": False, "embedding_convergence_proof": False,
            "new_physics_cells": 0, "new_taxonomy_claim": False, "statistical_significance_claim": False,
            "n640_automatically_justified": False, "thermodynamic_limit_proof": False,
        },
        "log": "embedding_census_run.log",
    }
    (ROOT / "embedding_census_verification.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("\n".join(logs))
    print("embedding_census_overall", "passed" if passed else "failed", "check_only", check_only)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
