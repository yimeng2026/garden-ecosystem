"""Verify the targeted swap-candidate spectral audit and reviewed Word artifact."""

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
DOCX = ROOT / "Floquet-BdG-交换候选谱结构.docx"


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
        ("swap_candidate_spectrum_analysis", [sys.executable, str(ROOT / "analyze_swap_candidate_spectrum.py")]),
        ("docx_gate", [sys.executable, str(DOCX_PY), "validate", str(DOCX)]),
        ("visual_hash_binding", [sys.executable, str(ROOT / "record_swap_candidate_spectrum_qa.py")]),
        ("report_contracts", [sys.executable, str(ROOT / "test_swap_candidate_spectrum.py"), "-v"]),
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
    qa = json.loads((ROOT / "swap-candidate-spectrum-word-qa.json").read_text(encoding="utf-8"))
    data = json.loads((ROOT / "swap_candidate_spectrum_analysis.json").read_text(encoding="utf-8"))
    passed = (
        len(rows) == len(commands) and all(row["exit_code"] == 0 for row in rows)
        and original.get("all_passed", False) and independent.get("all_passed", False)
        and qa.get("visualReview", {}).get("status") == "passed"
        and len(data["cells"]) == 2 and all(len(cell["spectrum"]) == 6 for cell in data["cells"])
        and not data["cross_pair_exact_degenerate"] and not data["near_degeneracy_threshold_added"]
        and all(cell["center_separation"] > 0 for cell in data["cells"])
        and all(not cell["pairs"][1]["diagnostic_joint_pass"] for cell in data["cells"])
        and all(cell["pairs"][1]["max_separation_ratio"] == 1 for cell in data["cells"])
        and all(row["cross_term_exceeds_each_diagonal_entry"] for row in data["candidate_overlap"].values())
        and data["max_profile_absolute_error"] <= 1e-10 and data["new_physics_cells"] == 0
        and not data["new_winding_computed"] and not data["n640_computed"]
        and not data["spectral_crossing_proven"] and not data["avoided_crossing_claim"]
        and not data["state_exchange_proven"] and not data["second_pair_topological_claim"]
        and data["sorted_order_is_constructed_not_tracking"] and not data["rank_swap_observed"]
        and not data["new_taxonomy_claim"] and not data["categories_changed"]
    )
    (ROOT / "swap_candidate_spectrum_run.log").write_text("\n".join(logs) + "\n", encoding="utf-8")
    artifacts = [
        "swap_candidate_spectrum_protocol.json", "repeated_category_analysis.json", "embedding_census_analysis.json",
        "multi_seed_independent.json", "category_new_cells_independent.json", "swap_candidate_spectrum_analysis.json",
        "swap-candidate-spectrum.png", "SWAP_CANDIDATE_SPECTRUM.md", "Floquet-BdG-交换候选谱结构.docx",
        "swap-candidate-spectrum-word-qa.json", "swap-candidate-spectrum-word-render/report.json",
        "analyze_swap_candidate_spectrum.py", "build_swap_candidate_spectrum_report.js", "record_swap_candidate_spectrum_qa.py",
        "test_swap_candidate_spectrum.py", "swap_candidate_spectrum_run.log",
    ]
    record = {
        "schema": "floquet-bdg-swap-candidate-spectrum-verification-v1",
        "recorded_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "all_passed": passed, "test_count": 6 if passed else None,
        "original_independent_projectors_passed": original.get("all_passed"),
        "new_independent_projectors_passed": independent.get("all_passed"),
        "visual_review_status": qa.get("visualReview", {}).get("status"),
        "rendered_pages": qa.get("visualReview", {}).get("pagesReviewed"),
        "commands": rows,
        "sha256": {name: sha(ROOT / name) for name in artifacts if (ROOT / name).exists()},
        "scope": {
            "swap_candidate_spectrum_analysis_evaluated": passed, "cells": 2, "spectrum_ranks_per_cell": 6,
            "center_separations": [cell["center_separation"] for cell in data["cells"]],
            "center_separation_delta": data["size_comparison"]["center_separation_delta"],
            "cross_pair_exact_degenerate": False, "second_pair_separation_ratio": 1,
            "cross_term_drives_candidate": True, "spectral_crossing_proven": False,
            "avoided_crossing_claim": False, "state_exchange_proven": False,
            "near_degeneracy_threshold_added": False, "second_pair_topological_claim": False,
            "new_physics_cells": 0, "new_taxonomy_claim": False,
            "n640_automatically_justified": False, "thermodynamic_limit_proof": False,
        },
        "log": "swap_candidate_spectrum_run.log",
    }
    (ROOT / "swap_candidate_spectrum_verification.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("\n".join(logs))
    print("swap_candidate_spectrum_overall", "passed" if passed else "failed")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
