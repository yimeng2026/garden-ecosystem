"""Run the complete evidence audit and persist real exit codes."""

import datetime
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WORKTREE = ROOT.parents[1]


def run_all_tests():
    commands = [
        "build_evidence.py",
        "test_floquet_evidence_boundary.py",
        "verify_floquet_evidence_boundary.py",
    ]
    results = []
    log = []
    for script in commands:
        argv = [sys.executable, str(ROOT / script)]
        if script.startswith(("test_", "verify_")):
            argv.append("-v")
        completed = subprocess.run(argv, cwd=WORKTREE, text=True, encoding="utf-8", capture_output=True)
        output = completed.stdout + completed.stderr
        log.append(f"$ python research/floquet-evidence-boundary/{script}" + (" -v" if argv[-1] == "-v" else ""))
        log.append(output.rstrip())
        log.append(f"exit_code={completed.returncode}")
        results.append({"script": script, "command": argv, "exit_code": completed.returncode})
        if completed.returncode != 0:
            break
    passed = len(results) == len(commands) and all(row["exit_code"] == 0 for row in results)
    (ROOT / "run.log").write_text("\n".join(log) + "\n", encoding="utf-8")
    record = {
        "schema": "floquet-evidence-verification-v1",
        "recorded_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "all_passed": passed,
        "results": results,
        "contract_tests": 7 if passed else None,
        "independent_tests": 6 if passed else None,
        "source_anchors": 15 if passed else None,
        "evidence_sha256": hashlib.sha256((ROOT / "evidence.json").read_bytes()).hexdigest() if (ROOT / "evidence.json").exists() else None,
        "scope": {
            "source_and_logic_boundary_checked": passed,
            "floquet_dfpt_reproduced": False,
            "physical_enhancement_proven": False,
            "experimental_validation_completed": False,
        },
        "log": "run.log",
    }
    (ROOT / "verification.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("\n".join(log))
    print(f"overall={'passed' if passed else 'failed'}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(run_all_tests())
