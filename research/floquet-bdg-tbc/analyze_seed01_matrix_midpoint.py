"""Cross-seed midpoint paths and within-seed step-size stability comparisons."""

import json
from collections import Counter
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

PROTOCOL = ROOT / "seed01_matrix_midpoint_protocol.json"
REFERENCE = ROOT / "seed6_matrix_midpoint_analysis.json"
BATCH_A = ROOT / "matched_beta_batch_a_analysis.json"
BATCH_C = ROOT / "matched_beta_batch_c_analysis.json"
REPORT_DATE = "2026-11-12"
ENTRIES = ((0, 0), (0, 1), (1, 0), (1, 1))
plt.rcParams.update({
    "font.sans-serif": ["Microsoft YaHei", "SimHei", "Noto Sans CJK SC", "DejaVu Sans"],
    "axes.unicode_minus": False, "font.size": 9, "figure.dpi": 160,
})


def endpoint_binding(cells, path_matrices, batch_a, batch_c):
    max_matrix = 0.0
    max_singular = 0.0
    max_spectrum = 0.0
    for seed in (0, 1):
        for strength, source in ((0.1, batch_a), (0.2, batch_c)):
            source_row = next(row for row in source["realizations"] if row["seed"] == seed and row["strength"] == strength)
            for method in ("linear_point", "cell_average"):
                for m in (1200, 2400, 4800):
                    actual = next(row for row in path_matrices if row["seed"] == seed and row["strength"] == strength and row["method"] == method and row["m"] == m)
                    expected = next(row for row in source_row["methods"][method]["grids"] if row["m"] == m)
                    for i, j in ENTRIES:
                        a, e = actual["overlap_matrix"][i][j], expected["overlap_matrix"][i][j]
                        max_matrix = max(max_matrix, abs(a["overlap"] - e["overlap"]))
                        max_singular = max(max_singular, max(abs(x - y) for x, y in zip(a["singular_values"], e["singular_values"])))
            for n in (400, 600):
                actual_cell = next(cell for cell in cells if cell["seed"] == seed and cell["strength"] == strength and cell["n"] == n)
                expected_cell = next(cell for cell in source_row["cells"] if cell["n"] == n)
                max_spectrum = max(max_spectrum, max(abs(x - y) for x, y in zip(actual_cell["spectrum_first_six"], expected_cell["spectrum_first_six"])))
    return {
        "max_matrix_absolute_error": max_matrix,
        "max_singular_absolute_error": max_singular,
        "max_spectrum_absolute_error": max_spectrum,
        "endpoint_recomputation_is_not_new_realization": True,
    }


def cross_seed_extrema(extrema, reference):
    agreements = []
    for method in ("linear_point", "cell_average"):
        for i, j in ENTRIES:
            entry = f"O{i}{j}"
            rows = {seed: next(row for row in extrema if row["seed"] == seed and row["method"] == method and row["entry"] == entry) for seed in (0, 1)}
            rows[6] = next(row for row in reference["entry_extrema"] if row["method"] == method and row["entry"] == entry)
            min_strengths = {str(seed): rows[seed]["min_strength"] for seed in (0, 1, 6)}
            max_strengths = {str(seed): rows[seed]["max_strength"] for seed in (0, 1, 6)}
            jump_links = {str(seed): [rows[seed]["max_jump_from"], rows[seed]["max_jump_to"]] for seed in (0, 1, 6)}
            agreements.append({
                "method": method, "entry": entry,
                "min_strength_by_seed": min_strengths, "max_strength_by_seed": max_strengths,
                "max_jump_link_by_seed": jump_links,
                "same_min_strength_across_all": len(set(min_strengths.values())) == 1,
                "same_max_strength_across_all": len(set(max_strengths.values())) == 1,
                "same_max_jump_link_across_all": len({tuple(value) for value in jump_links.values()}) == 1,
            })
    return agreements


