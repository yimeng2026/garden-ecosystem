"""Reproduce and verify the endpoint-subspace diagnostic and its native Word report."""

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
DOCX = ROOT / "Floquet-BdG-端点子空间诊断.docx"


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
        ("subspace_analysis", [sys.executable, str(ROOT / "analyze_endpoint_subspaces.py")]),
        ("independent_projectors", [sys.executable, str(ROOT / "verify_endpoint_subspaces.py")]),
        ("docx_gate", [sys.executable, str(DOCX_PY), "validate", str(DOCX)]),
        ("visual_hash_binding", [sys.executable, str(ROOT / "record_endpoint_qa.py")]),
        ("report_contracts", [sys.executable, str(ROOT / "test_endpoint_subspaces.py"), "-v"]),
    ]
    rows, logs = [], []
    for label, command in commands:
        completed = subprocess.run(command, cwd=WORKTREE, env=env, text=True, encoding="utf-8", capture_output=True, timeout=180)
        output = completed.stdout + completed.stderr
        logs.extend([f"$ {label}: {' '.join(command)}", output.rstrip(), f"exit_code={completed.returncode}"])
        rows.append({"label": label, "command": command, "exit_code": completed.returncode})
        if completed.returncode != 0:
            break
    independent = json.loads((ROOT / "endpoint_subspace_independent.json").read_text(encoding="utf-8"))
    qa = json.loads((ROOT / "endpoint-word-qa.json").read_text(encoding="utf-8"))
    data = json.loads((ROOT / "endpoint_subspace_analysis.json").read_text(encoding="utf-8"))
    passed = (
        len(rows) == len(commands)
        and all(row["exit_code"] == 0 for row in rows)
        and independent.get("all_passed", False)
        and qa.get("visualReview", {}).get("status") == "passed"
        and not data.get("n640_computed", True)
    )
    (ROOT / "endpoint_run.log").write_text("\n".join(logs) + "\n", encoding="utf-8")
    artifacts = [
        "scale_diagnostic.json", "n400_scale.json", "n600_scale.json",
        "endpoint_subspace_analysis.json", "endpoint_subspace_independent.json", "endpoint-subspaces.png",
        "ENDPOINT_SUBSPACES.md", "Floquet-BdG-端点子空间诊断.docx", "endpoint-word-qa.json",
        "endpoint-word-render/report.json", "analyze_endpoint_subspaces.py", "verify_endpoint_subspaces.py",
        "build_endpoint_report.js", "record_endpoint_qa.py", "test_endpoint_subspaces.py", "endpoint_run.log",
    ]
    record = {
        "schema": "floquet-bdg-endpoint-verification-v1",
        "recorded_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "all_passed": passed,
        "test_count": 7 if passed else None,
        "independent_projectors_passed": independent.get("all_passed"),
        "visual_review_status": qa.get("visualReview", {}).get("status"),
        "rendered_pages": qa.get("visualReview", {}).get("pagesReviewed"),
        "commands": rows,
        "sha256": {name: sha(ROOT / name) for name in artifacts if (ROOT / name).exists()},
        "scope": {
            "n400_single_end_mechanism_evaluated": passed,
            "n600_second_pair_delocalization_evaluated": passed,
            "n640_automatically_justified": False,
            "thermodynamic_limit_proof": False,
            "uniform_strength_control_pending": True,
        },
        "log": "endpoint_run.log",
    }
    (ROOT / "endpoint_verification.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("\n".join(logs))
    print("endpoint_overall", "passed" if passed else "failed")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
