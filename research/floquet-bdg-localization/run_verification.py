"""Run the complete localization study and artifact checks with real exit codes."""

import datetime
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WORKTREE = ROOT.parents[1]


def run_all_tests():
    scripts = [
        ("run_localization.py", False),
        ("test_localization.py", True),
        ("verify_localization.py", True),
        ("build_markdown.py", False),
        ("build_figure.py", False),
        ("test_report.py", True),
    ]
    environment = os.environ.copy()
    environment.setdefault("PYTHONPYCACHEPREFIX", "D:/migration/cache/python")
    environment.setdefault("MPLCONFIGDIR", "D:/migration/cache/matplotlib")
    results = []
    log = []
    for script, verbose in scripts:
        argv = [sys.executable, str(ROOT / script)] + (["-v"] if verbose else [])
        completed = subprocess.run(argv, cwd=WORKTREE, env=environment, text=True, encoding="utf-8", capture_output=True)
        output = completed.stdout + completed.stderr
        log.append(f"$ python research/floquet-bdg-localization/{script}" + (" -v" if verbose else ""))
        log.append(output.rstrip())
        log.append(f"exit_code={completed.returncode}")
        results.append({"script": script, "command": argv, "exit_code": completed.returncode})
        if completed.returncode != 0:
            break
    passed = len(results) == len(scripts) and all(row["exit_code"] == 0 for row in results)
    (ROOT / "run.log").write_text("\n".join(log) + "\n", encoding="utf-8")
    data = {
        "schema": "floquet-bdg-localization-verification-v1",
        "recorded_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "all_passed": passed,
        "results": results,
        "localization_tests": 6 if passed else None,
        "independent_solver_tests": 6 if passed else None,
        "report_tests": 2 if passed else None,
        "results_sha256": hashlib.sha256((ROOT / "results.json").read_bytes()).hexdigest() if (ROOT / "results.json").exists() else None,
        "docx_sha256": hashlib.sha256((ROOT / "REPORT.docx").read_bytes()).hexdigest() if (ROOT / "REPORT.docx").exists() else None,
        "short_chain_regime_supported": passed,
        "full_size_rule_status": "inconclusive_preserved",
        "thermodynamic_limit_proof": False,
        "material_tc_prediction": False,
        "experimental_validation": False,
        "log": "run.log",
    }
    (ROOT / "verification.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("\n".join(log))
    print(f"overall={'passed' if passed else 'failed'}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(run_all_tests())
