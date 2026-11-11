"""Verify the N=600 refined path; optionally bind evidence without recomputing."""

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
DOCX = ROOT / "Floquet-BdG-N600路径复核.docx"


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
    analysis_command = [sys.executable, str(ROOT / "analyze_n600_path.py")]
    if check_only:
        analysis_command.append("--check-only")
    commands = [
        ("n600_path_evidence_binding" if check_only else "n600_path_analysis", analysis_command),
        ("docx_gate", [sys.executable, str(DOCX_PY), "validate", str(DOCX)]),
        ("visual_hash_binding", [sys.executable, str(ROOT / "record_n600_path_qa.py")]),
        ("report_contracts", [sys.executable, str(ROOT / "test_n600_path.py"), "-v"]),
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
    qa = json.loads((ROOT / "n600-path-word-qa.json").read_text(encoding="utf-8"))
    data = json.loads((ROOT / "n600_path_analysis.json").read_text(encoding="utf-8"))
    summary, comparison = data["summary"], data["size_comparison"]
    passed = (
        len(rows) == len(commands) and all(row["exit_code"] == 0 for row in rows)
        and original.get("all_passed", False) and independent.get("all_passed", False)
        and qa.get("visualReview", {}).get("status") == "passed"
        and len(data["regions"]) == 2 and sum(len(region["points"]) for region in data["regions"]) == 10
        and sum(len(region["links"]) for region in data["regions"]) == 8
        and data["new_parameter_points"] == 9 and data["new_seed_count"] == 0
        and summary["diagonal_link_count"] == 8 and summary["swapped_link_count"] == 0 and summary["tie_link_count"] == 0
        and summary["min_center_separation_strength"] == 0.04375
        and abs(summary["min_center_separation"] - 0.0013216246877071761) < 1e-15
        and abs(summary["max_adjacent_center_separation_change"] - 0.00036595219294647467) < 1e-15
        and comparison["assignment_agreement_count"] == 8
        and not comparison["min_center_separation_same_strength"] and not comparison["max_change_same_link"]
        and comparison["max_change_link"] == {"from": 0.0425, "to": 0.04375}
        and abs(comparison["max_diagonal_score_absolute_difference"] - 0.21983270988901693) < 1e-12
        and abs(comparison["max_center_separation_absolute_difference"] - 0.001155621528202525) < 1e-12
        and summary["pair0_joint_pass_strengths"] == [0.04, 0.04125, 0.0425, 0.04375, 0.045]
        and summary["pair1_joint_pass_strengths"] == [] and data["max_reference_error"] <= 1e-10
        and data["fixed_random_stream"] and data["discrete_path"]
        and not data["new_winding_computed"] and not data["n640_computed"]
        and not data["size_invariance_claim"] and not data["continuous_path_proof"]
        and not data["spectral_crossing_proven"] and not data["avoided_crossing_claim"]
        and not data["state_exchange_proven"] and not data["second_pair_topological_claim"]
        and not data["new_taxonomy_claim"]
    )
    (ROOT / "n600_path_run.log").write_text("\n".join(logs) + "\n", encoding="utf-8")
    artifacts = [
        "n600_path_protocol.json", "repeated_category_analysis.json", "path_refinement_analysis.json",
        "fixed_n_path_analysis.json", "swap_candidate_spectrum_analysis.json", "multi_seed_independent.json",
        "category_new_cells_independent.json", "n600_path_analysis.json", "n600-path.png", "N600_PATH.md",
        "Floquet-BdG-N600路径复核.docx", "n600-path-word-qa.json", "n600-path-word-render/report.json",
        "analyze_n600_path.py", "build_n600_path_report.js", "record_n600_path_qa.py",
        "test_n600_path.py", "n600_path_run.log",
    ]
    record = {
        "schema": "floquet-bdg-n600-path-verification-v1",
        "recorded_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "all_passed": passed, "test_count": 6 if passed else None, "check_only": check_only,
        "original_independent_projectors_passed": original.get("all_passed"),
        "new_independent_projectors_passed": independent.get("all_passed"),
        "visual_review_status": qa.get("visualReview", {}).get("status"),
        "rendered_pages": qa.get("visualReview", {}).get("pagesReviewed"),
        "commands": rows,
        "sha256": {name: sha(ROOT / name) for name in artifacts if (ROOT / name).exists()},
        "scope": {
            "n600_path_analysis_evaluated": passed, "n": 600, "seed": 6,
            "refined_points": 10, "adjacent_links": 8, "new_unique_strengths": data["new_unique_strengths"],
            "diagonal_link_count": 8, "swapped_link_count": 0,
            "assignment_agreement_with_n400": 8,
            "min_center_separation": summary["min_center_separation"],
            "min_center_separation_strength": summary["min_center_separation_strength"],
            "max_adjacent_center_separation_change": summary["max_adjacent_center_separation_change"],
            "max_change_link": comparison["max_change_link"],
            "min_center_separation_same_strength": False, "max_change_same_link": False,
            "pair0_joint_pass_strengths": summary["pair0_joint_pass_strengths"], "pair1_joint_pass_strengths": [],
            "max_reference_error": data["max_reference_error"],
            "size_invariance_claim": False, "continuous_path_proof": False,
            "spectral_crossing_proven": False, "avoided_crossing_claim": False, "state_exchange_proven": False,
            "second_pair_topological_claim": False, "new_taxonomy_claim": False,
            "n640_automatically_justified": False, "thermodynamic_limit_proof": False,
        },
        "log": "n600_path_run.log",
    }
    (ROOT / "n600_path_verification.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("\n".join(logs))
    print("n600_path_overall", "passed" if passed else "failed", "check_only", check_only)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
