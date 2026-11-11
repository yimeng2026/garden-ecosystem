"""Verify near-miss spatial diagnostics and the exact reviewed Word artifact."""

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
DOCX = ROOT / "Floquet-BdG-近miss空间分布与次近对.docx"


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
        ("spatial_analysis", [sys.executable, str(ROOT / "analyze_near_miss_spatial.py")]),
        ("docx_gate", [sys.executable, str(DOCX_PY), "validate", str(DOCX)]),
        ("visual_hash_binding", [sys.executable, str(ROOT / "record_near_miss_qa.py")]),
        ("report_contracts", [sys.executable, str(ROOT / "test_near_miss_spatial.py"), "-v"]),
    ]
    rows, logs = [], []
    for label, command in commands:
        completed = subprocess.run(command, cwd=WORKTREE, env=env, text=True, encoding="utf-8", capture_output=True, timeout=180)
        output = completed.stdout + completed.stderr
        logs.extend([f"$ {label}: {' '.join(command)}", output.rstrip(), f"exit_code={completed.returncode}"])
        rows.append({"label": label, "command": command, "exit_code": completed.returncode})
        if completed.returncode != 0:
            break
    original = json.loads((ROOT / "multi_seed_independent.json").read_text(encoding="utf-8"))
    independent = json.loads((ROOT / "category_new_cells_independent.json").read_text(encoding="utf-8"))
    qa = json.loads((ROOT / "near-miss-word-qa.json").read_text(encoding="utf-8"))
    data = json.loads((ROOT / "near_miss_spatial_analysis.json").read_text(encoding="utf-8"))
    passed = (
        len(rows) == len(commands) and all(row["exit_code"] == 0 for row in rows)
        and original.get("all_passed", False) and independent.get("all_passed", False)
        and qa.get("visualReview", {}).get("status") == "passed"
        and len(data["records"]) == 12 and len(data["size_deltas"]) == 6
        and data["max_original_metric_recompute_error"] <= 1e-12
        and not data["new_winding_computed"] and not data["n640_computed"]
        and not data["new_taxonomy_claim"] and not data["categories_changed"]
        and not data["second_pair_topological_claim"]
    )
    (ROOT / "near_miss_run.log").write_text("\n".join(logs) + "\n", encoding="utf-8")
    artifacts = [
        "near_miss_spatial_protocol.json", "repeated_category_analysis.json", "unclassified_signature_analysis.json",
        "multi_seed_independent.json", "category_new_cells_independent.json", "near_miss_spatial_analysis.json",
        "near-miss-spatial.png", "NEAR_MISS_SPATIAL.md", "Floquet-BdG-近miss空间分布与次近对.docx",
        "near-miss-word-qa.json", "near-miss-word-render/report.json", "analyze_near_miss_spatial.py",
        "build_near_miss_report.js", "record_near_miss_qa.py", "test_near_miss_spatial.py", "near_miss_run.log",
    ]
    record = {
        "schema": "floquet-bdg-near-miss-spatial-verification-v1",
        "recorded_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "all_passed": passed, "test_count": 6 if passed else None,
        "original_independent_projectors_passed": original.get("all_passed"),
        "new_independent_projectors_passed": independent.get("all_passed"),
        "visual_review_status": qa.get("visualReview", {}).get("status"),
        "rendered_pages": qa.get("visualReview", {}).get("pagesReviewed"),
        "commands": rows,
        "sha256": {name: sha(ROOT / name) for name in artifacts if (ROOT / name).exists()},
        "scope": {
            "near_miss_spatial_analysis_evaluated": passed,
            "records": 12, "size_deltas": 6,
            "original_metric_max_error": data["max_original_metric_recompute_error"],
            "fixed40_and_original10pct_separated": True,
            "second_pair_is_descriptive_only": True,
            "categories_changed": False, "new_taxonomy_claim": False,
            "n640_automatically_justified": False, "thermodynamic_limit_proof": False,
        },
        "log": "near_miss_run.log",
    }
    (ROOT / "near_miss_verification.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("\n".join(logs))
    print("near_miss_overall", "passed" if passed else "failed")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