def figure(data, reference):
    strengths = [row["strength"] for row in data["cells"] if row["seed"] == 0 and row["n"] == 400]
    midpoints = [(first + second) / 2 for first, second in zip(strengths[:-1], strengths[1:])]
    colors = {0: "#356A64", 1: "#A25B3F", 6: "#6F7F92"}
    fig, axes = plt.subplots(2, 2, figsize=(14, 9.8))
    for axis in (axes[0, 0], axes[0, 1], axes[1, 1]):
        for strength in data["protocol_new_midpoint_strengths"]:
            axis.axvline(strength, color="#C2C9CC", lw=0.7, ls=":", zorder=0)
    for seed in (0, 1, 6):
        source_rows = data["path_matrices"] if seed != 6 else reference["path_matrices"]
        for method, linestyle in (("linear_point", "-"), ("cell_average", "--")):
            values = [next(row for row in source_rows if row["strength"] == strength and row["method"] == method and row["m"] == 4800)["overlap_matrix"][0][0]["overlap"] for strength in strengths]
            axes[0, 0].plot(strengths, values, color=colors[seed], ls=linestyle, marker="o", ms=3.5, label=f"seed={seed} {method}")
    axes[0, 0].set_yscale("log")
    axes[0, 0].set_title("O00：三个无序实现的路径")
    axes[0, 0].set_ylabel("O00（对数）")
    axes[0, 0].legend(frameon=False, fontsize=7)
    for seed in (0, 1, 6):
        source_rows = data["path_matrices"] if seed != 6 else reference["path_matrices"]
        for (i, j), entry_label, linestyle in (((0, 1), "O01", "-"), ((1, 0), "O10", "--")):
            values = [next(row for row in source_rows if row["strength"] == strength and row["method"] == "linear_point" and row["m"] == 4800)["overlap_matrix"][i][j]["overlap"] for strength in strengths]
            axes[0, 1].plot(strengths, values, color=colors[seed], ls=linestyle, marker="o", ms=3.5, label=f"seed={seed} {entry_label}")
    axes[0, 1].set_yscale("log")
    axes[0, 1].set_title("O01／O10：局部结构随实现改变")
    axes[0, 1].set_ylabel("重叠（对数）")
    axes[0, 1].legend(frameon=False, fontsize=7)
    positions = np.arange(3)
    summary_lookup = {row["seed"]: row for row in data["summary_by_seed"]}
    summary_lookup[6] = reference["summary"]
    jump_changes = [summary_lookup[seed]["jump_change_count"] for seed in (0, 1, 6)]
    driver_changes = [summary_lookup[seed]["driver_comparison_change_count"] for seed in (0, 1, 6)]
    axes[1, 0].bar(positions - 0.17, jump_changes, width=0.34, color="#356A64", label="跳变改变数（8项）")
    axes[1, 0].bar(positions + 0.17, driver_changes, width=0.34, color="#A25B3F", label="主导计数改变数（4组）")
    axes[1, 0].set_xticks(positions, ["seed=0", "seed=1", "seed=6"])
    axes[1, 0].set_ylim(0, 8.8)
    axes[1, 0].set_ylabel("数量")
    axes[1, 0].set_title("步长敏感性并不只存在于 seed=6")
    axes[1, 0].grid(alpha=0.2, axis="y")
    axes[1, 0].legend(frameon=False, fontsize=8)
    for seed in (0, 1, 6):
        source_rows = data["links"] if seed != 6 else reference["links"]
        rows = [row for row in source_rows if row["n"] == 400 and (seed == 6 or row["seed"] == seed)]
        axes[1, 1].plot(midpoints, [row["diagonal_score"] for row in rows], color=colors[seed], marker="o", ms=3.5, label=f"seed={seed}")
    axes[1, 1].set_yscale("log")
    axes[1, 1].set_title("N=400：同尺寸原生重叠")
    axes[1, 1].set_ylabel("同谱秩得分（对数）")
    axes[1, 1].legend(frameon=False, fontsize=8)
    for axis in axes.flat:
        axis.set_xlabel("无序强度 r")
        axis.grid(alpha=0.2, which="both")
    fig.subplots_adjust(top=0.89, bottom=0.13, left=0.08, right=0.98, hspace=0.44, wspace=0.25)
    fig.suptitle("跨种子跳变窗口与步长稳定性对照", fontsize=16, y=0.97)
    fig.savefig(ROOT / "seed01-matrix-midpoint.png", bbox_inches="tight")
    plt.close(fig)


def fmt(value):
    return f"{value:.6g}"


