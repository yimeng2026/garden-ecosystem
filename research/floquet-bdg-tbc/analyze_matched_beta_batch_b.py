"""Batch-B matched-beta controls with single-anchor reuse and unique A+B coverage."""

import hashlib
import json
from collections import Counter
from pathlib import Path
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
import numpy as np

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from analyze_matched_beta_batch_a import (  # noqa: E402
    assignment_pattern, compare_strengths, evaluate_realization, fmt, pattern_text, sha, summarize,
)

PROTOCOL = ROOT / "matched_beta_batch_b_protocol.json"
ANCHOR = ROOT / "matched_beta_control_analysis.json"
BATCH_A = ROOT / "matched_beta_batch_a_analysis.json"
CANDIDATE = ROOT / "swap_candidate_spectrum_analysis.json"
REPORT_DATE = "2026-11-12"
plt.rcParams.update({
    "font.sans-serif": ["Microsoft YaHei", "SimHei", "Noto Sans CJK SC", "DejaVu Sans"],
    "axes.unicode_minus": False, "font.size": 9, "figure.dpi": 160,
})


def reuse_anchor(source):
    methods = source["methods"]
    patterns = {method: assignment_pattern(methods[method]["grids"]) for method in methods}
    summary = source["summary"]
    return {
        "seed": 6, "strength": 0.05,
        "evidence_role": "reused_anchor", "recomputed_for_new_analysis": False,
        "source_analysis": ANCHOR.name, "source_analysis_sha256": sha(ANCHOR),
        "master_profile": source["master_profile"], "master_profile_sha256": source["master_profile_sha256"],
        "strength_pair_master_reused": True,
        "cells": source["cells"], "methods": methods,
        "representation_fidelity": source["representation_fidelity"],
        "native_rank_controls": source["native_rank_controls"], "rank_controls": source["rank_controls"],
        "max_direction_absolute_error": summary["max_direction_absolute_error"],
        "max_representation_direction_absolute_error": summary["max_representation_direction_absolute_error"],
        "min_representation_fidelity": summary["min_representation_fidelity"],
        "max_representation_fidelity": summary["max_representation_fidelity"],
        "max_native_off_diagonal": summary["max_native_off_diagonal"],
        "max_linear_point_off_diagonal": summary["max_linear_point_off_diagonal"],
        "max_cell_average_off_diagonal": summary["max_cell_average_off_diagonal"],
        "center_separation_delta": summary["center_separation_delta"],
        "assignment_patterns": patterns,
        "same_rank_all_grids_both_methods": all(value == "diagonal_3_of_3" for value in patterns.values()),
        "method_agreement_all_grids": all(
            methods["linear_point"]["grids"][index]["dominant_assignment"] == methods["cell_average"]["grids"][index]["dominant_assignment"]
            for index in range(3)
        ),
    }


def combined_summary(batch_a, batch_b):
    assignment_counts = {}
    for method in ("linear_point", "cell_average"):
        counts = Counter(batch_a["summary"]["assignment_counts"][method])
        counts.update(batch_b["summary"]["assignment_counts"][method])
        assignment_counts[method] = dict(counts)
    keys_a = {(row["seed"], row["strength"]) for row in batch_a["realizations"]}
    keys_b = {(row["seed"], row["strength"]) for row in batch_b["realizations"]}
    if keys_a & keys_b:
        raise ValueError(f"Duplicate A+B realization keys: {sorted(keys_a & keys_b)}")
    lower = min(batch_a["summary"]["center_separation_delta_range"][0], batch_b["summary"]["center_separation_delta_range"][0])
    upper = max(batch_a["summary"]["center_separation_delta_range"][1], batch_b["summary"]["center_separation_delta_range"][1])
    return {
        "realization_count": len(keys_a | keys_b), "control_cells": 2 * len(keys_a | keys_b),
        "unique_seed_strength_keys": True, "anchor_count": 1,
        "assignment_counts": assignment_counts,
        "same_rank_all_grids_both_methods_count": batch_a["summary"]["same_rank_all_grids_both_methods_count"] + batch_b["summary"]["same_rank_all_grids_both_methods_count"],
        "method_agreement_all_grids_count": batch_a["summary"]["method_agreement_all_grids_count"] + batch_b["summary"]["method_agreement_all_grids_count"],
        "min_representation_fidelity": min(batch_a["summary"]["min_representation_fidelity"], batch_b["summary"]["min_representation_fidelity"]),
        "max_representation_fidelity": max(batch_a["summary"]["max_representation_fidelity"], batch_b["summary"]["max_representation_fidelity"]),
        "center_separation_delta_range": [lower, upper],
        "size_effect_separated": "matched_nested_profile_descriptive_only",
        "universal_size_law_claim": False, "statistical_significance_claim": False,
        "spectral_crossing_proven": False, "state_exchange_proven": False,
    }


