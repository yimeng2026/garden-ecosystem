"""Preregistered midpoint refinement of the seed-6 matrix response path."""

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
from analyze_seed6_matrix_path import (  # noqa: E402
    build_links, driver_summary, entry_extrema, evaluate_path, link_summary, sha,
)

PROTOCOL = ROOT / "seed6_matrix_midpoint_protocol.json"
ORIGINAL = ROOT / "seed6_matrix_path_analysis.json"
REPORT_DATE = "2026-11-12"
ENTRIES = ((0, 0), (0, 1), (1, 0), (1, 1))
plt.rcParams.update({
    "font.sans-serif": ["Microsoft YaHei", "SimHei", "Noto Sans CJK SC", "DejaVu Sans"],
    "axes.unicode_minus": False, "font.size": 9, "figure.dpi": 160,
})


def original_path_binding(cells, path_matrices, original):
    original_strengths = sorted({row["strength"] for row in original["cells"]})
    actual_cells = [row for row in cells if row["strength"] in original_strengths]
    actual_matrices = [row for row in path_matrices if row["strength"] in original_strengths]
    max_spectrum = 0.0
    max_matrix = 0.0
    max_singular = 0.0
    for actual, expected in zip(actual_cells, original["cells"]):
        max_spectrum = max(max_spectrum, max(abs(x - y) for x, y in zip(actual["spectrum_first_six"], expected["spectrum_first_six"])))
    for actual, expected in zip(actual_matrices, original["path_matrices"]):
        for i, j in ENTRIES:
            a, e = actual["overlap_matrix"][i][j], expected["overlap_matrix"][i][j]
            max_matrix = max(max_matrix, abs(a["overlap"] - e["overlap"]))
            max_singular = max(max_singular, max(abs(x - y) for x, y in zip(a["singular_values"], e["singular_values"])))
    return {
        "original_cell_count": len(original["cells"]), "original_matrix_count": len(original["path_matrices"]),
        "max_spectrum_absolute_error": max_spectrum,
        "max_matrix_absolute_error": max_matrix,
        "max_singular_absolute_error": max_singular,
        "reused_cells_are_not_new_realizations": True,
    }


def jump_comparisons(old_rows, new_rows, new_midpoints):
    comparisons = []
    for old, new in zip(old_rows, new_rows):
        changed = (old["max_jump_from"], old["max_jump_to"], old["max_adjacent_absolute_jump"]) != (new["max_jump_from"], new["max_jump_to"], new["max_adjacent_absolute_jump"])
        comparisons.append({
            "method": new["method"], "entry": new["entry"],
            "old_max_adjacent_absolute_jump": old["max_adjacent_absolute_jump"],
            "refined_max_adjacent_absolute_jump": new["max_adjacent_absolute_jump"],
            "old_jump_from": old["max_jump_from"], "old_jump_to": old["max_jump_to"],
            "refined_jump_from": new["max_jump_from"], "refined_jump_to": new["max_jump_to"],
            "jump_changed": changed,
            "refined_jump_uses_new_midpoint": new["max_jump_from"] in new_midpoints or new["max_jump_to"] in new_midpoints,
        })
    return comparisons


def driver_comparisons(old_rows, new_rows):
    comparisons = []
    for old, new in zip(old_rows, new_rows):
        comparisons.append({
            "method": new["method"], "score_group": new["score_group"],
            "old_dominant_entry_counts": old["dominant_entry_counts"], "old_link_count": 8,
            "refined_dominant_entry_counts": new["dominant_entry_counts"], "refined_link_count": 12,
            "old_score_ratio_range": old["score_ratio_range"], "refined_score_ratio_range": new["score_ratio_range"],
            "driver_counts_changed": old["dominant_entry_counts"] != new["dominant_entry_counts"],
        })
    return comparisons


