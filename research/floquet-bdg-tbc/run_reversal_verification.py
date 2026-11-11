"""Verify targeted reversal decomposition and the exact reviewed Word artifact."""

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
DOCX = ROOT / "Floquet-BdG-反转单元机制诊断.docx"


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
        ("reversal_decomposition", [sys.executable, str(ROOT / "analyze_reversal_units.py")]),
        ("docx_gate", [sys.executable, str(DOCX_PY), "validate", str(DOCX)]),
        ("visual_hash_binding", [sys.executable, str(ROOT / "record_reversal_qa.py")]),
        ("report_contracts", [sys.executable, str(ROOT / "test_reversal_units.py"), "-v"]),
    ]
    rows, logs = [], []
    for label, command in commands:
        completed = subprocess.run(command, cwd=WORKTREE, env=env, text=True, encoding="utf-8", capture_output=True, timeout=180)
        output = completed.stdout + completed.stderr
        logs.extend([f"$ {label}: {' '.join(command)}", output.rstrip(), f"exit_code={completed.returncode}"])
        rows.append({"label": label, "command": command, "exit_code": completed.returncode})
        if completed.returncode != 0:
            break
    independent = json.loads((ROOT / "multi_seed_independent.json").read_text(encoding="utf-8"))
    qa = json.loads((ROOT / "reversal-word-qa.json").read_text(encoding="utf-8"))
    data = json.loads((ROOT / "reversal_unit_analysis.json").read_text(encoding="utf-8"))
    passed = (
        len(rows) == len(commands) and all(row["exit_code"] == 0 for row in rows)
        and independent.get("all_passed", False)
        and qa.get("visualReview", {}).get("status") == "passed"
        and data["new_seed_count"] == 0 and not data["new_winding_computed"] and not data["n640_computed"]
        and all(case["comparison"]["max_recompute_error"] <= 1e-12 for case in data["cases"])
    )
    (ROOT / "reversal_run.log").write_text("\n".join(logs) + "\n", encoding="utf-8")
    artifacts = [
        "multi_seed_profile_control.json", "multi_seed_independent.json", "reversal_unit_analysis.json",
        "reversal-units.png", "REVERSAL_UNITS.md", "Floquet-BdG-反转单元机制诊断.docx",
        "reversal-word-qa.json", "reversal-word-render/report.json", "analyze_reversal_units.py",
        "build_reversal_report.js", "record_reversal_qa.py", "test_reversal_units.py", "reversal_run.log",
    ]
    record = {
        "schema": "floquet-bdg-reversal-verification-v1",
        "recorded_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "all_passed": passed, "test_count": 6 if passed else None,
        "original_independent_projectors_passed": independent.get("all_passed"),
        "visual_review_status": qa.get("visualReview", {}).get("status"),
        "rendered_pages": qa.get("visualReview", {}).get("pagesReviewed"),
        "commands": rows,
        "sha256": {name: sha(ROOT / name) for name in artifacts if (ROOT / name).exists()},
        "scope": {
            "targeted_reversal_decomposition_evaluated": passed,
            "right_driven_symmetrization_is_descriptive_only": True,
            "broadening_is_not_endpoint_loss": True,
            "new_seed_count": 0,
            "n640_automatically_justified": False,
            "repeated_category_analysis_pending": True,
            "thermodynamic_limit_proof": False,
        },
        "log": "reversal_run.log",
    }
    (ROOT / "reversal_verification.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("\n".join(logs))
    print("reversal_overall", "passed" if passed else "failed")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