def figure(data):
    rows = data["realizations"]
    labels = [f"s{row['seed']} / r={row['strength']:g}" for row in rows]
    x = np.arange(len(rows))
    anchor_index = next(index for index, row in enumerate(rows) if row["evidence_role"] == "reused_anchor")
    fig, axes = plt.subplots(2, 2, figsize=(14, 9.6))
    for axis in (axes[0, 0], axes[0, 1], axes[1, 0]):
        axis.axvspan(anchor_index - 0.45, anchor_index + 0.45, color="#D7DCDD", alpha=0.55, zorder=0)
    axes[0, 0].text(anchor_index, 0.98, "复用锚点", transform=axes[0, 0].get_xaxis_transform(), ha="center", va="top", fontsize=8, color="#4F5E63")
    for method, color, marker, offset in (("linear_point", "#356A64", "o", -0.10), ("cell_average", "#A25B3F", "s", 0.10)):
        axes[0, 0].scatter(x + offset, [row["methods"][method]["grids"][-1]["diagonal_score"] for row in rows], color=color, marker=marker, label=f"{method}同谱秩")
        axes[0, 0].scatter(x + offset, [row["methods"][method]["grids"][-1]["swapped_score"] for row in rows], facecolors="none", edgecolors=color, marker=marker, label=f"{method}交换")
    axes[0, 0].set_xticks(x, labels, rotation=35, ha="right")
    axes[0, 0].set_yscale("log")
    axes[0, 0].set_title("M=4800：第二批逐实现分配得分")
    axes[0, 0].set_ylabel("重叠得分（对数）")
    axes[0, 0].grid(alpha=0.2, which="both")
    axes[0, 0].legend(frameon=False, fontsize=7, ncol=2)
    columns = [(method, index) for method in ("linear_point", "cell_average") for index in range(3)]
    mapping = {"swapped": -1, "tie_exact": 0, "diagonal": 1}
    matrix = np.asarray([[mapping[row["methods"][method]["grids"][index]["dominant_assignment"]] for method, index in columns] for row in rows])
    axes[0, 1].imshow(matrix, cmap=ListedColormap(["#A25B3F", "#D7DCDD", "#356A64"]), vmin=-1, vmax=1, aspect="auto")
    axes[0, 1].plot([-0.5, 5.5, 5.5, -0.5, -0.5], [anchor_index - 0.5, anchor_index - 0.5, anchor_index + 0.5, anchor_index + 0.5, anchor_index - 0.5], color="#D7DCDD", lw=2.2)
    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            axes[0, 1].text(j, i, {1: "D", -1: "S", 0: "T"}[matrix[i, j]], ha="center", va="center", color="white" if matrix[i, j] else "black", fontsize=8)
    axes[0, 1].set_xticks(np.arange(6), ["LP\n1200", "LP\n2400", "LP\n4800", "CA\n1200", "CA\n2400", "CA\n4800"])
    axes[0, 1].set_yticks(x, labels)
    axes[0, 1].set_title("全部网格方向（边框标出复用锚点）")
    for n, color, marker in ((400, "#356A64", "o"), (600, "#A25B3F", "s")):
        axes[1, 0].scatter(x, [next(cell["center_separation"] for cell in row["cells"] if cell["n"] == n) for row in rows], color=color, marker=marker, label=f"N={n}")
    axes[1, 0].set_xticks(x, labels, rotation=35, ha="right")
    axes[1, 0].set_yscale("log")
    axes[1, 0].set_title("两对谱距离中心的间隔")
    axes[1, 0].set_ylabel("中心间隔（对数）")
    axes[1, 0].grid(alpha=0.2, which="both")
    axes[1, 0].legend(frameon=False)
    combined = data["combined_with_batch_a"]["assignment_counts"]
    positions = np.arange(2)
    diagonal = [combined[method].get("diagonal", 0) for method in ("linear_point", "cell_average")]
    swapped = [combined[method].get("swapped", 0) for method in ("linear_point", "cell_average")]
    ties = [combined[method].get("tie_exact", 0) for method in ("linear_point", "cell_average")]
    axes[1, 1].bar(positions, diagonal, color="#356A64", label="同谱秩")
    axes[1, 1].bar(positions, swapped, bottom=diagonal, color="#A25B3F", label="交换")
    axes[1, 1].bar(positions, ties, bottom=np.asarray(diagonal) + np.asarray(swapped), color="#B8C0C4", label="平局")
    for index, method in enumerate(("linear_point", "cell_average")):
        axes[1, 1].text(index, diagonal[index] / 2 if diagonal[index] else 0, str(diagonal[index]), ha="center", va="center", color="white", fontsize=10)
        if swapped[index]:
            axes[1, 1].text(index, diagonal[index] + swapped[index] / 2, str(swapped[index]), ha="center", va="center", color="white", fontsize=10)
    axes[1, 1].set_xticks(positions, ["线性点值", "单元平均"])
    axes[1, 1].set_ylim(0, 52)
    axes[1, 1].set_ylabel("A+B网格数（每种表示48）")
    axes[1, 1].set_title("联合描述性计数：锚点仅计一次")
    axes[1, 1].grid(alpha=0.2, axis="y")
    axes[1, 1].legend(frameon=False, fontsize=8)
    fig.subplots_adjust(top=0.89, bottom=0.15, left=0.08, right=0.98, hspace=0.52, wspace=0.25)
    fig.suptitle("共同无序剖面第二批与A+B联合审计", fontsize=16, y=0.97)
    fig.savefig(ROOT / "matched-beta-batch-b.png", bbox_inches="tight")
    plt.close(fig)


