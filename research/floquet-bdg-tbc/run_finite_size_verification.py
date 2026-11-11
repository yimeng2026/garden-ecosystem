"""Verify finite-size registry integrity, reports, and current visual hashes."""

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
DOCX = ROOT / "Floquet-BdG-TBC有限尺寸报告.docx"


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
        ("unit_contracts", [sys.executable, str(ROOT / "test_finite_size.py"), "-v"]),
        ("registry_integrity", [sys.executable, str(ROOT / "run_finite_size.py"), "--merge-only"]),
        ("independent_integrity", [sys.executable, str(ROOT / "verify_finite_size.py"), "--merge-only"]),
        ("report_data", [sys.executable, str(ROOT / "build_finite_size_report.py")]),
        ("docx_gate", [sys.executable, str(DOCX_PY), "validate", str(DOCX)]),
        ("visual_hash", [sys.executable, str(ROOT / "record_finite_size_qa.py")]),
        ("report_contracts", [sys.executable, str(ROOT / "test_finite_size_report.py"), "-v"]),
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
    (ROOT / "finite_run.log").write_text("\n".join(logs) + "\n", encoding="utf-8")
    finite = json.loads((ROOT / "finite_size_zero.json").read_text(encoding="utf-8"))
    independent = json.loads((ROOT / "finite_size_independent.json").read_text(encoding="utf-8"))
    qa = json.loads((ROOT / "finite-word-qa" / "report.json").read_text(encoding="utf-8"))
    artifacts = [
        "finite_size_zero.json", "finite_size_independent.json", "finite_size_independent_controls.json",
        "finite_size_independent_remaining.json", "finite-size-winding.png", "finite-size-endpoints.png",
        "FINITE_SIZE.md", "Floquet-BdG-TBC有限尺寸报告.docx", "finite-word-qa/report.json", "finite_run.log",
        "run_disorder.py", "run_finite_size.py", "test_finite_size.py", "verify_finite_size.py",
        "build_finite_size_report.py", "build_finite_size_report.js", "record_finite_size_qa.py", "test_finite_size_report.py",
    ]
    record = {
        "schema": "floquet-bdg-tbc-finite-size-verification-v1",
        "recorded_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "all_passed": passed,
        "unit_test_count": 4 if passed else None,
        "report_test_count": 5 if passed else None,
        "registry_count": len(finite["rows"]),
        "independent_count": independent["selected_count"],
        "rendered_pages": qa["rendered"],
        "visual_review_status": qa.get("manualReview", {}).get("status"),
        "commands": rows,
        "sha256": {name: sha(ROOT / name) for name in artifacts if (ROOT / name).exists()},
        "scope": {
            "n160_zero_gap_evaluated": passed,
            "n320_tbc_winding_computed": False,
            "thermodynamic_limit_proof": False,
            "material_or_experiment": False,
        },
        "log": "finite_run.log",
    }
    (ROOT / "finite_verification.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("\n".join(logs))
    print("finite_size_overall", "passed" if passed else "failed")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