def figure(data, original):
    strengths = [row["strength"] for row in data["cells"] if row["n"] == 400]
    midpoints = [(first + second) / 2 for first, second in zip(strengths[:-1], strengths[1:])]
    new_strengths = set(data["protocol_new_midpoint_strengths"])
    fig, axes = plt.subplots(2, 2, figsize=(14, 9.8))
    for axis in (axes[0, 0], axes[0, 1], axes[1, 1]):
        for strength in sorted(new_strengths):
            axis.axvline(strength, color="#98A4A8", lw=0.8, ls=":", zorder=0)
    for method, color, marker in (("linear_point", "#356A64", "o"), ("cell_average", "#A25B3F", "s")):
        values = [next(row for row in data["path_matrices"] if row["strength"] == strength and row["method"] == method and row["m"] == 4800)["overlap_matrix"][0][0]["overlap"] for strength in strengths]
        axes[0, 0].plot(strengths, values, color=color, marker=marker, label=method)
    axes[0, 0].set_yscale("log")
    axes[0, 0].set_title("O00：13点路径")
    axes[0, 0].set_ylabel("O00（对数）")
    axes[0, 0].legend(frameon=False)
    for (i, j), label, color in (((0, 1), "O01", "#356A64"), ((1, 0), "O10", "#A25B3F")):
        for method, linestyle in (("linear_point", "-"), ("cell_average", "--")):
            values = [next(row for row in data["path_matrices"] if row["strength"] == strength and row["method"] == method and row["m"] == 4800)["overlap_matrix"][i][j]["overlap"] for strength in strengths]
            axes[0, 1].plot(strengths, values, color=color, ls=linestyle, marker="o", ms=4, label=f"{label} {method}")
    axes[0, 1].set_yscale("log")
    axes[0, 1].set_title("O01／O10：局部极值与新增中点")
    axes[0, 1].set_ylabel("重叠（对数）")
    axes[0, 1].legend(frameon=False, fontsize=7)
    comparisons = data["jump_comparisons"]
    positions = np.arange(8)
    old_values = [row["old_max_adjacent_absolute_jump"] for row in comparisons]
    new_values = [row["refined_max_adjacent_absolute_jump"] for row in comparisons]
    axes[1, 0].bar(positions - 0.17, old_values, width=0.34, color="#98A4A8", label="原8链接")
    axes[1, 0].bar(positions + 0.17, new_values, width=0.34, color="#356A64", label="细化12链接")
    axes[1, 0].set_yscale("log")
    axes[1, 0].set_xticks(positions, [f"{row['entry']}\n{'LP' if row['method'] == 'linear_point' else 'CA'}" for row in comparisons])
    axes[1, 0].set_ylabel("最大相邻 |ΔOij|（对数）")
    axes[1, 0].set_title("最大跳变：原网格与细化网格")
    axes[1, 0].grid(alpha=0.2, axis="y")
    axes[1, 0].legend(frameon=False, fontsize=8)
    for n, color in ((400, "#356A64"), (600, "#A25B3F")):
        rows = [row for row in data["links"] if row["n"] == n]
        axes[1, 1].plot(midpoints, [row["diagonal_score"] for row in rows], color=color, marker="o", ms=4, label=f"N={n}")
    axes[1, 1].set_yscale("log")
    axes[1, 1].set_title("同尺寸原生重叠：12条链接")
    axes[1, 1].set_ylabel("同谱秩得分（对数）")
    axes[1, 1].legend(frameon=False, fontsize=8)
    axes[1, 1].text(0.02, 0.04, "竖虚线为新增中点", transform=axes[1, 1].transAxes, fontsize=8, color="#4F5E63")
    for axis in axes.flat:
        axis.set_xlabel("无序强度 r")
        axis.grid(alpha=0.2, which="both")
    fig.subplots_adjust(top=0.89, bottom=0.13, left=0.08, right=0.98, hspace=0.44, wspace=0.25)
    fig.suptitle("seed=6：跳变窗口的中点复核与步长稳定性", fontsize=16, y=0.97)
    fig.savefig(ROOT / "seed6-matrix-midpoint.png", bbox_inches="tight")
    plt.close(fig)


def fmt(value):
    return f"{value:.6g}"


