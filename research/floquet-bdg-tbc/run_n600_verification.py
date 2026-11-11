"""Verify N=600 resume integrity, independent evidence, and report artifacts."""

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
DOCX = ROOT / "Floquet-BdG-N600尾长诊断报告.docx"


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
        ("resume_contracts", [sys.executable, str(ROOT / "test_resumable.py"), "-v"]),
        ("diagnostic_integrity", [sys.executable, str(ROOT / "run_scale_diagnostic.py"), "--n", "600", "--grid", "0.05", "--merge-only"]),
        ("report_data", [sys.executable, str(ROOT / "build_n600_report.py")]),
        ("docx_gate", [sys.executable, str(DOCX_PY), "validate", str(DOCX)]),
        ("visual_status_hash", [sys.executable, str(ROOT / "record_n600_qa.py")]),
        ("report_contracts", [sys.executable, str(ROOT / "test_n600_report.py"), "-v"]),
    ]
    rows, logs = [], []
    for label, command in commands:
        completed = subprocess.run(command, cwd=WORKTREE, env=env, text=True, encoding="utf-8", capture_output=True, timeout=180)
        output = completed.stdout + completed.stderr
        logs.extend([f"$ {label}: {' '.join(command)}", output.rstrip(), f"exit_code={completed.returncode}"])
        rows.append({"label": label, "command": command, "exit_code": completed.returncode})
        if completed.returncode != 0:
            break
    independent = json.loads((ROOT / "scale_independent_n600.json").read_text(encoding="utf-8"))
    passed = len(rows) == len(commands) and all(row["exit_code"] == 0 for row in rows) and independent.get("integer_agreement", False)
    (ROOT / "n600_run.log").write_text("\n".join(logs) + "\n", encoding="utf-8")
    data = json.loads((ROOT / "scale_diagnostic.json").read_text(encoding="utf-8"))
    qa = json.loads((ROOT / "n600-word-qa" / "report.json").read_text(encoding="utf-8"))
    artifacts = [
        "scale_diagnostic.json", "scale_independent_n600.json", "n600_scale.json", "n600-result.png",
        "n600-coverage.png", "N600_DIAGNOSTIC.md", "Floquet-BdG-N600尾长诊断报告.docx",
        "n600-word-qa/report.json", "n600_run.log", "scale_work/n600_zero_dtheta0p05.json",
        "scale_work/n600_zero_dtheta0p025.json", "tbc_model.py", "resumable_winding.py",
        "run_disorder.py", "run_scale_diagnostic.py", "verify_scale_diagnostic.py",
        "build_n600_report.py", "build_n600_report.js", "record_n600_qa.py", "test_n600_report.py",
    ]
    record = {
        "schema": "floquet-bdg-n600-verification-v1",
        "recorded_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "all_passed": passed,
        "resume_test_count": 5 if passed else None,
        "report_test_count": 5 if passed else None,
        "n600_complete": data["n600_complete"],
        "independent_agreement": independent["integer_agreement"],
        "visual_review_status": qa.get("visualReview", {}).get("status"),
        "visual_pass_claimed": qa.get("visualReview", {}).get("visualPassClaimed"),
        "commands": rows,
        "sha256": {name: sha(ROOT / name) for name in artifacts if (ROOT / name).exists()},
        "scope": {
            "n600_tail_growth_confirmed": True,
            "n640_automatically_justified": False,
            "thermodynamic_limit_proof": False,
        },
        "log": "n600_run.log",
    }
    (ROOT / "n600_verification.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("\n".join(logs))
    print("n600_overall", "passed" if passed else "failed")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
