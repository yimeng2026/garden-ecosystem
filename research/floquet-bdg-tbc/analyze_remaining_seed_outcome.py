"""Generate one preregistered remaining-seed path outcome without candidate scoring."""

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from analyze_seed6_matrix_path import build_links, driver_summary, entry_extrema, evaluate_path, link_summary, sha  # noqa: E402
from analyze_seed6_matrix_midpoint import driver_comparisons, jump_comparisons  # noqa: E402

PROTOCOL = ROOT / "remaining_seed_outcome_protocol.json"
CANDIDATES = ROOT / "profile_stat_candidates_analysis.json"
REPORT_DATE = "2026-11-12"
ENTRIES = ((0, 0), (0, 1), (1, 0), (1, 1))
plt.rcParams.update({
    "font.sans-serif": ["Microsoft YaHei", "SimHei", "Noto Sans CJK SC", "DejaVu Sans"],
    "axes.unicode_minus": False, "font.size": 9, "figure.dpi": 160,
})


def output_paths(seed):
    return {
        "analysis": ROOT / f"remaining_seed{seed}_path_outcome_analysis.json",
        "figure": ROOT / f"remaining-seed{seed}-outcome.png",
        "markdown": ROOT / f"REMAINING_SEED{seed}_OUTCOME.md",
    }


def endpoint_binding(seed, cells, matrices, protocol):
    max_matrix = 0.0
    max_singular = 0.0
    max_spectrum = 0.0
    for strength, filename in protocol["endpoint_sources_by_seed"][str(seed)].items():
        strength = float(strength)
        source = json.loads((ROOT / filename).read_text(encoding="utf-8"))
        source_row = next(row for row in source["realizations"] if row["seed"] == seed and row["strength"] == strength)
        for method in protocol["methods"]:
            for m in protocol["common_grids"]:
                actual = next(row for row in matrices if row["strength"] == strength and row["method"] == method and row["m"] == m)
                expected = next(row for row in source_row["methods"][method]["grids"] if row["m"] == m)
                for i, j in ENTRIES:
                    a, e = actual["overlap_matrix"][i][j], expected["overlap_matrix"][i][j]
                    max_matrix = max(max_matrix, abs(a["overlap"] - e["overlap"]))
                    max_singular = max(max_singular, max(abs(x - y) for x, y in zip(a["singular_values"], e["singular_values"])))
        for n in protocol["n_values"]:
            actual_cell = next(cell for cell in cells if cell["strength"] == strength and cell["n"] == n)
            expected_cell = next(cell for cell in source_row["cells"] if cell["n"] == n)
            max_spectrum = max(max_spectrum, max(abs(x - y) for x, y in zip(actual_cell["spectrum_first_six"], expected_cell["spectrum_first_six"])))
    return {
        "max_matrix_absolute_error": max_matrix,
        "max_singular_absolute_error": max_singular,
        "max_spectrum_absolute_error": max_spectrum,
        "endpoint_recomputation_is_not_new_realization": True,
    }


