"""Verify all pair-response audits and the exact reviewed Word artifact."""

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
DOCX = ROOT / "Floquet-BdG-最近对与次近对响应审计.docx"


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
        ("pair_response_analysis", [sys.executable, str(ROOT / "analyze_pair_responses.py")]),
        ("docx_gate", [sys.executable, str(DOCX_PY), "validate", str(DOCX)]),
        ("visual_hash_binding", [sys.executable, str(ROOT / "record_pair_response_qa.py")]),
        ("report_contracts", [sys.executable, str(ROOT / "test_pair_responses.py"), "-v"]),
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
    qa = json.loads((ROOT / "pair-response-word-qa.json").read_text(encoding="utf-8"))
    data = json.loads((ROOT / "pair_response_analysis.json").read_text(encoding="utf-8"))
    edge, tail = data["edge_relation_counts"], data["L50_relation_counts"]
    passed = (
        len(rows) == len(commands) and all(row["exit_code"] == 0 for row in rows)
        and original.get("all_passed", False) and independent.get("all_passed", False)
        and qa.get("visualReview", {}).get("status") == "passed"
        and len(data["records"]) == 64 and len(data["responses"]) == 32 and len(data["cases"]) == 16
        and edge.get("same_nonzero") == 6 and edge.get("opposite_nonzero") == 10 and edge.get("at_least_one_zero", 0) == 0
        and tail.get("same_nonzero") == 10 and tail.get("opposite_nonzero") == 6 and tail.get("at_least_one_zero", 0) == 0
        and data["second_pair_joint_pass_contrasts"] == 0
        and data["max_original_metric_recompute_error"] <= 1e-12
        and not data["new_winding_computed"] and not data["n640_computed"]
        and not data["new_taxonomy_claim"] and not data["categories_changed"]
        and not data["second_pair_topological_claim"] and not data["statistical_significance_claim"]
    )
    (ROOT / "pair_response_run.log").write_text("\n".join(logs) + "\n", encoding="utf-8")
    artifacts = [
        "pair_response_protocol.json", "repeated_category_analysis.json", "near_miss_spatial_analysis.json",
        "multi_seed_independent.json", "category_new_cells_independent.json", "pair_response_analysis.json",
        "pair-response-audit.png", "PAIR_RESPONSE_AUDIT.md", "Floquet-BdG-最近对与次近对响应审计.docx",
        "pair-response-word-qa.json", "pair-response-word-render/report.json", "analyze_pair_responses.py",
        "build_pair_response_report.js", "record_pair_response_qa.py", "test_pair_responses.py", "pair_response_run.log",
    ]
    record = {
        "schema": "floquet-bdg-pair-response-verification-v1",
        "recorded_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "all_passed": passed, "test_count": 6 if passed else None,
        "original_independent_projectors_passed": original.get("all_passed"),
        "new_independent_projectors_passed": independent.get("all_passed"),
        "visual_review_status": qa.get("visualReview", {}).get("status"),
        "rendered_pages": qa.get("visualReview", {}).get("pagesReviewed"),
        "commands": rows,
        "sha256": {name: sha(ROOT / name) for name in artifacts if (ROOT / name).exists()},
        "scope": {
            "pair_response_analysis_evaluated": passed, "contrasts": 16,
            "records": 64, "responses": 32,
            "edge_same_nonzero": 6, "edge_opposite_nonzero": 10,
            "L50_same_nonzero": 10, "L50_opposite_nonzero": 6,
            "second_pair_joint_pass_contrasts": 0,
            "pair_identity": "same_spectral_rank_not_adiabatic_state_tracking",
            "statistical_significance_claim": False, "second_pair_topological_claim": False,
            "categories_changed": False, "new_taxonomy_claim": False,
            "n640_automatically_justified": False, "thermodynamic_limit_proof": False,
        },
        "log": "pair_response_run.log",
    }
    (ROOT / "pair_response_verification.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("\n".join(logs))
    print("pair_response_overall", "passed" if passed else "failed")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