def count_text(counts):
    return f"同谱秩 {counts.get('diagonal', 0)}、交换 {counts.get('swapped', 0)}、平局 {counts.get('tie_exact', 0)}"


def markdown(data):
    summary = data["summary"]
    combined = data["combined_with_batch_a"]
    lines = [
        "# Floquet-BdG 共同无序剖面第二批尺寸隔离",
        "",
        f"> 协议登记：{data['analysis_date']}；报告复核：{REPORT_DATE}。seed=4、5、6、7，r=0.05、0.1；7个新实现加1个复用锚点，共8个实现、16个展示单元。不新增类别，不补算体 winding，未计算 N=640。",
        "",
        "## 一、协议、单次锚点与谱结构",
        "",
        "每个粗格点的 β 值等于其覆盖主格点的算术平均，因此 N=400 和 N=600 通过嵌套块平均共享同一无序结构。两个强度使用同一主剖面，是配对控制而非独立样本。",
        "",
        "seed=6、r=0.05 是复用锚点：直接读取既有共同剖面分析，不作为新实现重复计数；第二批独立复核仍重新检查它的谱。所有预登记结果保留，不筛选有利方向。跨尺寸重叠不归一化。",
        "",
        "| seed | r | 证据角色 | N | 最近对中心 | 次近对中心 | 中心间隔 |",
        "|---:|---:|:---|---:|---:|---:|---:|",
    ]
    for row in data["realizations"]:
        role = "复用锚点" if row["evidence_role"] == "reused_anchor" else "本批新增"
        for cell in row["cells"]:
            lines.append(f"| {row['seed']} | {row['strength']:g} | {role} | {cell['n']} | {fmt(cell['pairs'][0]['center'])} | {fmt(cell['pairs'][1]['center'])} | {fmt(cell['center_separation'])} |")
    lines += [
        "",
        "## 二、三种网格与两种表示",
        "",
        "D 表示同谱秩主导，S 表示交换主导；三格顺序均为 M=1200／2400／4800。下表只是描述性计数，不是统计显著性检验。",
        "",
        "| seed | r | 角色 | 线性点值 D/S | 单元平均 D/S | M=4800线性同谱秩 | M=4800线性交换 | M=4800单元同谱秩 | M=4800单元交换 |",
        "|---:|---:|:---:|:---:|:---:|---:|---:|---:|---:|",
    ]
    for row in data["realizations"]:
        linear = row["methods"]["linear_point"]["grids"][-1]
        average = row["methods"]["cell_average"]["grids"][-1]
        role = "锚点" if row["evidence_role"] == "reused_anchor" else "新增"
        lines.append(f"| {row['seed']} | {row['strength']:g} | {role} | {pattern_text(row, 'linear_point')} | {pattern_text(row, 'cell_average')} | {fmt(linear['diagonal_score'])} | {fmt(linear['swapped_score'])} | {fmt(average['diagonal_score'])} | {fmt(average['swapped_score'])} |")
    lines += [
        "",
        f"第二批两种表示各自均有24个网格结果。线性点值：{count_text(summary['assignment_counts']['linear_point'])}；单元平均：{count_text(summary['assignment_counts']['cell_average'])}。",
        "",
        "图 1 插入位置：全网格分配表之后、强度配对与联合审计之前。",
        "",
        "![图 1：共同无序剖面第二批与联合审计](matched-beta-batch-b.png)",
        "",
        "**图 1**　逐实现分配得分、全网格方向、中心间隔及A+B联合计数。灰底和边框标出复用锚点，联合计数中锚点只出现一次。",
        "",
        "## 三、同主剖面的强度配对",
        "",
        "| seed | N=400中心间隔差（0.1−0.05） | N=600中心间隔差（0.1−0.05） | 线性方向改变网格数 | 单元方向改变网格数 |",
        "|---:|---:|---:|---:|---:|",
    ]
    for row in data["strength_pair_comparisons"]:
        changes = {method: sum(item["from"] != item["to"] for item in row["assignment_transitions"][method]) for method in ("linear_point", "cell_average")}
        lines.append(f"| {row['seed']} | {fmt(row['n400_center_separation_delta'])} | {fmt(row['n600_center_separation_delta'])} | {changes['linear_point']} | {changes['cell_average']} |")
    lines += [
        "",
        "## 四、A+B联合描述性审计与边界",
        "",
        f"第一批与第二批共有 {combined['realization_count']} 个互不重复的“种子—强度”键和 {combined['control_cells']} 个尺寸单元。联合线性点值：{count_text(combined['assignment_counts']['linear_point'])}；联合单元平均：{count_text(combined['assignment_counts']['cell_average'])}。每种表示均为48个网格结果，复用锚点只计一次。",
        "",
        f"联合跨表示自一致性范围为 {fmt(combined['min_representation_fidelity'])}–{fmt(combined['max_representation_fidelity'])}；联合中心间隔尺寸差范围为 {fmt(combined['center_separation_delta_range'][0])} 至 {fmt(combined['center_separation_delta_range'][1])}。第二批线性点值秩间重叠最大为 {fmt(summary['max_linear_point_off_diagonal'])}，嵌入诱导串扰仍单独保留。",
        "",
        "联合结果只描述当前指定的共同无序剖面，不能外推为普遍尺寸律、真实态交换或谱交叉。旧交换候选仍属于不同无序实现，不能与联合结果直接相减并命名为尺寸效应。",
        "",
        "本批闭合的是第二批预登记样本与单次锚点的联合描述性覆盖，不构成统计显著性、连续路径、次近对拓扑性或热力学极限结论。后续应依据预先声明的新问题扩展，而不是根据有利结果选择样本。",
        "",
        "复现：`python research/floquet-bdg-tbc/analyze_matched_beta_batch_b.py`。完整主剖面、角色、重叠矩阵、跨表示与秩间控制保存在 `matched_beta_batch_b_analysis.json`。",
        "",
    ]
    (ROOT / "MATCHED_BETA_BATCH_B.md").write_text("\n".join(lines), encoding="utf-8")


