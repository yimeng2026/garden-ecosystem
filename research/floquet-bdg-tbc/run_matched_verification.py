"""Reproduce and verify the 2x2 matched-profile control and its report."""

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
DOCX = ROOT / "Floquet-BdG-同强度尺寸对照.docx"


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
        ("independent_projectors", [sys.executable, str(ROOT / "verify_matched_profiles.py")]),
        ("docx_gate", [sys.executable, str(DOCX_PY), "validate", str(DOCX)]),
        ("visual_hash_binding", [sys.executable, str(ROOT / "record_matched_qa.py")]),
        ("report_contracts", [sys.executable, str(ROOT / "test_matched_profiles.py"), "-v"]),
    ]
    rows, logs = [], []
    for label, command in commands:
        completed = subprocess.run(command, cwd=WORKTREE, env=env, text=True, encoding="utf-8", capture_output=True, timeout=180)
        output = completed.stdout + completed.stderr
        logs.extend([f"$ {label}: {' '.join(command)}", output.rstrip(), f"exit_code={completed.returncode}"])
        rows.append({"label": label, "command": command, "exit_code": completed.returncode})
        if completed.returncode != 0:
            break
    independent = json.loads((ROOT / "matched_profile_independent.json").read_text(encoding="utf-8"))
    qa = json.loads((ROOT / "matched-word-qa.json").read_text(encoding="utf-8"))
    data = json.loads((ROOT / "matched_profile_control.json").read_text(encoding="utf-8"))
    passed = (
        len(rows) == len(commands) and all(row["exit_code"] == 0 for row in rows)
        and independent.get("all_passed", False)
        and qa.get("visualReview", {}).get("status") == "passed"
        and len(data["cases"]) == 4 and not data["new_winding_computed"] and not data["n640_computed"]
    )
    (ROOT / "matched_run.log").write_text("\n".join(logs) + "\n", encoding="utf-8")
    artifacts = [
        "scale_diagnostic.json", "n400_scale.json", "n600_scale.json",
        "matched_profile_control.json", "matched_profile_independent.json", "matched-profile-control.png",
        "MATCHED_PROFILE_CONTROL.md", "Floquet-BdG-同强度尺寸对照.docx", "matched-word-qa.json",
        "matched-word-render/report.json", "analyze_matched_profiles.py", "verify_matched_profiles.py",
        "build_matched_report.js", "record_matched_qa.py", "test_matched_profiles.py", "matched_run.log",
    ]
    record = {
        "schema": "floquet-bdg-matched-verification-v1",
        "recorded_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "all_passed": passed,
        "test_count": 7 if passed else None,
        "independent_projectors_passed": independent.get("all_passed"),
        "visual_review_status": qa.get("visualReview", {}).get("status"),
        "rendered_pages": qa.get("visualReview", {}).get("pagesReviewed"),
        "commands": rows,
        "sha256": {name: sha(ROOT / name) for name in artifacts if (ROOT / name).exists()},
        "scope": {
            "matched_2x2_profile_control_evaluated": passed,
            "new_profile_pass_is_not_bulk_winding": True,
            "n640_automatically_justified": False,
            "multi_seed_control_pending": True,
            "thermodynamic_limit_proof": False,
        },
        "log": "matched_run.log",
    }
    (ROOT / "matched_verification.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("\n".join(logs))
    print("matched_overall", "passed" if passed else "failed")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
