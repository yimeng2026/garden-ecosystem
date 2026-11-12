"""Verify pair structure, independent recomputation and reviewed native Word."""

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
DATA = ROOT / "pair_inconsistency_structure_analysis.json"
DOCX = ROOT / "Floquet-BdG-候选不一致对结构分析.docx"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    check_only = "--check-only" in sys.argv
    env = os.environ.copy()
    env.update({
        "TMP": str(CACHE / "tmp"), "TEMP": str(CACHE / "tmp"),
        "PYTHONPYCACHEPREFIX": str(CACHE / "pycache"), "MPLCONFIGDIR": str(CACHE / "matplotlib"),
        "OPENBLAS_NUM_THREADS": "1", "OMP_NUM_THREADS": "1",
        "PATH": r"C:\Program Files\nodejs" + os.pathsep + env.get("PATH", ""),
    })
    analysis_command = [sys.executable, str(ROOT / "analyze_pair_inconsistency_structure.py")]
    if check_only:
        analysis_command.append("--check-only")
    commands = [
        ("pair_inconsistency_structure_binding" if check_only else "pair_inconsistency_structure_analysis", analysis_command),
        ("pair_inconsistency_structure_independent_recheck", [sys.executable, str(ROOT / "verify_pair_inconsistency_structure.py")]),
        ("docx_gate", [sys.executable, str(DOCX_PY), "validate", str(DOCX)]),
        ("visual_hash_binding", [sys.executable, str(ROOT / "record_pair_inconsistency_structure_qa.py")]),
        ("report_contracts", [sys.executable, str(ROOT / "test_pair_inconsistency_structure.py"), "-v"]),
    ]
    rows, logs = [], []
    for label, command in commands:
        completed = subprocess.run(command, cwd=WORKTREE, env=env, text=True, encoding="utf-8", capture_output=True, timeout=240)
        output = completed.stdout + completed.stderr
        logs.extend([f"$ {label}: {' '.join(command)}", output.rstrip(), f"exit_code={completed.returncode}"])
        rows.append({"label": label, "command": command, "exit_code": completed.returncode})
        if completed.returncode != 0:
            break
    data = json.loads(DATA.read_text(encoding="utf-8"))
    independent = json.loads((ROOT / "pair_inconsistency_structure_independent.json").read_text(encoding="utf-8"))
    qa = json.loads((ROOT / "pair-inconsistency-structure-word-qa.json").read_text(encoding="utf-8"))
    closest = data["closest_candidate_comparison"]
    passed = (
        len(rows) == len(commands) and all(row["exit_code"] == 0 for row in rows)
        and independent.get("all_passed", False)
        and independent.get("pair_summary_count") == 20
        and independent.get("overlap_record_count") == 120
        and independent.get("total_inconsistent_assignments") == 104
        and independent.get("pair_summary_mismatch_count") == 0
        and independent.get("failure_set_mismatch_count") == 0
        and independent.get("overlap_mismatch_count") == 0
        and independent.get("spectrum_mismatch_count") == 0
        and independent.get("closest_comparison_mismatch_count") == 0
        and not independent.get("new_floquet_spectra_recomputed")
        and qa.get("visualReview", {}).get("status") == "passed"
        and qa.get("visualReview", {}).get("pagesReviewed") == 5
        and qa.get("visualReview", {}).get("contactSheetRead") is True
        and qa.get("visualReview", {}).get("nearBlankPages") == []
        and qa.get("visualReview", {}).get("clippedPages") == []
        and qa.get("visualReview", {}).get("docxSha256") == sha(DOCX)
        and qa.get("visualReview", {}).get("renderOutputComplete") is True
        and data["schema"] == "floquet-bdg-pair-inconsistency-structure-v1"
        and len(data["pair_summaries"]) == 20 and len(data["candidate_failure_sets"]) == 16
        and len(data["overlap_records"]) == 120 and len(data["shared_failure_spectrum"]) == 17
        and data["total_inconsistent_assignments"] == 104
        and data["source_pair_record_count"] == 400 and data["source_uninformative_pair_count"] == 5
        and data["source_records_unchanged"] and data["all_preregistered_results_retained"]
        and not data["strict_rule_changed"] and not data["failed_pairs_removed"] and not data["tie_pairs_removed"]
        and not data["new_metric_proposed"] and not data["ensemble_rule_proposed"]
        and data["structure_is_descriptive_only"] and not data["causal_attribution_completed"]
        and not data["predictive_validation_completed"] and not data["pristine_external_holdout_claim"]
        and not data["predictive_model_fitted"] and not data["correlation_claim"]
        and not data["predictive_accuracy_computed"] and not data["statistical_significance_claim"]
        and not data["causal_mechanism_proven"] and not data["new_taxonomy_claim"]
        and data["new_floquet_cells_computed"] == 0 and not data["new_winding_computed"] and not data["n640_computed"]
        and data["protocol_sha256"] == sha(ROOT / "pair_inconsistency_structure_protocol.json")
        and data["source_pair_evaluation_sha256"] == sha(ROOT / "holdout_pair_evaluation_analysis.json")
        and closest["intersection_count"] == 1 and closest["union_count"] == 3
        and independent.get("max_pair_inconsistent_candidate_count") == 12
    )
    (ROOT / "pair_inconsistency_structure_run.log").write_text("\n".join(logs) + "\n", encoding="utf-8")
    artifacts = [
        "pair_inconsistency_structure_protocol.json", "pair_inconsistency_structure_analysis.json", "pair_inconsistency_structure_independent.json",
        "pair-inconsistency-structure.png", "PAIR_INCONSISTENCY_STRUCTURE.md", DOCX.name,
        "pair-inconsistency-structure-word-qa.json", "pair-inconsistency-structure-word-render/report.json", "pair_inconsistency_structure_verification.json",
        "pair_inconsistency_structure_run.log", "analyze_pair_inconsistency_structure.py", "verify_pair_inconsistency_structure.py",
        "build_pair_inconsistency_structure_report.js", "record_pair_inconsistency_structure_qa.py", "test_pair_inconsistency_structure.py",
        "run_pair_inconsistency_structure_verification.py",
    ]
    record = {
        "schema": "floquet-bdg-pair-inconsistency-structure-verification-v1",
        "recorded_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "all_passed": passed, "test_count": 8 if passed else None, "check_only": check_only,
        "independent_recheck_passed": independent.get("all_passed"),
        "independent_overlap_mismatch_count": independent.get("overlap_mismatch_count"),
        "visual_review_status": qa.get("visualReview", {}).get("status"),
        "rendered_pages": qa.get("visualReview", {}).get("pagesReviewed"),
        "render_command_exit_code": qa.get("visualReview", {}).get("renderCommandExitCode"),
        "render_output_complete": qa.get("visualReview", {}).get("renderOutputComplete"),
        "commands": rows,
        "sha256": {name: sha(ROOT / name) for name in artifacts if (ROOT / name).exists()},
        "scope": {
            "pair_inconsistency_structure_analysis_evaluated": passed,
            "pair_summary_count": 20, "candidate_failure_set_count": 16,
            "overlap_record_count": 120, "total_inconsistent_assignments": 104,
            "all_candidates_inconsistent_pairs": independent.get("all_candidates_inconsistent_pairs"),
            "all_candidates_consistent_pairs": independent.get("all_candidates_consistent_pairs"),
            "max_pair_inconsistent_candidate_count": independent.get("max_pair_inconsistent_candidate_count"),
            "closest_candidate_comparison": closest,
            "source_records_unchanged": True, "strict_rule_changed": False,
            "failed_pairs_removed": False, "tie_pairs_removed": False,
            "new_metric_proposed": False, "ensemble_rule_proposed": False,
            "structure_is_descriptive_only": True, "causal_attribution_completed": False,
            "predictive_validation_completed": False, "pristine_external_holdout_claim": False,
            "predictive_model_fitted": False, "correlation_claim": False,
            "predictive_accuracy_computed": False, "statistical_significance_claim": False,
            "new_floquet_cells_computed": 0, "new_winding_computed": False, "n640_computed": False,
            "new_taxonomy_claim": False,
        },
        "log": "pair_inconsistency_structure_run.log",
    }
    (ROOT / "pair_inconsistency_structure_verification.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("\n".join(logs))
    print("pair_inconsistency_structure_overall", "passed" if passed else "failed", "check_only", check_only)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