def markdown(data):
    summary = data["summary"]
    lines = [
        "# Floquet-BdG 固定 seed=6 跳变窗口中点复核",
        "",
        f"> 日期：{REPORT_DATE}。在两个既定跳变窗口插入4个预登记中点，共8个新尺寸单元；原9点与新增4点组成13点路径、12条相邻链接。不新增类别，不补算体 winding，未计算 N=640。",
        "",
        "## 一、协议与原路径绑定",
        "",
        "新增强度为 r=0.13125、0.14375、0.18125、0.19375，不根据结果增删点。跨尺寸矩阵、矩阵项差分和同尺寸原生链接均不归一化，不筛选有利路径段。",
        "",
        f"原18个单元的谱最大误差为 {fmt(data['original_path_binding']['max_spectrum_absolute_error'])}；原54组矩阵的最大重叠误差为 {fmt(data['original_path_binding']['max_matrix_absolute_error'])}，主奇异值最大误差为 {fmt(data['original_path_binding']['max_singular_absolute_error'])}。复用单元不计入新增实现。",
        "",
        "## 二、极值与最大跳变的步长对照",
        "",
        "| 方法 | 矩阵项 | 原最大跳变及链接 | 细化最大跳变及链接 | 是否改变 |",
        "|:---|:---:|---:|---:|:---:|",
    ]
    for row in data["jump_comparisons"]:
        lines.append(f"| {row['method']} | {row['entry']} | {fmt(row['old_max_adjacent_absolute_jump'])}（{row['old_jump_from']}→{row['old_jump_to']}） | {fmt(row['refined_max_adjacent_absolute_jump'])}（{row['refined_jump_from']}→{row['refined_jump_to']}） | {row['jump_changed']} |")
    lines += [
        "",
        "图 1 插入位置：跳变对照表之后、主导项与原生链接之前。",
        "",
        "![图 1：固定种子跳变窗口中点复核](seed6-matrix-midpoint.png)",
        "",
        "**图 1**　13点路径、局部极值、原8链接与细化12链接的最大跳变，以及同尺寸原生重叠。竖虚线为新增中点，数值贡献不作因果命名。",
        "",
        "## 三、主导项与原生链接的步长对照",
        "",
        "| 方法 | 得分组 | 原主导项计数（8链接） | 细化主导项计数（12链接） | 计数是否改变 |",
        "|:---|:---|:---:|:---:|:---:|",
    ]
    for row in data["driver_comparisons"]:
        lines.append(f"| {row['method']} | {row['score_group']} | {row['old_dominant_entry_counts']} | {row['refined_dominant_entry_counts']} | {row['driver_counts_changed']} |")
    lines += [
        "",
        "| N | 链接数 | 同谱秩最小值及链接 | 交换最大值及链接 | 最大中心间隔变化 |",
        "|---:|---:|---:|---:|---:|",
    ]
    for row in data["link_summary"]:
        lines.append(f"| {row['n']} | {row['link_count']} | {fmt(row['min_diagonal_score'])}（{row['min_diagonal_from']}→{row['min_diagonal_to']}） | {fmt(row['max_swapped_score'])}（{row['max_swapped_from']}→{row['max_swapped_to']}） | {fmt(row['max_absolute_center_separation_delta'])} |")
    lines += [
        "",
        f"跨表示自一致性范围为 {fmt(summary['min_representation_fidelity'])}–{fmt(summary['max_representation_fidelity'])}；线性点值秩间重叠最大为 {fmt(summary['max_linear_point_off_diagonal'])}，单元平均最大为 {fmt(summary['max_cell_average_off_diagonal'])}。这些控制不与路径得分混用。",
        "",
        "## 四、结论与边界",
        "",
        "中点插入可以检验局部极值、最大跳变和主导项的步长稳定性，但更密的离散采样仍不等于连续路径证明。更平滑的外观不能替代独立数值收敛判据，也不能直接命名为谱交叉、避免交叉或真实态交换。",
        "",
        "本轮不能外推为其他种子、普遍尺寸律、统计显著性、次近对拓扑性或热力学极限结论。旧交换候选属于不同无序实现，不能与路径差分直接相减。",
        "",
        "复现：`python research/floquet-bdg-tbc/analyze_seed6_matrix_midpoint.py`。26个路径单元、78组矩阵、24条原生链接、288条矩阵项差分及原路径绑定保存在 `seed6_matrix_midpoint_analysis.json`。",
        "",
    ]
    (ROOT / "SEED6_MATRIX_MIDPOINT.md").write_text("\n".join(lines), encoding="utf-8")


