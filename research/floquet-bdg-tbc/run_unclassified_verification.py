"""Verify unclassified signature auditing and the exact reviewed Word artifact."""

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
DOCX = ROOT / "Floquet-BdG-未归类与未复现诊断.docx"


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
        ("signature_audit", [sys.executable, str(ROOT / "analyze_unclassified_signatures.py")]),
        ("docx_gate", [sys.executable, str(DOCX_PY), "validate", str(DOCX)]),
        ("visual_hash_binding", [sys.executable, str(ROOT / "record_unclassified_qa.py")]),
        ("report_contracts", [sys.executable, str(ROOT / "test_unclassified_signatures.py"), "-v"]),
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
    qa = json.loads((ROOT / "unclassified-word-qa.json").read_text(encoding="utf-8"))
    data = json.loads((ROOT / "unclassified_signature_analysis.json").read_text(encoding="utf-8"))
    passed = (
        len(rows) == len(commands) and all(row["exit_code"] == 0 for row in rows)
        and original.get("all_passed", False) and independent.get("all_passed", False)
        and qa.get("visualReview", {}).get("status") == "passed"
        and len(data["unclassified_cases"]) == 7 and sum(data["signature_counts"].values()) == 7
        and data["reference_weakening_new_seed_recurrences"] == 0
        and not data["new_winding_computed"] and not data["n640_computed"] and not data["new_taxonomy_claim"]
    )
    (ROOT / "unclassified_run.log").write_text("\n".join(logs) + "\n", encoding="utf-8")
    artifacts = [
        "repeated_category_analysis.json", "multi_seed_independent.json", "category_new_cells_independent.json",
        "unclassified_signature_analysis.json", "unclassified-signatures.png", "UNCLASSIFIED_SIGNATURES.md",
        "Floquet-BdG-未归类与未复现诊断.docx", "unclassified-word-qa.json", "unclassified-word-render/report.json",
        "analyze_unclassified_signatures.py", "build_unclassified_report.js", "record_unclassified_qa.py",
        "test_unclassified_signatures.py", "unclassified_run.log",
    ]
    record = {
        "schema": "floquet-bdg-unclassified-verification-v1",
        "recorded_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "all_passed": passed, "test_count": 5 if passed else None,
        "original_independent_projectors_passed": original.get("all_passed"),
        "new_independent_projectors_passed": independent.get("all_passed"),
        "visual_review_status": qa.get("visualReview", {}).get("status"),
        "rendered_pages": qa.get("visualReview", {}).get("pagesReviewed"),
        "commands": rows,
        "sha256": {name: sha(ROOT / name) for name in artifacts if (ROOT / name).exists()},
        "scope": {
            "unclassified_condition_audit_evaluated": passed,
            "unclassified_not_homogeneous": True,
            "right_weakening_new_seed_recurrences": 0,
            "near_misses_are_not_reference_recurrence": True,
            "new_taxonomy_claim": False,
            "n640_automatically_justified": False,
            "thermodynamic_limit_proof": False,
        },
        "log": "unclassified_run.log",
    }
    (ROOT / "unclassified_verification.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("\n".join(logs))
    print("unclassified_overall", "passed" if passed else "failed")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