def markdown(data):
    lines = [
        "# Floquet-BdG 跨种子跳变窗口中点对照",
        "",
        f"> 日期：{REPORT_DATE}。seed=0、1 使用同一13点协议，与 seed=6 对照；共52个新尺寸单元、156组矩阵、48条原生链接。不新增类别，不补算体 winding，未计算 N=640。",
        "",
        "## 一、三个无序实现的步长响应",
        "",
        "每个种子分别比较原9点／8链接与细化13点／12链接，不归一化，不筛选有利路径段。跨种子一致或不一致只描述当前实现，不构成普遍性或统计显著性结论。",
        "",
        "每条矩阵项差分同时保留两条主奇异值通道的贡献，便于区分矩阵项变化与主奇异通道变化。",
        "",
        "| seed | 新尺寸单元 | 跳变改变数（8项） | 主导计数改变数（4组） | 新中点参与极值数 | 跨尺寸分配改变数 |",
        "|---:|---:|---:|---:|---:|---:|",
    ]
    for row in data["summary_by_seed"]:
        lines.append(f"| {row['seed']} | {row['new_control_cells']} | {row['jump_change_count']} | {row['driver_comparison_change_count']} | {row['new_extrema_midpoint_count']} | {row['method_grid_assignment_change_count']} |")
    lines += [
        "",
        "图 1 插入位置：种子汇总表之后、逐项对照之前。",
        "",
        "![图 1：跨种子跳变窗口中点对照](seed01-matrix-midpoint.png)",
        "",
        "**图 1**　三个无序实现的 O00、O01、O10 路径、步长改变计数及同尺寸原生重叠。数值贡献不作因果命名。",
        "",
        "## 二、每个种子内部的最大跳变对照",
        "",
        "| seed | 方法 | 项 | 原最大跳变及链接 | 细化最大跳变及链接 | 改变 |",
        "|---:|:---|:---:|---:|---:|:---:|",
    ]
    for row in data["jump_comparisons"]:
        lines.append(f"| {row['seed']} | {row['method']} | {row['entry']} | {fmt(row['original_max_adjacent_absolute_jump'])}（{row['original_jump_from']}→{row['original_jump_to']}） | {fmt(row['refined_max_adjacent_absolute_jump'])}（{row['refined_jump_from']}→{row['refined_jump_to']}） | {row['jump_changed']} |")
    lines += [
        "",
        "## 三、跨种子极值与跳变位置一致性",
        "",
        "| 方法 | 项 | 最小值强度（0／1／6） | 最大值强度（0／1／6） | 最大跳变链接（0／1／6） |",
        "|:---|:---:|---:|---:|---:|",
    ]
    for row in data["cross_seed_extremum_agreement"]:
        lines.append(f"| {row['method']} | {row['entry']} | {row['min_strength_by_seed']} | {row['max_strength_by_seed']} | {row['max_jump_link_by_seed']} |")
    lines += [
        "",
        "## 四、主导项、原生链接与边界",
        "",
        "| seed | 方法 | 得分组 | 原主导项计数（8链接） | 细化主导项计数（12链接） |",
        "|---:|:---|:---|:---:|:---:|",
    ]
    for row in data["driver_comparisons"]:
        lines.append(f"| {row['seed']} | {row['method']} | {row['score_group']} | {row['original_dominant_entry_counts']} | {row['refined_dominant_entry_counts']} |")
    lines += [
        "",
        "| seed | N | 同谱秩最小值及链接 | 交换最大值及链接 | 最大中心间隔变化 |",
        "|---:|---:|---:|---:|---:|",
    ]
    for row in data["link_summary"]:
        lines.append(f"| {row['seed']} | {row['n']} | {fmt(row['min_diagonal_score'])}（{row['min_diagonal_from']}→{row['min_diagonal_to']}） | {fmt(row['max_swapped_score'])}（{row['max_swapped_from']}→{row['max_swapped_to']}） | {fmt(row['max_absolute_center_separation_delta'])} |")
    lines += [
        "",
        f"两个新路径的跨表示自一致性总范围为 {fmt(data['summary']['min_representation_fidelity'])}–{fmt(data['summary']['max_representation_fidelity'])}；线性点值秩间重叠最大为 {fmt(data['summary']['max_linear_point_off_diagonal'])}，单元平均最大为 {fmt(data['summary']['max_cell_average_off_diagonal'])}。这些控制不与路径得分混用。",
        "",
        "中点插入和跨种子对照可以区分步长依赖与实现依赖，但都不能外推为其他种子、普遍尺寸律、真实态交换、谱交叉、统计显著性或热力学极限结论。旧交换候选属于不同无序实现，不能与路径差分直接相减。",
        "",
        "复现：`python research/floquet-bdg-tbc/analyze_seed01_matrix_midpoint.py`。52个路径单元及全部比较保存在 `seed01_matrix_midpoint_analysis.json`。",
        "",
    ]
    (ROOT / "SEED01_MATRIX_MIDPOINT.md").write_text("\n".join(lines), encoding="utf-8")