def check_only():
    stored = json.loads((ROOT / "matched_beta_batch_b_analysis.json").read_text(encoding="utf-8"))
    if stored.get("protocol_sha256") != sha(PROTOCOL) or stored.get("anchor_control_analysis_sha256") != sha(ANCHOR) or stored.get("batch_a_analysis_sha256") != sha(BATCH_A):
        raise ValueError("Batch-B evidence is stale")
    if len(stored.get("realizations", [])) != 8 or stored.get("new_control_cells") != 14 or stored.get("reused_anchor_control_cells") != 2:
        raise ValueError("Batch-B realization evidence is incomplete")
    if sum(row["evidence_role"] == "reused_anchor" for row in stored["realizations"]) != 1:
        raise ValueError("Batch-B anchor count changed")
    if any(cell["coarsening_max_absolute_error"] != 0 for row in stored["realizations"] for cell in row["cells"]):
        raise ValueError("Batch-B nested coarsening failed")
    if stored["combined_with_batch_a"]["realization_count"] != 16 or not stored.get("all_preregistered_results_retained"):
        raise ValueError("Batch-B combined coverage or retention changed")
    print(json.dumps({"check_only": True, "new_realizations": 7, "reused_anchor": 1, "new_control_cells": 14, "combined_realizations": 16, "all_passed": True}, ensure_ascii=False))
    return 0


