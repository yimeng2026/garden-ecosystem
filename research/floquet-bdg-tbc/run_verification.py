"""Reproduce TBC baselines, corrected disorder evidence, and bound report artifacts."""

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
DOCX_PY = Path("C:/Users/一梦/AppData/Roaming/kimi-desktop/daimon-share/daimon/runtime/kimi-code/home/plugins/managed/kimi-word/skills/kimi-word/scripts/docx.py")
DOCX = ROOT / "Floquet-BdG-TBC无序对照报告.docx"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    for name in ("tmp", "pycache", "matplotlib", "npm"):
        (CACHE / name).mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env.update({
        "TMP": str(CACHE / "tmp"), "TEMP": str(CACHE / "tmp"),
        "PYTHONPYCACHEPREFIX": str(CACHE / "pycache"),
        "MPLCONFIGDIR": str(CACHE / "matplotlib"), "NPM_CONFIG_CACHE": str(CACHE / "npm"),
        "OPENBLAS_NUM_THREADS": "1", "OMP_NUM_THREADS": "1",
        "PATH": r"C:\Program Files\nodejs" + os.pathsep + env.get("PATH", ""),
    })
    commands = [
        ("baseline_tests", [sys.executable, str(ROOT / "test_tbc.py"), "-v"], 120),
        ("baseline_compute", [sys.executable, str(ROOT / "run_tbc.py")], 120),
        ("baseline_independent", [sys.executable, str(ROOT / "verify_tbc.py")], 180),
        ("disorder_tests", [sys.executable, str(ROOT / "test_disorder.py"), "-v"], 120),
        ("disorder_checkpoint_integrity", [sys.executable, str(ROOT / "run_disorder.py"), "--merge-only"], 60),
        ("disorder_independent_recheck", [sys.executable, str(ROOT / "verify_disorder.py"), "--nominal-step", "0.05", "--output", "disorder_recheck.json"], 180),
        ("report_data_and_figures", [sys.executable, str(ROOT / "build_disorder_report.py")], 60),
        ("docx_structure_gate", [sys.executable, str(DOCX_PY), "validate", str(DOCX)], 120),
        ("visual_hash_binding", [sys.executable, str(ROOT / "record_word_qa.py")], 60),
        ("report_contracts", [sys.executable, str(ROOT / "test_report.py"), "-v"], 60),
        ("finite_size_suite", [sys.executable, str(ROOT / "run_finite_size_verification.py")], 180),
        ("n320_suite", [sys.executable, str(ROOT / "run_n320_verification.py")], 180),
        ("n400_suite", [sys.executable, str(ROOT / "run_scale_verification.py")], 180),
    ]
    rows, logs = [], []
    for label, command, timeout in commands:
        completed = subprocess.run(command, cwd=WORKTREE, env=env, text=True, encoding="utf-8", capture_output=True, timeout=timeout)
        output = completed.stdout + completed.stderr
        logs.extend([f"$ {label}: {' '.join(command)}", output.rstrip(), f"exit_code={completed.returncode}"])
        rows.append({"label": label, "command": command, "exit_code": completed.returncode})
        if completed.returncode != 0:
            break
    passed = len(rows) == len(commands) and all(row["exit_code"] == 0 for row in rows)
    (ROOT / "run.log").write_text("\n".join(logs) + "\n", encoding="utf-8")
    result_data = json.loads((ROOT / "results.json").read_text(encoding="utf-8"))
    disorder = json.loads((ROOT / "disorder_results.json").read_text(encoding="utf-8"))
    independent = json.loads((ROOT / "disorder_independent.json").read_text(encoding="utf-8"))
    recheck = json.loads((ROOT / "disorder_recheck.json").read_text(encoding="utf-8")) if (ROOT / "disorder_recheck.json").exists() else {}
    qa = json.loads((ROOT / "word-qa" / "report.json").read_text(encoding="utf-8"))
    finite_verification = json.loads((ROOT / "finite_verification.json").read_text(encoding="utf-8")) if (ROOT / "finite_verification.json").exists() else {}
    n320_verification = json.loads((ROOT / "n320_verification.json").read_text(encoding="utf-8")) if (ROOT / "n320_verification.json").exists() else {}
    n400_verification = json.loads((ROOT / "scale_verification.json").read_text(encoding="utf-8")) if (ROOT / "scale_verification.json").exists() else {}
    old_disorder = json.loads((ROOT.parent / "floquet-bdg-disorder" / "results.json").read_text(encoding="utf-8"))
    artifacts = [
        "results.json", "independent_verification.json", "disorder_results.json", "disorder_results.csv",
        "disorder_r0p05.json", "disorder_r0p10.json", "disorder_r0p20.json", "disorder_independent.json",
        "disorder_recheck.json", "disorder-winding.png", "disorder-gaps.png", "REPORT.md",
        "Floquet-BdG-TBC无序对照报告.docx", "word-qa/report.json", "run.log", "ERRATA.md",
        "finite_size_zero.json", "finite_size_independent.json", "finite_size_independent_controls.json",
        "finite_size_independent_remaining.json", "finite-size-winding.png", "finite-size-endpoints.png",
        "FINITE_SIZE.md", "Floquet-BdG-TBC有限尺寸报告.docx", "finite-word-qa/report.json",
        "finite_verification.json", "finite_run.log", "run_finite_size.py", "test_finite_size.py",
        "verify_finite_size.py", "build_finite_size_report.py", "build_finite_size_report.js",
        "record_finite_size_qa.py", "test_finite_size_report.py", "run_finite_size_verification.py",
        "n320_zero.json", "n320_independent.json", "n320_summary.json", "n320-winding.png", "n320-endpoints.png",
        "N320.md", "Floquet-BdG-TBC-N320定向报告.docx", "n320-word-qa/report.json",
        "n320_verification.json", "n320_run.log", "run_n320.py", "test_n320.py", "verify_n320.py",
        "build_n320_report.py", "build_n320_report.js", "record_n320_qa.py", "test_n320_report.py",
        "run_n320_verification.py", "spectral_benchmark.json",
        "scale_diagnostic.json", "scale_independent_n400.json", "n400_scale.json", "n400-result.png",
        "n400-coverage.png", "SCALE_DIAGNOSTIC.md", "Floquet-BdG-N400阈值诊断报告.docx",
        "n400-word-qa/report.json", "scale_verification.json", "scale_run.log", "resumable_winding.py",
        "run_scale_diagnostic.py", "verify_scale_diagnostic.py", "build_scale_report.py", "build_scale_report.js",
        "record_scale_qa.py", "test_scale_report.py", "run_scale_verification.py", "test_resumable.py",
        "scale_work/n400_zero_dtheta0p05.json", "scale_work/n400_zero_dtheta0p025.json",
        "tbc_model.py", "test_tbc.py", "run_tbc.py", "verify_tbc.py", "run_disorder.py",
        "test_disorder.py", "verify_disorder.py", "build_disorder_report.py", "build_report.js",
        "record_word_qa.py", "test_report.py",
    ]
    valid_count = sum(row[target]["status"] == "ok" for row in disorder["realizations"] for target in ("zero", "pi"))
    nc_count = sum(row[target]["status"] == "not_converged" for row in disorder["realizations"] for target in ("zero", "pi"))
    record = {
        "schema": "floquet-bdg-tbc-complete-verification-v2",
        "recorded_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "all_passed": passed,
        "test_counts": {"baseline": 9 if passed else None, "disorder": 8 if passed else None, "report": 5 if passed else None, "finite_unit": 4 if passed else None, "finite_report": 5 if passed else None, "n320_backend": 5 if passed else None, "n320_report": 5 if passed else None, "n400_resume": 5 if passed else None, "n400_report": 5 if passed else None},
        "commands": rows,
        "environment": {
            "python": platform.python_version(), "numpy": np.__version__, "scipy": scipy.__version__,
            "openblas_num_threads": "1", "cache_root": str(CACHE),
        },
        "sha256": {name: sha256(ROOT / name) for name in artifacts if (ROOT / name).exists()},
        "observed_status": result_data.get("status"),
        "disorder_status": disorder.get("status"),
        "independent_passed": independent.get("passed"),
        "recheck_passed": recheck.get("passed"),
        "visual_review_status": qa.get("manualReview", {}).get("status"),
        "rendered_pages": qa.get("rendered"),
        "main_winding_valid_count": valid_count,
        "main_winding_not_converged_count": nc_count,
        "finite_size_all_passed": finite_verification.get("all_passed"),
        "finite_size_independent_count": finite_verification.get("independent_count"),
        "n320_all_passed": n320_verification.get("all_passed"),
        "n320_independent_count": n320_verification.get("independent_count"),
        "n400_all_passed": n400_verification.get("all_passed"),
        "n400_independent_agreement": n400_verification.get("independent_agreement"),
        "scope": {
            "static_baseline_checked": passed, "clean_kicked_baseline_checked": passed,
            "disorder_evaluated": passed, "n160_zero_gap_evaluated": passed,
            "n320_tbc_winding_computed": passed, "n400_threshold_diagnostic_evaluated": passed,
            "n600_tail_growth_diagnostic_pending": True, "n640_tbc_winding_computed": False,
            "localization_scale_analysis_pending": False, "independent_disorder_realizations": 12,
            "paired_control_rows": 12, "uniform_controls_are_independent_random_samples": False,
            "double_kick_diagnostic_excluded": True,
            "old_disorder_assessment": old_disorder["assessment"]["status"],
            "old_full_size_rule_status": old_disorder["assessment"]["full_size_rule_status"],
            "thermodynamic_limit_proof": False, "interactions_or_dissipation": False,
            "material_tc_or_experiment": False,
        },
        "log": "run.log",
    }
    (ROOT / "verification.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("\n".join(logs))
    print("overall", "passed" if passed else "failed", "valid_winding", valid_count, "not_converged", nc_count)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