def check_only():
    stored = json.loads((ROOT / "seed01_matrix_midpoint_analysis.json").read_text(encoding="utf-8"))
    if stored.get("protocol_sha256") != sha(PROTOCOL) or stored.get("reference_seed6_analysis_sha256") != sha(REFERENCE):
        raise ValueError("Seed-0/1 midpoint evidence is stale")
    if len(stored.get("cells", [])) != 52 or len(stored.get("path_matrices", [])) != 156 or len(stored.get("links", [])) != 48:
        raise ValueError("Seed-0/1 midpoint evidence is incomplete")
    if stored.get("new_control_cells") != 52 or not stored.get("all_preregistered_results_retained"):
        raise ValueError("Seed-0/1 midpoint scope changed")
    print(json.dumps({"check_only": True, "cells": 52, "path_matrices": 156, "native_links": 48, "entry_links": 576, "all_passed": True}, ensure_ascii=False))
    return 0


def main():
    if "--check-only" in sys.argv:
        return check_only()
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    all_cells, all_matrices, all_links, all_method_links, all_entry_links = [], [], [], [], []
    all_fidelity, all_rank, all_extrema, all_original_extrema = [], [], [], []
    all_drivers, all_original_drivers, all_jumps, all_driver_comparisons = [], [], [], []
    all_link_summaries, all_original_link_summaries, summary_by_seed = [], [], []
    new_midpoints = set(protocol["new_midpoint_strengths"])
    for seed in protocol["seed_values"]:
        cells, bases_by_key, matrices, fidelity, rank_controls, max_direction = evaluate_path(dict(protocol, seed=seed))
        links, method_links, entry_links = build_links(dict(protocol, seed=seed), cells, bases_by_key, matrices)
        for collection, seed_collection in ((all_cells, cells), (all_matrices, matrices), (all_links, links), (all_method_links, method_links), (all_entry_links, entry_links), (all_fidelity, fidelity), (all_rank, rank_controls)):
            for row in seed_collection:
                row["seed"] = seed
                if collection is all_cells:
                    row["new_for_path"] = True
                    row["evidence_role"] = "new_seed_path"
            collection.extend(seed_collection)
        original_matrices = [row for row in matrices if row["strength"] not in new_midpoints]
        original_method_links = [row for row in method_links if row["from"] not in new_midpoints and row["to"] not in new_midpoints]
        original_entry_links = [row for row in entry_links if row["from"] not in new_midpoints and row["to"] not in new_midpoints]
        original_native_links = [row for row in links if row["from"] not in new_midpoints and row["to"] not in new_midpoints]
        original_extrema = entry_extrema(original_matrices, original_entry_links)
        extrema = entry_extrema(matrices, entry_links)
        original_drivers = driver_summary(original_method_links)
        drivers = driver_summary(method_links)
        for row in original_extrema:
            row["seed"] = seed
        for row in extrema:
            row["seed"] = seed
        for row in original_drivers:
            row["seed"] = seed
        for row in drivers:
            row["seed"] = seed
        all_original_extrema.extend(original_extrema)
        all_extrema.extend(extrema)
        all_original_drivers.extend(original_drivers)
        all_drivers.extend(drivers)
        jumps = jump_comparisons(original_extrema, extrema, protocol["new_midpoint_strengths"])
        for row in jumps:
            row["seed"] = seed
            row["original_max_adjacent_absolute_jump"] = row.pop("old_max_adjacent_absolute_jump")
            row["original_jump_from"] = row.pop("old_jump_from")
            row["original_jump_to"] = row.pop("old_jump_to")
        all_jumps.extend(jumps)
        driver_changes = driver_comparisons(original_drivers, drivers)
        for row in driver_changes:
            row["seed"] = seed
            row["original_dominant_entry_counts"] = row.pop("old_dominant_entry_counts")
            row["original_link_count"] = row.pop("old_link_count")
            row["original_score_ratio_range"] = row.pop("old_score_ratio_range")
        all_driver_comparisons.extend(driver_changes)
        link_summaries = link_summary(links)
        for row in link_summaries:
            row["seed"] = seed
        all_link_summaries.extend(link_summaries)
        original_link_summaries = link_summary(original_native_links)
        for row in original_link_summaries:
            row["seed"] = seed
        all_original_link_summaries.extend(original_link_summaries)
        summary_by_seed.append({
            "seed": seed, "new_control_cells": 26,
            "cross_size_assignment_counts": {
                method: dict(Counter(row["dominant_assignment"] for row in matrices if row["method"] == method))
                for method in protocol["methods"]
            },
            "method_grid_assignment_change_count": sum(row["before_dominant_assignment"] != row["after_dominant_assignment"] for row in method_links),
            "jump_change_count": sum(row["jump_changed"] for row in jumps),
            "driver_comparison_change_count": sum(row["driver_counts_changed"] for row in driver_changes),
            "new_extrema_midpoint_count": sum(row["min_strength"] in new_midpoints or row["max_strength"] in new_midpoints for row in extrema),
            "min_representation_fidelity": min(row["forward"] for row in fidelity),
            "max_representation_fidelity": max(row["forward"] for row in fidelity),
            "max_direction_absolute_error": max_direction,
        })
    reference = json.loads(REFERENCE.read_text(encoding="utf-8"))
    summary = {
        "cross_size_assignment_counts": {
            method: dict(Counter(row["dominant_assignment"] for row in all_matrices if row["method"] == method))
            for method in protocol["methods"]
        },
        "max_direction_absolute_error": max(row["max_direction_absolute_error"] for row in summary_by_seed),
        "max_representation_direction_absolute_error": max(row["direction_absolute_error"] for row in all_fidelity),
        "min_representation_fidelity": min(row["forward"] for row in all_fidelity),
        "max_representation_fidelity": max(row["forward"] for row in all_fidelity),
        "max_native_off_diagonal": max(row["off01"] for row in all_rank if row["method"] == "native_qr"),
        "max_linear_point_off_diagonal": max(row["off01"] for row in all_rank if row["method"] == "linear_point"),
        "max_cell_average_off_diagonal": max(row["off01"] for row in all_rank if row["method"] == "cell_average"),
        "method_grid_assignment_change_count": sum(row["before_dominant_assignment"] != row["after_dominant_assignment"] for row in all_method_links),
    }
    agreements = cross_seed_extrema(all_extrema, reference)
    summary["same_min_strength_across_all_count"] = sum(row["same_min_strength_across_all"] for row in agreements)
    summary["same_max_strength_across_all_count"] = sum(row["same_max_strength_across_all"] for row in agreements)
    summary["same_max_jump_link_across_all_count"] = sum(row["same_max_jump_link_across_all"] for row in agreements)
    data = {
        "schema": "floquet-bdg-seed01-matrix-midpoint-analysis-v1",
        "analysis_date": protocol["analysis_date"], "report_date": REPORT_DATE,
        "protocol_sha256": sha(PROTOCOL), "reference_seed6_analysis_sha256": sha(REFERENCE),
        "batch_a_analysis_sha256": sha(BATCH_A), "batch_c_analysis_sha256": sha(BATCH_C),
        "protocol_new_midpoint_strengths": protocol["new_midpoint_strengths"],
        "cells": all_cells, "path_matrices": all_matrices, "links": all_links,
        "method_grid_links": all_method_links, "entry_links": all_entry_links,
        "original_entry_extrema": all_original_extrema, "entry_extrema": all_extrema,
        "original_driver_summary": all_original_drivers, "driver_summary": all_drivers,
        "jump_comparisons": all_jumps, "driver_comparisons": all_driver_comparisons,
        "original_link_summary": all_original_link_summaries, "link_summary": all_link_summaries,
        "summary_by_seed": summary_by_seed, "cross_seed_extremum_agreement": agreements,
        "representation_fidelity": all_fidelity, "rank_controls": all_rank,
        "summary": summary, "endpoint_binding": endpoint_binding(all_cells, all_matrices, json.loads(BATCH_A.read_text(encoding="utf-8")), json.loads(BATCH_C.read_text(encoding="utf-8"))),
        "reference_seed6_recomputed": False,
        "new_control_cells": 52, "evaluated_control_cells": 52,
        "not_merged_into_batch_counts": True, "new_seed_count": 0,
        "new_winding_computed": False, "n640_computed": False,
        "all_preregistered_results_retained": True,
        "normalization_correction_applied": False, "representation_invariant_claim": False,
        "statistical_significance_claim": False, "continuous_path_proof": False,
        "spectral_crossing_proven": False, "avoided_crossing_claim": False,
        "state_exchange_proven": False, "causal_mechanism_proven": False,
        "thermodynamic_limit_proof": False, "new_taxonomy_claim": False,
        "old_candidate_is_different_realization": True,
        "difference_from_original_is_not_size_effect": True,
        "categories_changed": False,
    }
    (ROOT / "seed01_matrix_midpoint_analysis.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    figure(data, reference)
    markdown(data)
    print(json.dumps({"summary": summary, "summary_by_seed": summary_by_seed, "cross_seed_extremum_agreement": agreements, "endpoint_binding": data["endpoint_binding"], "cells": 52, "native_links": 48, "entry_links": 576}, ensure_ascii=False, indent=2))
    print("generated seed01_matrix_midpoint_analysis.json seed01-matrix-midpoint.png SEED01_MATRIX_MIDPOINT.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
