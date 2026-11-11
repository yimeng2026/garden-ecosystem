"""Verify embedding robustness and the exact reviewed Word artifact."""

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
DOCX = ROOT / "Floquet-BdG-共同表示稳健性.docx"


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
        ("embedding_robustness_analysis", [sys.executable, str(ROOT / "analyze_embedding_robustness.py")]),
        ("docx_gate", [sys.executable, str(DOCX_PY), "validate", str(DOCX)]),
        ("visual_hash_binding", [sys.executable, str(ROOT / "record_embedding_robustness_qa.py")]),
        ("report_contracts", [sys.executable, str(ROOT / "test_embedding_robustness.py"), "-v"]),
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
    qa = json.loads((ROOT / "embedding-robustness-word-qa.json").read_text(encoding="utf-8"))
    data = json.loads((ROOT / "embedding_robustness_analysis.json").read_text(encoding="utf-8"))
    summary = data["summary"]
    passed = (
        len(rows) == len(commands) and all(row["exit_code"] == 0 for row in rows)
        and original.get("all_passed", False) and independent.get("all_passed", False)
        and qa.get("visualReview", {}).get("status") == "passed"
        and len(data["cases"]) == 3 and len(data["cells"]) == 6
        and summary["method_grid_count"] == 18 and summary["diagonal_dominant_count"] == 18
        and summary["finest_same_assignment_count"] == 3
        and abs(summary["max_absolute_diagonal_score_change"] - 0.0006710320950930326) < 1e-15
        and all(row["diagonal_score_change_cell_minus_linear"] < 0 for case in data["cases"] for row in case["method_comparisons"])
        and data["max_linear_reproduction_error"] <= 1e-12 and data["max_profile_absolute_error"] <= 1e-10
        and data["new_physics_cells"] == 0 and not data["new_winding_computed"] and not data["n640_computed"]
        and not data["representation_invariant_claim"] and not data["embedding_convergence_proof"]
        and not data["same_physics_state_tracking_claim"] and not data["rank_exchange_proven"]
        and not data["second_pair_topological_claim"] and not data["new_taxonomy_claim"]
    )
    (ROOT / "embedding_robustness_run.log").write_text("\n".join(logs) + "\n", encoding="utf-8")
    artifacts = [
        "embedding_robustness_protocol.json", "repeated_category_analysis.json", "subspace_overlap_analysis.json",
        "multi_seed_independent.json", "category_new_cells_independent.json", "embedding_robustness_analysis.json",
        "embedding-robustness.png", "EMBEDDING_ROBUSTNESS.md", "Floquet-BdG-共同表示稳健性.docx",
        "embedding-robustness-word-qa.json", "embedding-robustness-word-render/report.json", "analyze_embedding_robustness.py",
        "build_embedding_robustness_report.js", "record_embedding_robustness_qa.py", "test_embedding_robustness.py", "embedding_robustness_run.log",
    ]
    record = {
        "schema": "floquet-bdg-embedding-robustness-verification-v1",
        "recorded_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "all_passed": passed, "test_count": 6 if passed else None,
        "original_independent_projectors_passed": original.get("all_passed"),
        "new_independent_projectors_passed": independent.get("all_passed"),
        "visual_review_status": qa.get("visualReview", {}).get("status"),
        "rendered_pages": qa.get("visualReview", {}).get("pagesReviewed"),
        "commands": rows,
        "sha256": {name: sha(ROOT / name) for name in artifacts if (ROOT / name).exists()},
        "scope": {
            "embedding_robustness_analysis_evaluated": passed, "cases": 3, "cells": 6,
            "methods": ["linear_point", "cell_average"], "method_grid_count": 18,
            "diagonal_dominant_count": 18, "finest_same_assignment_count": 3,
            "max_absolute_diagonal_score_change": summary["max_absolute_diagonal_score_change"],
            "cell_average_lower_in_all_nine_comparisons": True,
            "direction_stability_is_not_state_tracking": True,
            "representation_invariant_claim": False, "embedding_convergence_proof": False,
            "same_physics_state_tracking_claim": False, "rank_exchange_proven": False,
            "new_physics_cells": 0, "new_taxonomy_claim": False,
            "n640_automatically_justified": False, "thermodynamic_limit_proof": False,
        },
        "log": "embedding_robustness_run.log",
    }
    (ROOT / "embedding_robustness_verification.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("\n".join(logs))
    print("embedding_robustness_overall", "passed" if passed else "failed")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
