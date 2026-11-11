"""Verify the repeated category analysis and its exact reviewed Word artifact."""

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
DOCX = ROOT / "Floquet-BdG-端部机制类别检验.docx"


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
        ("new_cell_registry", [sys.executable, str(ROOT / "build_category_cells.py")]),
        ("new_cell_independent_projectors", [sys.executable, str(ROOT / "verify_category_cells.py")]),
        ("category_analysis", [sys.executable, str(ROOT / "analyze_repeated_categories.py")]),
        ("docx_gate", [sys.executable, str(DOCX_PY), "validate", str(DOCX)]),
        ("visual_hash_binding", [sys.executable, str(ROOT / "record_category_qa.py")]),
        ("report_contracts", [sys.executable, str(ROOT / "test_repeated_categories.py"), "-v"]),
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
    qa = json.loads((ROOT / "category-word-qa.json").read_text(encoding="utf-8"))
    data = json.loads((ROOT / "repeated_category_analysis.json").read_text(encoding="utf-8"))
    passed = (
        len(rows) == len(commands) and all(row["exit_code"] == 0 for row in rows)
        and original.get("all_passed", False) and independent.get("all_passed", False)
        and qa.get("visualReview", {}).get("status") == "passed"
        and len(data["all_cells"]) == 32 and len(data["cases"]) == 16
        and sum(data["category_counts"].values()) == 16
        and not data["new_winding_computed"] and not data["n640_computed"]
    )
    (ROOT / "category_run.log").write_text("\n".join(logs) + "\n", encoding="utf-8")
    artifacts = [
        "repeated_category_protocol.json", "multi_seed_profile_control.json", "multi_seed_independent.json",
        "category_new_cells.json", "category_new_cells_independent.json", "repeated_category_analysis.json",
        "repeated-categories.png", "REPEATED_CATEGORIES.md", "Floquet-BdG-端部机制类别检验.docx",
        "category-word-qa.json", "category-word-render/report.json", "build_category_cells.py",
        "verify_category_cells.py", "analyze_repeated_categories.py", "build_category_report.js",
        "record_category_qa.py", "test_repeated_categories.py", "category_run.log",
    ]
    record = {
        "schema": "floquet-bdg-category-verification-v1",
        "recorded_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "all_passed": passed, "test_count": 5 if passed else None,
        "original_independent_projectors_passed": original.get("all_passed"),
        "new_independent_projectors_passed": independent.get("all_passed"),
        "visual_review_status": qa.get("visualReview", {}).get("status"),
        "rendered_pages": qa.get("visualReview", {}).get("pagesReviewed"),
        "commands": rows,
        "sha256": {name: sha(ROOT / name) for name in artifacts if (ROOT / name).exists()},
        "scope": {
            "repeated_category_analysis_evaluated": passed,
            "right_symmetrization_new_seed_recurrences": data["new_seed_category_counts"]["right_end_driven_symmetrization"],
            "right_weakening_new_seed_recurrences": data["new_seed_category_counts"]["right_end_weakening_with_broadening"],
            "other_unclassified_count": data["category_counts"]["other_unclassified"],
            "unclassified_cases_preserved": True,
            "n640_automatically_justified": False,
            "universal_category_claim": False,
            "thermodynamic_limit_proof": False,
        },
        "log": "category_run.log",
    }
    (ROOT / "category_verification.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("\n".join(logs))
    print("category_overall", "passed" if passed else "failed")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