def check_only():
    stored = json.loads((ROOT / "seed6_matrix_midpoint_analysis.json").read_text(encoding="utf-8"))
    if stored.get("protocol_sha256") != sha(PROTOCOL) or stored.get("original_path_analysis_sha256") != sha(ORIGINAL):
        raise ValueError("Seed-6 midpoint evidence is stale")
    if len(stored.get("cells", [])) != 26 or len(stored.get("path_matrices", [])) != 78 or len(stored.get("links", [])) != 24:
        raise ValueError("Seed-6 midpoint evidence is incomplete")
    if stored.get("new_midpoint_control_cells") != 8 or not stored.get("all_preregistered_results_retained"):
        raise ValueError("Seed-6 midpoint scope changed")
    print(json.dumps({"check_only": True, "cells": 26, "path_matrices": 78, "native_links": 24, "entry_links": 288, "all_passed": True}, ensure_ascii=False))
    return 0


def main():
    if "--check-only" in sys.argv:
        return check_only()
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    cells, bases_by_key, path_matrices, representation_fidelity, rank_controls, max_direction = evaluate_path(protocol)
    links, method_grid_links, entry_links = build_links(protocol, cells, bases_by_key, path_matrices)
    original = json.loads(ORIGINAL.read_text(encoding="utf-8"))
    extrema = entry_extrema(path_matrices, entry_links)
    drivers = driver_summary(method_grid_links)
    summary = {
        "cross_size_assignment_counts": {
            method: dict(Counter(row["dominant_assignment"] for row in path_matrices if row["method"] == method))
            for method in protocol["methods"]
        },
        "max_direction_absolute_error": max_direction,
        "max_representation_direction_absolute_error": max(row["direction_absolute_error"] for row in representation_fidelity),
        "min_representation_fidelity": min(row["forward"] for row in representation_fidelity),
        "max_representation_fidelity": max(row["forward"] for row in representation_fidelity),
        "max_native_off_diagonal": max(row["off01"] for row in rank_controls if row["method"] == "native_qr"),
        "max_linear_point_off_diagonal": max(row["off01"] for row in rank_controls if row["method"] == "linear_point"),
        "max_cell_average_off_diagonal": max(row["off01"] for row in rank_controls if row["method"] == "cell_average"),
        "method_grid_assignment_change_count": sum(row["before_dominant_assignment"] != row["after_dominant_assignment"] for row in method_grid_links),
    }
    jumps = jump_comparisons(original["entry_extrema"], extrema, protocol["new_midpoint_strengths"])
    drivers_comparison = driver_comparisons(original["driver_summary"], drivers)
    summary["jump_change_count"] = sum(row["jump_changed"] for row in jumps)
    summary["driver_comparison_change_count"] = sum(row["driver_counts_changed"] for row in drivers_comparison)
    summary["new_extrema_midpoint_count"] = sum(row["min_strength"] in protocol["new_midpoint_strengths"] or row["max_strength"] in protocol["new_midpoint_strengths"] for row in extrema)
    data = {
        "schema": "floquet-bdg-seed6-matrix-midpoint-analysis-v1",
        "analysis_date": protocol["analysis_date"], "report_date": REPORT_DATE,
        "protocol_sha256": sha(PROTOCOL), "original_path_analysis_sha256": sha(ORIGINAL),
        "protocol_new_midpoint_strengths": protocol["new_midpoint_strengths"],
        "cells": cells, "path_matrices": path_matrices, "links": links,
        "method_grid_links": method_grid_links, "entry_links": entry_links,
        "entry_extrema": extrema, "driver_summary": drivers,
        "jump_comparisons": jumps, "driver_comparisons": drivers_comparison,
        "link_summary": link_summary(links),
        "representation_fidelity": representation_fidelity, "rank_controls": rank_controls,
        "summary": summary, "original_path_binding": original_path_binding(cells, path_matrices, original),
        "new_midpoint_control_cells": 8, "reused_path_control_cells": 18,
        "evaluated_control_cells": 26, "not_merged_into_batch_counts": True,
        "new_seed_count": 0, "new_winding_computed": False, "n640_computed": False,
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
    (ROOT / "seed6_matrix_midpoint_analysis.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    figure(data, original)
    markdown(data)
    print(json.dumps({"summary": summary, "driver_comparisons": drivers_comparison, "link_summary": data["link_summary"], "original_path_binding": data["original_path_binding"], "cells": 26, "native_links": 24, "entry_links": 288}, ensure_ascii=False, indent=2))
    print("generated seed6_matrix_midpoint_analysis.json seed6-matrix-midpoint.png SEED6_MATRIX_MIDPOINT.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
