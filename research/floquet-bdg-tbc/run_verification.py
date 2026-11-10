"""Reproduce the static and clean TBC baselines with logs and SHA-256 manifests."""

import datetime
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys

import numpy as np
import scipy

ROOT = Path(__file__).resolve().parent
WORKTREE = ROOT.parents[1]
CACHE = Path("D:/kimi-cache/tbc")


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    for name in ("tmp", "pycache"):
        (CACHE / name).mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env.update({
        "TMP": str(CACHE / "tmp"),
        "TEMP": str(CACHE / "tmp"),
        "PYTHONPYCACHEPREFIX": str(CACHE / "pycache"),
        "OPENBLAS_NUM_THREADS": "1",
        "OMP_NUM_THREADS": "1",
    })
    scripts = [
        ("test_tbc.py", ["-v"]),
        ("run_tbc.py", []),
        ("verify_tbc.py", []),
    ]
    rows, logs = [], []
    for script, arguments in scripts:
        command = [sys.executable, str(ROOT / script), *arguments]
        completed = subprocess.run(
            command,
            cwd=WORKTREE,
            env=env,
            text=True,
            encoding="utf-8",
            capture_output=True,
            timeout=240,
        )
        output = completed.stdout + completed.stderr
        logs.extend([
            f"$ python research/floquet-bdg-tbc/{script}" + (" " + " ".join(arguments) if arguments else ""),
            output.rstrip(),
            f"exit_code={completed.returncode}",
        ])
        rows.append({
            "script": script,
            "arguments": arguments,
            "exit_code": completed.returncode,
        })
        if completed.returncode != 0:
            break
    passed = len(rows) == len(scripts) and all(row["exit_code"] == 0 for row in rows)
    (ROOT / "run.log").write_text("\n".join(logs) + "\n", encoding="utf-8")
    artifacts = [
        "results.json",
        "independent_verification.json",
        "run.log",
        "tbc_model.py",
        "test_tbc.py",
        "run_tbc.py",
        "verify_tbc.py",
    ]
    result_data = json.loads((ROOT / "results.json").read_text(encoding="utf-8")) if (ROOT / "results.json").exists() else {}
    independent = json.loads((ROOT / "independent_verification.json").read_text(encoding="utf-8")) if (ROOT / "independent_verification.json").exists() else {}
    record = {
        "schema": "floquet-bdg-tbc-baseline-verification-v1",
        "recorded_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "all_passed": passed,
        "test_count": 9 if passed else None,
        "commands": rows,
        "environment": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "scipy": scipy.__version__,
            "openblas_num_threads": "1",
            "cache_root": str(CACHE),
        },
        "sha256": {name: sha256(ROOT / name) for name in artifacts if (ROOT / name).exists()},
        "observed_status": result_data.get("status"),
        "independent_passed": independent.get("passed"),
        "scope": {
            "static_baseline_checked": passed,
            "clean_kicked_baseline_checked": passed,
            "disorder_evaluated": False,
            "thermodynamic_limit_proof": False,
            "interactions_or_dissipation": False,
            "material_tc_or_experiment": False,
        },
        "log": "run.log",
    }
    (ROOT / "verification.json").write_text(
        json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print("\n".join(logs))
    print("overall", "passed" if passed else "failed")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
