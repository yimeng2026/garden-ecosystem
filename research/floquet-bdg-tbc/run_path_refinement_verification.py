"""Verify targeted path refinement and the exact reviewed Word artifact."""

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
DOCX = ROOT / "Floquet-BdG-参数路径细化.docx"


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
        ("path_refinement_analysis", [sys.executable, str(ROOT / "analyze_path_refinement.py")]),
        ("docx_gate", [sys.executable, str(DOCX_PY), "validate", str(DOCX)]),
        ("visual_hash_binding", [sys.executable, str(ROOT / "record_path_refinement_qa.py")]),
        ("report_contracts", [sys.executable, str(ROOT / "test_path_refinement.py"), "-v"]),
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
    qa = json.loads((ROOT / "path-refinement-word-qa.json").read_text(encoding="utf-8"))
    data = json.loads((ROOT / "path_refinement_analysis.json").read_text(encoding="utf-8"))
    summary = data["summary"]
    passed = (
        len(rows) == len(commands) and all(row["exit_code"] == 0 for row in rows)
        and original.get("all_passed", False) and independent.get("all_passed", False)
        and qa.get("visualReview", {}).get("status") == "passed"
        and len(data["regions"]) == 2 and sum(len(region["points"]) for region in data["regions"]) == 10
        and sum(len(region["links"]) for region in data["regions"]) == 8
        and data["new_parameter_points"] == 5 and data["new_seed_count"] == 0
        and summary["diagonal_link_count"] == 8 and summary["swapped_link_count"] == 0 and summary["tie_link_count"] == 0
        and summary["min_center_separation_strength"] == 0.04125
        and abs(summary["min_center_separation"] - 0.0021869066664570976) < 1e-15
        and abs(summary["max_adjacent_center_separation_change"] - 0.00019730593093726092) < 1e-15
        and data["max_reference_error"] <= 1e-10
        and data["fixed_random_stream"] and data["adaptive_refinement_only"]
        and not data["new_winding_computed"] and not data["n640_computed"]
        and not data["continuous_path_proof"] and not data["spectral_crossing_proven"]
        and not data["avoided_crossing_claim"] and not data["state_exchange_proven"]
        and not data["second_pair_topological_claim"] and not data["new_taxonomy_claim"]
    )
    (ROOT / "path_refinement_run.log").write_text("\n".join(logs) + "\n", encoding="utf-8")
    artifacts = [
        "path_refinement_protocol.json", "fixed_n_path_analysis.json", "swap_candidate_spectrum_analysis.json",
        "multi_seed_independent.json", "category_new_cells_independent.json", "path_refinement_analysis.json",
        "path-refinement.png", "PATH_REFINEMENT.md", "Floquet-BdG-参数路径细化.docx",
        "path-refinement-word-qa.json", "path-refinement-word-render/report.json", "analyze_path_refinement.py",
        "build_path_refinement_report.js", "record_path_refinement_qa.py", "test_path_refinement.py", "path_refinement_run.log",
    ]
    record = {
        "schema": "floquet-bdg-path-refinement-verification-v1",
        "recorded_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "all_passed": passed, "test_count": 6 if passed else None,
        "original_independent_projectors_passed": original.get("all_passed"),
        "new_independent_projectors_passed": independent.get("all_passed"),
        "visual_review_status": qa.get("visualReview", {}).get("status"),
        "rendered_pages": qa.get("visualReview", {}).get("pagesReviewed"),
        "commands": rows,
        "sha256": {name: sha(ROOT / name) for name in artifacts if (ROOT / name).exists()},
        "scope": {
            "path_refinement_analysis_evaluated": passed, "regions": 2,
            "refined_points": 10, "adjacent_links": 8, "new_unique_strengths": data["new_unique_strengths"],
            "diagonal_link_count": 8, "swapped_link_count": 0,
            "min_center_separation": summary["min_center_separation"],
            "min_center_separation_strength": summary["min_center_separation_strength"],
            "max_adjacent_center_separation_change": summary["max_adjacent_center_separation_change"],
            "max_reference_error": data["max_reference_error"],
            "coarse_jump_is_not_crossing_proof": True,
            "discrete_minimum_is_not_continuous_extremum": True,
            "continuous_path_proof": False, "spectral_crossing_proven": False,
            "avoided_crossing_claim": False, "state_exchange_proven": False,
            "second_pair_topological_claim": False, "new_taxonomy_claim": False,
            "n640_automatically_justified": False, "thermodynamic_limit_proof": False,
        },
        "log": "path_refinement_run.log",
    }
    (ROOT / "path_refinement_verification.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("\n".join(logs))
    print("path_refinement_overall", "passed" if passed else "failed")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