def figure(data, path):
    seed = data["seed"]
    strengths = [row["strength"] for row in data["cells"] if row["n"] == 400]
    midpoints = [(a + b) / 2 for a, b in zip(strengths[:-1], strengths[1:])]
    fig, axes = plt.subplots(2, 2, figsize=(14, 9.6))
    for method, color, marker in (("linear_point", "#356A64", "o"), ("cell_average", "#A25B3F", "s")):
        values = [next(row for row in data["path_matrices"] if row["strength"] == strength and row["method"] == method and row["m"] == 4800)["overlap_matrix"][0][0]["overlap"] for strength in strengths]
        axes[0, 0].plot(strengths, values, color=color, marker=marker, label=method)
    axes[0, 0].set_yscale("log")
    axes[0, 0].set_title("O00：两种表示的路径")
    axes[0, 0].set_ylabel("O00（对数）")
    axes[0, 0].legend(frameon=False, fontsize=8)
    for (i, j), label, color in (((0, 1), "O01", "#356A64"), ((1, 0), "O10", "#A25B3F")):
        for method, linestyle in (("linear_point", "-"), ("cell_average", "--")):
            values = [next(row for row in data["path_matrices"] if row["strength"] == strength and row["method"] == method and row["m"] == 4800)["overlap_matrix"][i][j]["overlap"] for strength in strengths]
            axes[0, 1].plot(strengths, values, color=color, ls=linestyle, marker="o", ms=3.5, label=f"{label} {method}")
    axes[0, 1].set_yscale("log")
    axes[0, 1].set_title("O01／O10：路径响应")
    axes[0, 1].set_ylabel("重叠（对数）")
    axes[0, 1].legend(frameon=False, fontsize=7)
    summary = data["summary"]
    axes[1, 0].bar([0, 1], [summary["jump_change_count"], summary["driver_comparison_change_count"]], color=["#356A64", "#A25B3F"], width=0.55)
    axes[1, 0].set_xticks([0, 1], ["跳变改变数（8项）", "主导计数改变数（4组）"])
    axes[1, 0].set_ylim(0, 8.8)
    axes[1, 0].set_ylabel("数量")
    axes[1, 0].set_title("原始9点与细化13点对照")
    axes[1, 0].grid(alpha=0.2, axis="y")
    for n, color in ((400, "#356A64"), (600, "#A25B3F")):
        rows = [row for row in data["links"] if row["n"] == n]
        axes[1, 1].plot(midpoints, [row["diagonal_score"] for row in rows], color=color, marker="o", ms=3.5, label=f"N={n}同谱秩")
        axes[1, 1].plot(midpoints, [row["swapped_score"] for row in rows], color=color, ls="--", marker="s", ms=3.5, label=f"N={n}交换")
    axes[1, 1].set_yscale("log")
    axes[1, 1].set_title("同尺寸相邻强度原生重叠")
    axes[1, 1].set_ylabel("得分（对数）")
    axes[1, 1].legend(frameon=False, fontsize=7)
    for axis in (axes[0, 0], axes[0, 1], axes[1, 1]):
        axis.set_xlabel("无序强度 r")
        axis.grid(alpha=0.2, which="both")
    fig.subplots_adjust(top=0.89, bottom=0.13, left=0.08, right=0.98, hspace=0.44, wspace=0.25)
    fig.suptitle(f"seed={seed} 剩余种子路径结局（不作候选验证）", fontsize=16, y=0.97)
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def markdown(data, path):
    summary = data["summary"]
    seed = data["seed"]
    lines = [
        f"# Floquet-BdG seed={seed} 剩余种子路径结局",
        "",
        f"> 日期：{REPORT_DATE}。seed={seed} 使用既有主剖面，计算13点路径的26个尺寸单元、78组跨尺寸矩阵和24条原生链接。本报告只生成路径结局，不作候选验证。不补算体 winding，未计算 N=640。",
        "",
        "## 一、预登记路径结局",
        "",
        "原9点／8链接与细化13点／12链接逐种子比较，保留全部点、链接和主导项，不归一化，不筛选有利路径段。候选名单与逐对方向规则已在计算前冻结，但必须等 seed=2、3、4、5、7 的结局全部存在后才能执行。",
        "",
        "| seed | 尺寸单元 | 跨尺寸矩阵 | 原生链接 | 跳变改变数（8项） | 主导计数改变数（4组） | 新中点参与极值数 |",
        "|---:|---:|---:|---:|---:|---:|---:|",
        f"| {seed} | {data['new_control_cells']} | {len(data['path_matrices'])} | {len(data['links'])} | {summary['jump_change_count']} | {summary['driver_comparison_change_count']} | {summary['new_extrema_midpoint_count']} |",
        "",
        "图 1 插入位置：路径结局汇总之后、逐项比较之前。",
        "",
        f"![图 1：seed={seed} 剩余种子路径结局](remaining-seed{seed}-outcome.png)",
        "",
        "**图 1**　O00、O01／O10 路径、步长改变计数及同尺寸原生重叠。本图不作候选验证。",
        "",
        "## 二、逐项跳变比较",
        "",
        "| 方法 | 项 | 原最大跳变及链接 | 细化最大跳变及链接 | 改变 |",
        "|:---|:---:|---:|---:|:---:|",
    ]
    for row in data["jump_comparisons"]:
        lines.append(f"| {row['method']} | {row['entry']} | {row['original_max_adjacent_absolute_jump']:.6g}（{row['original_jump_from']}→{row['original_jump_to']}） | {row['refined_max_adjacent_absolute_jump']:.6g}（{row['refined_jump_from']}→{row['refined_jump_to']}） | {row['jump_changed']} |")
    lines += [
        "",
        "## 三、证据边界",
        "",
        "既有候选值曾在描述统计中出现，因此本设计不是完全未触碰的外部验证集；只有路径跳变结局是新生成的。它至多是结局盲的逐对方向检验，不是外部实验重复、预测模型或统计显著性检验。",
        "",
        f"端点矩阵、主奇异值和前六谱分量的最大绑定误差分别为 {data['endpoint_binding']['max_matrix_absolute_error']}、{data['endpoint_binding']['max_singular_absolute_error']} 和 {data['endpoint_binding']['max_spectrum_absolute_error']}。端点重算不新增无序实现。",
        "",
        "在五个剩余种子结局齐备之前，不输出候选通过、淘汰、相关性、预测准确率或显著性结论。本报告也不能外推为连续路径、真实态交换、谱交叉、普遍尺寸律、因果机制或热力学极限结论。",
        "",
        f"复现：`python research/floquet-bdg-tbc/analyze_remaining_seed_outcome.py --seed {seed}`。完整路径与结局保存在 `remaining_seed{seed}_path_outcome_analysis.json`。",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def check_only(seed):
    stored = json.loads(output_paths(seed)["analysis"].read_text(encoding="utf-8"))
    if stored.get("protocol_sha256") != sha(PROTOCOL) or stored.get("candidate_source_analysis_sha256") != sha(CANDIDATES):
        raise ValueError("Remaining-seed outcome evidence is stale")
    if len(stored.get("cells", [])) != 26 or len(stored.get("path_matrices", [])) != 78 or len(stored.get("links", [])) != 24 or len(stored.get("entry_links", [])) != 288:
        raise ValueError("Remaining-seed outcome evidence is incomplete")
    if not stored.get("candidate_evaluation_deferred") or stored.get("candidate_validation_completed"):
        raise ValueError("Candidate evaluation occurred before all remaining outcomes existed")
    print(json.dumps({"check_only": True, "seed": seed, "cells": 26, "path_matrices": 78, "native_links": 24, "entry_links": 288, "jump_change_count": stored["summary"]["jump_change_count"], "candidate_evaluation_deferred": True, "all_passed": True}, ensure_ascii=False))
    return 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, required=True, choices=[2, 3, 4, 5, 7])
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args()
    if args.check_only:
        return check_only(args.seed)
    seed = args.seed
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    local = dict(protocol, seed=seed)
    cells, bases_by_key, matrices, fidelity, rank_controls, max_direction = evaluate_path(local)
    links, method_links, entry_links = build_links(local, cells, bases_by_key, matrices)
    for collection in (cells, matrices, links, method_links, entry_links, fidelity, rank_controls):
        for row in collection:
            row["seed"] = seed
    for cell in cells:
        cell["new_for_path"] = True
        cell["evidence_role"] = "remaining_seed_path_outcome"
    new_midpoints = set(protocol["new_midpoint_strengths"])
    original_matrices = [row for row in matrices if row["strength"] not in new_midpoints]
    original_method_links = [row for row in method_links if row["from"] not in new_midpoints and row["to"] not in new_midpoints]
    original_entry_links = [row for row in entry_links if row["from"] not in new_midpoints and row["to"] not in new_midpoints]
    original_native_links = [row for row in links if row["from"] not in new_midpoints and row["to"] not in new_midpoints]
    original_extrema = entry_extrema(original_matrices, original_entry_links)
    extrema = entry_extrema(matrices, entry_links)
    original_drivers = driver_summary(original_method_links)
    drivers = driver_summary(method_links)
    for collection in (original_extrema, extrema, original_drivers, drivers):
        for row in collection:
            row["seed"] = seed
    jumps = jump_comparisons(original_extrema, extrema, protocol["new_midpoint_strengths"])
    for row in jumps:
        row["seed"] = seed
        row["original_max_adjacent_absolute_jump"] = row.pop("old_max_adjacent_absolute_jump")
        row["original_jump_from"] = row.pop("old_jump_from")
        row["original_jump_to"] = row.pop("old_jump_to")
    driver_changes = driver_comparisons(original_drivers, drivers)
    for row in driver_changes:
        row["seed"] = seed
        row["original_dominant_entry_counts"] = row.pop("old_dominant_entry_counts")
        row["original_link_count"] = row.pop("old_link_count")
        row["original_score_ratio_range"] = row.pop("old_score_ratio_range")
    links_summary = link_summary(links)
    original_links_summary = link_summary(original_native_links)
    for row in links_summary + original_links_summary:
        row["seed"] = seed
    summary = {
        "cross_size_assignment_counts": {method: dict(Counter(row["dominant_assignment"] for row in matrices if row["method"] == method)) for method in protocol["methods"]},
        "max_direction_absolute_error": max_direction,
        "max_representation_direction_absolute_error": max(row["direction_absolute_error"] for row in fidelity),
        "min_representation_fidelity": min(row["forward"] for row in fidelity),
        "max_representation_fidelity": max(row["forward"] for row in fidelity),
        "max_native_off_diagonal": max(row["off01"] for row in rank_controls if row["method"] == "native_qr"),
        "max_linear_point_off_diagonal": max(row["off01"] for row in rank_controls if row["method"] == "linear_point"),
        "max_cell_average_off_diagonal": max(row["off01"] for row in rank_controls if row["method"] == "cell_average"),
        "method_grid_assignment_change_count": sum(row["before_dominant_assignment"] != row["after_dominant_assignment"] for row in method_links),
        "jump_change_count": sum(row["jump_changed"] for row in jumps),
        "driver_comparison_change_count": sum(row["driver_counts_changed"] for row in driver_changes),
        "new_extrema_midpoint_count": sum(row["min_strength"] in new_midpoints or row["max_strength"] in new_midpoints for row in extrema),
    }
    master = np.random.default_rng(20261111 + seed).random(protocol["master_grid"])
    data = {
        "schema": "floquet-bdg-remaining-seed-path-outcome-v1",
        "analysis_date": protocol["analysis_date"], "report_date": REPORT_DATE, "seed": seed,
        "protocol_sha256": sha(PROTOCOL), "candidate_source_analysis_sha256": sha(CANDIDATES),
        "batch_a_analysis_sha256": sha(ROOT / "matched_beta_batch_a_analysis.json"),
        "batch_b_analysis_sha256": sha(ROOT / "matched_beta_batch_b_analysis.json"),
        "batch_c_analysis_sha256": sha(ROOT / "matched_beta_batch_c_analysis.json"),
        "master_profile": [float(value) for value in master],
        "master_profile_sha256": hashlib.sha256(master.tobytes()).hexdigest(),
        "cells": cells, "path_matrices": matrices, "links": links,
        "method_grid_links": method_links, "entry_links": entry_links,
        "original_entry_extrema": original_extrema, "entry_extrema": extrema,
        "original_driver_summary": original_drivers, "driver_summary": drivers,
        "jump_comparisons": jumps, "driver_comparisons": driver_changes,
        "original_link_summary": original_links_summary, "link_summary": links_summary,
        "representation_fidelity": fidelity, "rank_controls": rank_controls,
        "summary": summary, "endpoint_binding": endpoint_binding(seed, cells, matrices, protocol),
        "new_control_cells": 26, "evaluated_control_cells": 26, "new_floquet_cells_computed": 26,
        "new_path_seed_count": 1, "new_disorder_realization_count": 0,
        "not_merged_into_batch_counts": True, "all_preregistered_results_retained": True,
        "candidate_evaluation_deferred": True, "candidate_validation_completed": False,
        "holdout_pair_evaluations": [], "pristine_external_holdout_claim": False,
        "predictive_model_fitted": False, "correlation_claim": False,
        "statistical_significance_claim": False, "causal_mechanism_proven": False,
        "continuous_path_proof": False, "spectral_crossing_proven": False,
        "avoided_crossing_claim": False, "state_exchange_proven": False,
        "thermodynamic_limit_proof": False, "universal_size_law_claim": False,
        "new_winding_computed": False, "n640_computed": False,
        "new_taxonomy_claim": False, "categories_changed": False,
        "normalization_correction_applied": False, "representation_invariant_claim": False,
        "old_candidate_is_different_realization": True,
    }
    paths = output_paths(seed)
    paths["analysis"].write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    figure(data, paths["figure"])
    markdown(data, paths["markdown"])
    print(json.dumps({"seed": seed, "summary": summary, "endpoint_binding": data["endpoint_binding"], "cells": 26, "path_matrices": 78, "native_links": 24, "entry_links": 288, "candidate_evaluation_deferred": True}, ensure_ascii=False, indent=2))
    print(f"generated {paths['analysis'].name} {paths['figure'].name} {paths['markdown'].name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
