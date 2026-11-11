"""Verify N=320 backend, registry, independent evidence, and report artifacts."""

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
DOCX = ROOT / "Floquet-BdG-TBC-N320定向报告.docx"


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
        ("backend_and_registry_tests", [sys.executable, str(ROOT / "test_n320.py"), "-v"]),
        ("registry_integrity", [sys.executable, str(ROOT / "run_n320.py"), "--merge-only"]),
        ("independent_integrity", [sys.executable, str(ROOT / "verify_n320.py"), "--merge-only"]),
        ("report_data", [sys.executable, str(ROOT / "build_n320_report.py")]),
        ("docx_gate", [sys.executable, str(DOCX_PY), "validate", str(DOCX)]),
        ("visual_hash", [sys.executable, str(ROOT / "record_n320_qa.py")]),
        ("report_contracts", [sys.executable, str(ROOT / "test_n320_report.py"), "-v"]),
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
    (ROOT / "n320_run.log").write_text("\n".join(logs) + "\n", encoding="utf-8")
    data = json.loads((ROOT / "n320_zero.json").read_text(encoding="utf-8"))
    independent = json.loads((ROOT / "n320_independent.json").read_text(encoding="utf-8"))
    qa = json.loads((ROOT / "n320-word-qa" / "report.json").read_text(encoding="utf-8"))
    artifacts = [
        "n320_zero.json", "n320_independent.json", "n320_summary.json", "n320-winding.png", "n320-endpoints.png",
        "N320.md", "Floquet-BdG-TBC-N320定向报告.docx", "n320-word-qa/report.json", "n320_run.log",
        "tbc_model.py", "run_disorder.py", "run_n320.py", "test_n320.py", "verify_n320.py",
        "build_n320_report.py", "build_n320_report.js", "record_n320_qa.py", "test_n320_report.py",
        "spectral_benchmark.json",
    ]
    record = {
        "schema": "floquet-bdg-tbc-n320-verification-v1",
        "recorded_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "all_passed": passed,
        "backend_test_count": 5 if passed else None,
        "report_test_count": 5 if passed else None,
        "registry_count": len(data["rows"]), "independent_count": independent["selected_count"],
        "rendered_pages": qa["rendered"], "visual_review_status": qa.get("manualReview", {}).get("status"),
        "commands": rows,
        "sha256": {name: sha(ROOT / name) for name in artifacts if (ROOT / name).exists()},
        "scope": {
            "n320_zero_gap_evaluated": passed,
            "n640_tbc_winding_computed": False,
            "localization_scale_analysis_pending": True,
            "thermodynamic_limit_proof": False,
        },
        "log": "n320_run.log",
    }
    (ROOT / "n320_verification.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("\n".join(logs))
    print("n320_overall", "passed" if passed else "failed")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