def main():
    if "--check-only" in sys.argv:
        return check_only()
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    anchor_source = json.loads(ANCHOR.read_text(encoding="utf-8"))
    realizations = []
    for seed in protocol["seed_values"]:
        master = np.random.default_rng(20261111 + seed).random(protocol["master_grid"])
        for strength in protocol["strength_values"]:
            if seed == 6 and strength == 0.05:
                realizations.append(reuse_anchor(anchor_source))
                continue
            row = evaluate_realization(seed, strength, master, protocol)
            row["evidence_role"] = "new_batch_b"
            row["recomputed_for_new_analysis"] = True
            realizations.append(row)
    batch_a = json.loads(BATCH_A.read_text(encoding="utf-8"))
    data = {
        "schema": "floquet-bdg-matched-beta-batch-b-analysis-v1",
        "analysis_date": protocol["analysis_date"], "report_date": REPORT_DATE, "batch": "B",
        "protocol_sha256": sha(PROTOCOL), "anchor_control_analysis_sha256": sha(ANCHOR),
        "batch_a_analysis_sha256": sha(BATCH_A), "candidate_source_sha256": sha(CANDIDATE),
        "realizations": realizations, "summary": summarize(realizations),
        "strength_pair_comparisons": compare_strengths(realizations),
        "combined_with_batch_a": combined_summary(batch_a, {"realizations": realizations, "summary": summarize(realizations)}),
        "anchor_case_observation": {
            "count_weight": 1, "recomputed_for_new_analysis": False,
            "old_assignments": anchor_source["old_candidate_comparison"]["old_assignments"],
            "matched_control_assignments": anchor_source["old_candidate_comparison"]["control_assignments"],
        },
        "max_coarsening_absolute_error": 0.0,
        "new_realization_count": 7, "reused_anchor_realization_count": 1, "reported_realization_count": 8,
        "new_control_cells": 14, "reused_anchor_control_cells": 2, "reported_control_cells": 16,
        "new_seed_count": 0, "anchor_reused_exactly_once": True,
        "new_winding_computed": False, "n640_computed": False,
        "all_preregistered_results_retained": True,
        "common_disorder_profile_control_computed": True,
        "size_effect_separated": "matched_nested_profile_descriptive_only",
        "old_candidate_is_different_realization": True,
        "difference_from_original_is_not_size_effect": True,
        "normalization_correction_applied": False, "representation_invariant_claim": False,
        "universal_size_law_claim": False, "continuous_path_proof": False,
        "spectral_crossing_proven": False, "avoided_crossing_claim": False,
        "state_exchange_proven": False, "second_pair_topological_claim": False,
        "statistical_significance_claim": False, "thermodynamic_limit_proof": False,
        "new_taxonomy_claim": False, "categories_changed": False,
    }
    (ROOT / "matched_beta_batch_b_analysis.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    figure(data)
    markdown(data)
    print(json.dumps({"summary": data["summary"], "combined_with_batch_a": data["combined_with_batch_a"], "new_control_cells": 14, "reused_anchor_control_cells": 2, "n640_computed": False}, ensure_ascii=False, indent=2))
    print("generated matched_beta_batch_b_analysis.json matched-beta-batch-b.png MATCHED_BETA_BATCH_B.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
