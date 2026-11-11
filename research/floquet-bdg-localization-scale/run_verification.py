"""Verify localization-scale analysis, native Word, and current visual hashes."""

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
DOCX = ROOT / "Floquet-BdG-局域恢复尺度报告.docx"


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
        ("analysis_contracts", [sys.executable, str(ROOT / "test_scale_analysis.py"), "-v"]),
        ("profile_analysis", [sys.executable, str(ROOT / "analyze_scale.py")]),
        ("report_data", [sys.executable, str(ROOT / "build_report.py")]),
        ("docx_gate", [sys.executable, str(DOCX_PY), "validate", str(DOCX)]),
        ("visual_hash", [sys.executable, str(ROOT / "record_qa.py")]),
        ("report_contracts", [sys.executable, str(ROOT / "test_report.py"), "-v"]),
    ]
    rows, logs = [], []
    for label, command in commands:
        completed = subprocess.run(command, cwd=WORKTREE, env=env, text=True, encoding="utf-8", capture_output=True, timeout=120)
        output = completed.stdout + completed.stderr
        logs.extend([f"$ {label}: {' '.join(command)}", output.rstrip(), f"exit_code={completed.returncode}"])
        rows.append({"label": label, "command": command, "exit_code": completed.returncode})
        if completed.returncode != 0:
            break
    passed = len(rows) == len(commands) and all(row["exit_code"] == 0 for row in rows)
    (ROOT / "run.log").write_text("\n".join(logs) + "\n", encoding="utf-8")
    data = json.loads((ROOT / "localization_scale.json").read_text(encoding="utf-8"))
    qa = json.loads((ROOT / "word-qa" / "report.json").read_text(encoding="utf-8"))
    artifacts = [
        "localization_scale.json", "localization_scale.csv", "coverage-scale.png", "scale-diagnostics.png",
        "REPORT.md", "Floquet-BdG-局域恢复尺度报告.docx", "word-qa/report.json", "run.log",
        "scale_analysis.py", "analyze_scale.py", "test_scale_analysis.py", "build_report.py",
        "build_report.js", "record_qa.py", "test_report.py",
    ]
    record = {
        "schema": "floquet-bdg-localization-scale-verification-v1",
        "recorded_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "all_passed": passed,
        "analysis_test_count": 8 if passed else None,
        "report_test_count": 5 if passed else None,
        "profile_count": data["profile_count"], "case_count": data["case_count"],
        "rendered_pages": qa["rendered"], "visual_review_status": qa.get("manualReview", {}).get("status"),
        "commands": rows,
        "sha256": {name: sha(ROOT / name) for name in artifacts if (ROOT / name).exists()},
        "scope": {
            "n400_diagnostic_pending": True, "n600_diagnostic_pending": True,
            "n640_computed": False, "recovery_prediction": False,
            "thermodynamic_limit_proof": False,
        },
        "log": "run.log",
    }
    (ROOT / "verification.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("\n".join(logs))
    print("localization_scale_overall", "passed" if passed else "failed")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
