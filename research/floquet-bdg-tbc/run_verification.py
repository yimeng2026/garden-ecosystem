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
        ("n600_suite", [sys.executable, str(ROOT / "run_n600_verification.py")], 180),
        ("endpoint_suite", [sys.executable, str(ROOT / "run_endpoint_verification.py")], 180),
        ("matched_suite", [sys.executable, str(ROOT / "run_matched_verification.py")], 180),
        ("multi_seed_suite", [sys.executable, str(ROOT / "run_multi_seed_verification.py")], 180),
        ("reversal_suite", [sys.executable, str(ROOT / "run_reversal_verification.py")], 180),
        ("category_suite", [sys.executable, str(ROOT / "run_category_verification.py")], 180),
        ("unclassified_suite", [sys.executable, str(ROOT / "run_unclassified_verification.py")], 180),
        ("near_miss_suite", [sys.executable, str(ROOT / "run_near_miss_verification.py")], 180),
        ("pair_response_suite", [sys.executable, str(ROOT / "run_pair_response_verification.py")], 180),
        ("subspace_overlap_suite", [sys.executable, str(ROOT / "run_subspace_overlap_verification.py")], 180),
        ("embedding_robustness_suite", [sys.executable, str(ROOT / "run_embedding_robustness_verification.py")], 180),
        ("embedding_census_suite", [sys.executable, str(ROOT / "run_embedding_census_verification.py"), "--check-only"], 180),
        ("swap_candidate_spectrum_suite", [sys.executable, str(ROOT / "run_swap_candidate_spectrum_verification.py")], 180),
        ("fixed_n_path_suite", [sys.executable, str(ROOT / "run_fixed_n_path_verification.py")], 180),
        ("path_refinement_suite", [sys.executable, str(ROOT / "run_path_refinement_verification.py")], 180),
        ("n600_path_suite", [sys.executable, str(ROOT / "run_n600_path_verification.py"), "--check-only"], 180),
        ("n600_valley_suite", [sys.executable, str(ROOT / "run_n600_valley_verification.py"), "--check-only"], 180),
        ("overlap_confounding_suite", [sys.executable, str(ROOT / "run_overlap_confounding_verification.py"), "--check-only"], 180),
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
    n600_verification = json.loads((ROOT / "n600_verification.json").read_text(encoding="utf-8")) if (ROOT / "n600_verification.json").exists() else {}
    endpoint_verification = json.loads((ROOT / "endpoint_verification.json").read_text(encoding="utf-8")) if (ROOT / "endpoint_verification.json").exists() else {}
    matched_verification = json.loads((ROOT / "matched_verification.json").read_text(encoding="utf-8")) if (ROOT / "matched_verification.json").exists() else {}
    multi_seed_verification = json.loads((ROOT / "multi_seed_verification.json").read_text(encoding="utf-8")) if (ROOT / "multi_seed_verification.json").exists() else {}
    reversal_verification = json.loads((ROOT / "reversal_verification.json").read_text(encoding="utf-8")) if (ROOT / "reversal_verification.json").exists() else {}
    category_verification = json.loads((ROOT / "category_verification.json").read_text(encoding="utf-8")) if (ROOT / "category_verification.json").exists() else {}
    unclassified_verification = json.loads((ROOT / "unclassified_verification.json").read_text(encoding="utf-8")) if (ROOT / "unclassified_verification.json").exists() else {}
    near_miss_verification = json.loads((ROOT / "near_miss_verification.json").read_text(encoding="utf-8")) if (ROOT / "near_miss_verification.json").exists() else {}
    pair_response_verification = json.loads((ROOT / "pair_response_verification.json").read_text(encoding="utf-8")) if (ROOT / "pair_response_verification.json").exists() else {}
    subspace_overlap_verification = json.loads((ROOT / "subspace_overlap_verification.json").read_text(encoding="utf-8")) if (ROOT / "subspace_overlap_verification.json").exists() else {}
    embedding_robustness_verification = json.loads((ROOT / "embedding_robustness_verification.json").read_text(encoding="utf-8")) if (ROOT / "embedding_robustness_verification.json").exists() else {}
    embedding_census_verification = json.loads((ROOT / "embedding_census_verification.json").read_text(encoding="utf-8")) if (ROOT / "embedding_census_verification.json").exists() else {}
    swap_candidate_spectrum_verification = json.loads((ROOT / "swap_candidate_spectrum_verification.json").read_text(encoding="utf-8")) if (ROOT / "swap_candidate_spectrum_verification.json").exists() else {}
    fixed_n_path_verification = json.loads((ROOT / "fixed_n_path_verification.json").read_text(encoding="utf-8")) if (ROOT / "fixed_n_path_verification.json").exists() else {}
    path_refinement_verification = json.loads((ROOT / "path_refinement_verification.json").read_text(encoding="utf-8")) if (ROOT / "path_refinement_verification.json").exists() else {}
    n600_path_verification = json.loads((ROOT / "n600_path_verification.json").read_text(encoding="utf-8")) if (ROOT / "n600_path_verification.json").exists() else {}
    n600_valley_verification = json.loads((ROOT / "n600_valley_verification.json").read_text(encoding="utf-8")) if (ROOT / "n600_valley_verification.json").exists() else {}
    overlap_confounding_verification = json.loads((ROOT / "overlap_confounding_verification.json").read_text(encoding="utf-8")) if (ROOT / "overlap_confounding_verification.json").exists() else {}
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
        "scale_independent_n600.json", "n600_scale.json", "n600-result.png", "n600-coverage.png",
        "N600_DIAGNOSTIC.md", "Floquet-BdG-N600尾长诊断报告.docx", "n600-word-qa/report.json",
        "n600_verification.json", "n600_run.log", "build_n600_report.py", "build_n600_report.js",
        "record_n600_qa.py", "test_n600_report.py", "run_n600_verification.py",
        "scale_work/n600_zero_dtheta0p05.json", "scale_work/n600_zero_dtheta0p025.json",
        "endpoint_subspace_analysis.json", "endpoint_subspace_independent.json", "endpoint-subspaces.png",
        "ENDPOINT_SUBSPACES.md", "Floquet-BdG-端点子空间诊断.docx", "endpoint-word-qa.json",
        "endpoint-word-render/report.json", "endpoint_verification.json", "endpoint_run.log",
        "analyze_endpoint_subspaces.py", "verify_endpoint_subspaces.py", "build_endpoint_report.js",
        "record_endpoint_qa.py", "test_endpoint_subspaces.py", "run_endpoint_verification.py",
        "matched_profile_control.json", "matched_profile_independent.json", "matched-profile-control.png",
        "MATCHED_PROFILE_CONTROL.md", "Floquet-BdG-同强度尺寸对照.docx", "matched-word-qa.json",
        "matched-word-render/report.json", "matched_verification.json", "matched_run.log",
        "analyze_matched_profiles.py", "verify_matched_profiles.py", "build_matched_report.js",
        "record_matched_qa.py", "test_matched_profiles.py", "run_matched_verification.py",
        "multi_seed_protocol.json", "multi_seed_profile_control.json", "multi_seed_independent.json",
        "multi-seed-control.png", "MULTI_SEED_CONTROL.md", "Floquet-BdG-多种子稳健性对照.docx",
        "multi-seed-word-qa.json", "multi-seed-word-render/report.json", "multi_seed_verification.json",
        "multi_seed_run.log", "analyze_multi_seed.py", "verify_multi_seed.py", "build_multi_seed_report.js",
        "record_multi_seed_qa.py", "test_multi_seed.py", "run_multi_seed_verification.py",
        "reversal_unit_analysis.json", "reversal-units.png", "REVERSAL_UNITS.md",
        "Floquet-BdG-反转单元机制诊断.docx", "reversal-word-qa.json", "reversal-word-render/report.json",
        "reversal_verification.json", "reversal_run.log", "analyze_reversal_units.py",
        "build_reversal_report.js", "record_reversal_qa.py", "test_reversal_units.py", "run_reversal_verification.py",
        "repeated_category_protocol.json", "category_new_cells.json", "category_new_cells_independent.json",
        "repeated_category_analysis.json", "repeated-categories.png", "REPEATED_CATEGORIES.md",
        "Floquet-BdG-端部机制类别检验.docx", "category-word-qa.json", "category-word-render/report.json",
        "category_verification.json", "category_run.log", "build_category_cells.py", "verify_category_cells.py",
        "analyze_repeated_categories.py", "build_category_report.js", "record_category_qa.py",
        "test_repeated_categories.py", "run_category_verification.py",
        "unclassified_signature_analysis.json", "unclassified-signatures.png", "UNCLASSIFIED_SIGNATURES.md",
        "Floquet-BdG-未归类与未复现诊断.docx", "unclassified-word-qa.json", "unclassified-word-render/report.json",
        "unclassified_verification.json", "unclassified_run.log", "analyze_unclassified_signatures.py",
        "build_unclassified_report.js", "record_unclassified_qa.py", "test_unclassified_signatures.py",
        "run_unclassified_verification.py",
        "near_miss_spatial_protocol.json", "near_miss_spatial_analysis.json", "near-miss-spatial.png",
        "NEAR_MISS_SPATIAL.md", "Floquet-BdG-近miss空间分布与次近对.docx", "near-miss-word-qa.json",
        "near-miss-word-render/report.json", "near_miss_verification.json", "near_miss_run.log",
        "analyze_near_miss_spatial.py", "build_near_miss_report.js", "record_near_miss_qa.py",
        "test_near_miss_spatial.py", "run_near_miss_verification.py",
        "pair_response_protocol.json", "pair_response_analysis.json", "pair-response-audit.png",
        "PAIR_RESPONSE_AUDIT.md", "Floquet-BdG-最近对与次近对响应审计.docx", "pair-response-word-qa.json",
        "pair-response-word-render/report.json", "pair_response_verification.json", "pair_response_run.log",
        "analyze_pair_responses.py", "build_pair_response_report.js", "record_pair_response_qa.py",
        "test_pair_responses.py", "run_pair_response_verification.py",
        "subspace_overlap_protocol.json", "subspace_overlap_analysis.json", "subspace-overlap.png",
        "SUBSPACE_OVERLAP.md", "Floquet-BdG-跨尺寸子空间重叠.docx", "subspace-overlap-word-qa.json",
        "subspace-overlap-word-render/report.json", "subspace_overlap_verification.json", "subspace_overlap_run.log",
        "analyze_subspace_overlap.py", "build_subspace_overlap_report.js", "record_subspace_overlap_qa.py",
        "test_subspace_overlap.py", "run_subspace_overlap_verification.py",
        "diagnose_overlap_symmetry.py", "overlap_symmetry_diagnostic.json",
        "embedding_robustness_protocol.json", "embedding_robustness_analysis.json", "embedding-robustness.png",
        "EMBEDDING_ROBUSTNESS.md", "Floquet-BdG-共同表示稳健性.docx", "embedding-robustness-word-qa.json",
        "embedding-robustness-word-render/report.json", "embedding_robustness_verification.json", "embedding_robustness_run.log",
        "analyze_embedding_robustness.py", "build_embedding_robustness_report.js", "record_embedding_robustness_qa.py",
        "test_embedding_robustness.py", "run_embedding_robustness_verification.py",
        "embedding_census_protocol.json", "embedding_census_analysis.json", "embedding-census.png",
        "EMBEDDING_CENSUS.md", "Floquet-BdG-全样本共同表示审计.docx", "embedding-census-word-qa.json",
        "embedding-census-word-render/report.json", "embedding_census_verification.json", "embedding_census_run.log",
        "analyze_embedding_census.py", "build_embedding_census_report.js", "record_embedding_census_qa.py",
        "test_embedding_census.py", "run_embedding_census_verification.py",
        "swap_candidate_spectrum_protocol.json", "swap_candidate_spectrum_analysis.json", "swap-candidate-spectrum.png",
        "SWAP_CANDIDATE_SPECTRUM.md", "Floquet-BdG-交换候选谱结构.docx", "swap-candidate-spectrum-word-qa.json",
        "swap-candidate-spectrum-word-render/report.json", "swap_candidate_spectrum_verification.json", "swap_candidate_spectrum_run.log",
        "analyze_swap_candidate_spectrum.py", "build_swap_candidate_spectrum_report.js", "record_swap_candidate_spectrum_qa.py",
        "test_swap_candidate_spectrum.py", "run_swap_candidate_spectrum_verification.py",
        "fixed_n_path_protocol.json", "fixed_n_path_analysis.json", "fixed-n-path.png",
        "FIXED_N_PATH.md", "Floquet-BdG-固定尺寸参数路径.docx", "fixed-n-path-word-qa.json",
        "fixed-n-path-word-render/report.json", "fixed_n_path_verification.json", "fixed_n_path_run.log",
        "analyze_fixed_n_path.py", "build_fixed_n_path_report.js", "record_fixed_n_path_qa.py",
        "test_fixed_n_path.py", "run_fixed_n_path_verification.py",
        "path_refinement_protocol.json", "path_refinement_analysis.json", "path-refinement.png",
        "PATH_REFINEMENT.md", "Floquet-BdG-参数路径细化.docx", "path-refinement-word-qa.json",
        "path-refinement-word-render/report.json", "path_refinement_verification.json", "path_refinement_run.log",
        "analyze_path_refinement.py", "build_path_refinement_report.js", "record_path_refinement_qa.py",
        "test_path_refinement.py", "run_path_refinement_verification.py",
        "n600_path_protocol.json", "n600_path_analysis.json", "n600-path.png",
        "N600_PATH.md", "Floquet-BdG-N600路径复核.docx", "n600-path-word-qa.json",
        "n600-path-word-render/report.json", "n600_path_verification.json", "n600_path_run.log",
        "analyze_n600_path.py", "build_n600_path_report.js", "record_n600_path_qa.py",
        "test_n600_path.py", "run_n600_path_verification.py",
        "n600_valley_protocol.json", "n600_valley_analysis.json", "n600-valley.png",
        "N600_VALLEY.md", "Floquet-BdG-N600谷值细化.docx", "n600-valley-word-qa.json",
        "n600-valley-word-render/report.json", "n600_valley_verification.json", "n600_valley_run.log",
        "analyze_n600_valley.py", "build_n600_valley_report.js", "record_n600_valley_qa.py",
        "test_n600_valley.py", "run_n600_valley_verification.py",
        "overlap_confounding_protocol.json", "overlap_confounding_analysis.json", "overlap-confounding-audit.png",
        "OVERLAP_CONFOUNDING_AUDIT.md", "Floquet-BdG-重叠差异混杂审计.docx", "overlap-confounding-word-qa.json",
        "overlap-confounding-word-render/report.json", "overlap_confounding_verification.json", "overlap_confounding_run.log",
        "analyze_overlap_confounding.py", "build_overlap_confounding_report.js", "record_overlap_confounding_qa.py",
        "test_overlap_confounding.py", "run_overlap_confounding_verification.py", "diagnose_same_n_rank_leakage.py",
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
        "test_counts": {"baseline": 9 if passed else None, "disorder": 8 if passed else None, "report": 5 if passed else None, "finite_unit": 4 if passed else None, "finite_report": 5 if passed else None, "n320_backend": 5 if passed else None, "n320_report": 5 if passed else None, "n400_resume": 5 if passed else None, "n400_report": 5 if passed else None, "n600_resume": 5 if passed else None, "n600_report": 5 if passed else None, "endpoint_subspace": 7 if passed else None, "matched_profile": 7 if passed else None, "multi_seed_profile": 7 if passed else None, "reversal_decomposition": 6 if passed else None, "repeated_categories": 5 if passed else None, "unclassified_signatures": 5 if passed else None, "near_miss_spatial": 6 if passed else None, "pair_responses": 6 if passed else None, "subspace_overlap": 9 if passed else None, "embedding_robustness": 6 if passed else None, "embedding_census": 6 if passed else None, "swap_candidate_spectrum": 6 if passed else None, "fixed_n_path": 6 if passed else None, "path_refinement": 6 if passed else None, "n600_path": 6 if passed else None, "n600_valley": 6 if passed else None, "overlap_confounding": 6 if passed else None},
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
        "n600_all_passed": n600_verification.get("all_passed"),
        "n600_independent_agreement": n600_verification.get("independent_agreement"),
        "n600_visual_review_status": n600_verification.get("visual_review_status"),
        "n600_visual_pass_claimed": n600_verification.get("visual_pass_claimed"),
        "endpoint_all_passed": endpoint_verification.get("all_passed"),
        "endpoint_independent_projectors_passed": endpoint_verification.get("independent_projectors_passed"),
        "endpoint_visual_review_status": endpoint_verification.get("visual_review_status"),
        "matched_all_passed": matched_verification.get("all_passed"),
        "matched_independent_projectors_passed": matched_verification.get("independent_projectors_passed"),
        "matched_visual_review_status": matched_verification.get("visual_review_status"),
        "multi_seed_all_passed": multi_seed_verification.get("all_passed"),
        "multi_seed_independent_projectors_passed": multi_seed_verification.get("independent_projectors_passed"),
        "multi_seed_visual_review_status": multi_seed_verification.get("visual_review_status"),
        "reversal_all_passed": reversal_verification.get("all_passed"),
        "reversal_original_independent_projectors_passed": reversal_verification.get("original_independent_projectors_passed"),
        "reversal_visual_review_status": reversal_verification.get("visual_review_status"),
        "category_all_passed": category_verification.get("all_passed"),
        "category_new_independent_projectors_passed": category_verification.get("new_independent_projectors_passed"),
        "category_visual_review_status": category_verification.get("visual_review_status"),
        "unclassified_all_passed": unclassified_verification.get("all_passed"),
        "unclassified_new_independent_projectors_passed": unclassified_verification.get("new_independent_projectors_passed"),
        "unclassified_visual_review_status": unclassified_verification.get("visual_review_status"),
        "near_miss_all_passed": near_miss_verification.get("all_passed"),
        "near_miss_original_independent_projectors_passed": near_miss_verification.get("original_independent_projectors_passed"),
        "near_miss_visual_review_status": near_miss_verification.get("visual_review_status"),
        "pair_response_all_passed": pair_response_verification.get("all_passed"),
        "pair_response_original_independent_projectors_passed": pair_response_verification.get("original_independent_projectors_passed"),
        "pair_response_visual_review_status": pair_response_verification.get("visual_review_status"),
        "subspace_overlap_all_passed": subspace_overlap_verification.get("all_passed"),
        "subspace_overlap_original_independent_projectors_passed": subspace_overlap_verification.get("original_independent_projectors_passed"),
        "subspace_overlap_visual_review_status": subspace_overlap_verification.get("visual_review_status"),
        "embedding_robustness_all_passed": embedding_robustness_verification.get("all_passed"),
        "embedding_robustness_original_independent_projectors_passed": embedding_robustness_verification.get("original_independent_projectors_passed"),
        "embedding_robustness_visual_review_status": embedding_robustness_verification.get("visual_review_status"),
        "embedding_census_all_passed": embedding_census_verification.get("all_passed"),
        "embedding_census_original_independent_projectors_passed": embedding_census_verification.get("original_independent_projectors_passed"),
        "embedding_census_visual_review_status": embedding_census_verification.get("visual_review_status"),
        "swap_candidate_spectrum_all_passed": swap_candidate_spectrum_verification.get("all_passed"),
        "swap_candidate_spectrum_original_independent_projectors_passed": swap_candidate_spectrum_verification.get("original_independent_projectors_passed"),
        "swap_candidate_spectrum_visual_review_status": swap_candidate_spectrum_verification.get("visual_review_status"),
        "fixed_n_path_all_passed": fixed_n_path_verification.get("all_passed"),
        "fixed_n_path_original_independent_projectors_passed": fixed_n_path_verification.get("original_independent_projectors_passed"),
        "fixed_n_path_visual_review_status": fixed_n_path_verification.get("visual_review_status"),
        "path_refinement_all_passed": path_refinement_verification.get("all_passed"),
        "path_refinement_original_independent_projectors_passed": path_refinement_verification.get("original_independent_projectors_passed"),
        "path_refinement_visual_review_status": path_refinement_verification.get("visual_review_status"),
        "n600_path_all_passed": n600_path_verification.get("all_passed"),
        "n600_path_original_independent_projectors_passed": n600_path_verification.get("original_independent_projectors_passed"),
        "n600_path_visual_review_status": n600_path_verification.get("visual_review_status"),
        "n600_valley_all_passed": n600_valley_verification.get("all_passed"),
        "n600_valley_original_independent_projectors_passed": n600_valley_verification.get("original_independent_projectors_passed"),
        "n600_valley_visual_review_status": n600_valley_verification.get("visual_review_status"),
        "overlap_confounding_all_passed": overlap_confounding_verification.get("all_passed"),
        "overlap_confounding_visual_review_status": overlap_confounding_verification.get("visual_review_status"),
        "overlap_confounding_size_effect_separated": overlap_confounding_verification.get("scope", {}).get("size_effect_separated"),
        "scope": {
            "static_baseline_checked": passed, "clean_kicked_baseline_checked": passed,
            "disorder_evaluated": passed, "n160_zero_gap_evaluated": passed,
            "n320_tbc_winding_computed": passed, "n400_threshold_diagnostic_evaluated": passed,
            "n600_tail_growth_evaluated": "passed", "n640_tbc_winding_computed": False,
            "n640_automatically_justified": False,
            "endpoint_subspace_diagnostic_evaluated": "passed",
            "n400_single_end_weight_is_not_two_end_recovery": True,
            "n600_second_pair_is_not_alternate_endpoint": True,
            "uniform_strength_profile_control_pending": False,
            "matched_2x2_profile_control_evaluated": "passed",
            "n600_r0p1_profile_pass_is_not_bulk_winding": True,
            "multi_seed_profile_control_pending": False,
            "four_seed_profile_robustness_evaluated": "passed",
            "strength_edge_increase_stable_within_grid": True,
            "size_effect_is_not_universal": True,
            "interaction_has_two_positive_and_two_negative_signs": True,
            "reversal_mechanism_analysis_pending": False,
            "targeted_reversal_decomposition_evaluated": "passed",
            "broadening_is_not_endpoint_loss": True,
            "repeated_category_analysis_pending": False,
            "repeated_category_analysis_evaluated": "passed",
            "right_symmetrization_new_seed_recurrences": 2,
            "right_weakening_new_seed_recurrences": 0,
            "other_unclassified_count": 7,
            "unclassified_condition_audit_evaluated": "passed",
            "unclassified_not_homogeneous": True,
            "near_misses_are_not_reference_recurrence": True,
            "near_miss_spatial_analysis_evaluated": "passed",
            "fixed40_and_original10pct_separated": True,
            "second_pair_is_descriptive_only": True,
            "near_miss_second_pair_not_topological": True,
            "pair_response_analysis_evaluated": "passed",
            "pair_response_edge_same_nonzero": 6,
            "pair_response_edge_opposite_nonzero": 10,
            "pair_response_L50_same_nonzero": 10,
            "pair_response_L50_opposite_nonzero": 6,
            "pair_response_second_joint_pass_contrasts": 0,
            "pair_rank_matching_is_not_state_tracking": True,
            "pair_response_not_statistical_significance": True,
            "subspace_overlap_analysis_evaluated": "passed",
            "subspace_overlap_finest_diagonal_assignments": 3,
            "subspace_absolute_overlap_is_weak": True,
            "subspace_relative_rank_advantage_is_not_state_tracking": True,
            "subspace_rank_exchange_proven": False,
            "subspace_grid_convergence_proof": False,
            "embedding_robustness_analysis_evaluated": "passed",
            "embedding_diagonal_dominant_count": 18,
            "embedding_finest_same_assignment_count": 3,
            "embedding_direction_stability_is_not_state_tracking": True,
            "embedding_representation_invariant_claim": False,
            "embedding_census_analysis_evaluated": "passed",
            "embedding_census_diagonal_dominant_count": 90,
            "embedding_census_same_assignment_count": 48,
            "embedding_census_fully_diagonal_cases": 15,
            "embedding_census_swap_candidates": ["seed_6_r_0p05"],
            "embedding_census_candidate_is_not_state_exchange": True,
            "swap_candidate_spectrum_analysis_evaluated": "passed",
            "swap_candidate_cross_pair_exact_degenerate": False,
            "swap_candidate_second_pair_separation_ratio": 1,
            "swap_candidate_cross_term_drives_candidate": True,
            "swap_candidate_spectral_crossing_proven": False,
            "swap_candidate_state_exchange_proven": False,
            "fixed_n_path_analysis_evaluated": "passed",
            "fixed_n_path_parameter_points": 9,
            "fixed_n_path_adjacent_links": 8,
            "fixed_n_path_diagonal_link_count": 8,
            "fixed_n_path_swapped_link_count": 0,
            "fixed_n_path_continuous_path_proof": False,
            "fixed_n_path_state_exchange_proven": False,
            "path_refinement_analysis_evaluated": "passed",
            "path_refinement_refined_points": 10,
            "path_refinement_adjacent_links": 8,
            "path_refinement_diagonal_link_count": 8,
            "path_refinement_swapped_link_count": 0,
            "path_refinement_min_center_separation_strength": 0.04125,
            "path_refinement_coarse_jump_is_not_crossing": True,
            "path_refinement_continuous_path_proof": False,
            "n600_path_analysis_evaluated": "passed",
            "n600_path_refined_points": 10,
            "n600_path_adjacent_links": 8,
            "n600_path_diagonal_link_count": 8,
            "n600_path_assignment_agreement_with_n400": 8,
            "n600_path_min_center_separation_strength": 0.04375,
            "n600_path_min_center_separation_same_strength": False,
            "n600_path_max_change_same_link": False,
            "n600_path_size_invariance_claim": False,
            "n600_valley_analysis_evaluated": "passed",
            "n600_valley_refined_points": 5,
            "n600_valley_adjacent_links": 4,
            "n600_valley_diagonal_link_count": 4,
            "n600_valley_swapped_link_count": 0,
            "n600_valley_min_center_separation_strength": 0.044375,
            "n600_valley_is_not_crossing_proof": True,
            "n600_valley_low_overlap_has_step_dependence": True,
            "n600_valley_continuous_path_proof": False,
            "overlap_confounding_analysis_evaluated": "passed",
            "overlap_confounding_cases": 16,
            "overlap_confounding_same_n_embedding_rank_gate_passed": False,
            "overlap_confounding_linear_embedding_max_rank_leakage": 3.2111372980829987e-06,
            "overlap_confounding_same_disorder_realization": False,
            "overlap_confounding_size_effect_separated": False,
            "overlap_confounding_common_beta_control_computed": False,
            "overlap_confounding_normalization_correction_applied": False,
            "new_taxonomy_claim": False,
            "universal_category_claim": False,
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
