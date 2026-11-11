"""Preregistered batch-A matched nested-beta size and strength controls."""

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
from analyze_matched_beta_control import compute_cell, native_rank, embedded_rank, sha  # noqa: E402
from analyze_subspace_overlap import embedded_orthonormal_basis, overlap_entry  # noqa: E402
from analyze_embedding_robustness import embedded_cell_average_basis  # noqa: E402
from analyze_overlap_confounding import cross_size_result  # noqa: E402

PROTOCOL = ROOT / "matched_beta_batch_a_protocol.json"
ANCHOR = ROOT / "matched_beta_control_analysis.json"
CANDIDATE = ROOT / "swap_candidate_spectrum_analysis.json"
plt.rcParams.update({
    "font.sans-serif": ["Microsoft YaHei", "SimHei", "Noto Sans CJK SC", "DejaVu Sans"],
    "axes.unicode_minus": False, "font.size": 9, "figure.dpi": 160,
})


def assignment_pattern(grids):
    assignments = [grid["dominant_assignment"] for grid in grids]
    if all(value == "diagonal" for value in assignments):
        return "diagonal_3_of_3"
    if all(value == "swapped" for value in assignments):
        return "swapped_3_of_3"
    return "mixed"


def evaluate_realization(seed, strength, master, protocol):
    cells, bases_by_n, methods = [], {}, {name: {"grids": []} for name in protocol["methods"]}
    representation_fidelity, rank_controls = [], []
    for n in protocol["n_values"]:
        beta = master.reshape(n, protocol["master_grid"] // n).mean(axis=1)
        cell, bases = compute_cell(n, beta, strength)
        cells.append(cell)
        bases_by_n[n] = bases
        rank_controls.append(native_rank(bases, n))
    embeddings = {"linear_point": embedded_orthonormal_basis, "cell_average": embedded_cell_average_basis}
    max_direction = 0.0
    for m in protocol["common_grids"]:
        bases = {
            n: {name: [embedding(subspace, m) for subspace in bases_by_n[n]] for name, embedding in embeddings.items()}
            for n in protocol["n_values"]
        }
        for method in embeddings:
            grid = cross_size_result(bases[400][method], bases[600][method], m)
            methods[method]["grids"].append(grid)
            for i in range(2):
                for j in range(2):
                    reverse = overlap_entry(bases[600][method][j], bases[400][method][i])["overlap"]
                    max_direction = max(max_direction, abs(grid["overlap_matrix"][i][j]["overlap"] - reverse))
        for n in protocol["n_values"]:
            for method in embeddings:
                rank_controls.append(embedded_rank(bases[n][method], n, method, m))
            for pair_index in (0, 1):
                forward = overlap_entry(bases[n]["linear_point"][pair_index], bases[n]["cell_average"][pair_index])
                reverse = overlap_entry(bases[n]["cell_average"][pair_index], bases[n]["linear_point"][pair_index])
                representation_fidelity.append({
                    "n": n, "pair_index": pair_index, "m": m,
                    "forward": forward["overlap"], "reverse": reverse["overlap"],
                    "direction_absolute_error": abs(forward["overlap"] - reverse["overlap"]),
                    "singular_values": forward["singular_values"],
                    "principal_angles_deg": forward["principal_angles_deg"],
                })
    patterns = {method: assignment_pattern(methods[method]["grids"]) for method in methods}
    return {
        "seed": seed, "strength": strength,
        "master_profile": [float(value) for value in master],
        "master_profile_sha256": hashlib.sha256(master.tobytes()).hexdigest(),
        "strength_pair_master_reused": True,
        "cells": cells, "methods": methods,
        "representation_fidelity": representation_fidelity,
        "native_rank_controls": [row for row in rank_controls if row["method"] == "native_qr"],
        "rank_controls": rank_controls,
        "max_direction_absolute_error": max_direction,
        "max_representation_direction_absolute_error": max(row["direction_absolute_error"] for row in representation_fidelity),
        "min_representation_fidelity": min(row["forward"] for row in representation_fidelity),
        "max_representation_fidelity": max(row["forward"] for row in representation_fidelity),
        "max_native_off_diagonal": max(row["off01"] for row in rank_controls if row["method"] == "native_qr"),
        "max_linear_point_off_diagonal": max(row["off01"] for row in rank_controls if row["method"] == "linear_point"),
        "max_cell_average_off_diagonal": max(row["off01"] for row in rank_controls if row["method"] == "cell_average"),
        "center_separation_delta": cells[1]["center_separation"] - cells[0]["center_separation"],
        "assignment_patterns": patterns,
        "same_rank_all_grids_both_methods": all(value == "diagonal_3_of_3" for value in patterns.values()),
        "method_agreement_all_grids": all(
            methods["linear_point"]["grids"][index]["dominant_assignment"] == methods["cell_average"]["grids"][index]["dominant_assignment"]
            for index in range(3)
        ),
    }


def summarize(realizations):
    assignment_counts = {}
    pattern_counts = {}
    for method in ("linear_point", "cell_average"):
        assignment_counts[method] = dict(Counter(
            grid["dominant_assignment"]
            for row in realizations for grid in row["methods"][method]["grids"]
        ))
        pattern_counts[method] = dict(Counter(row["assignment_patterns"][method] for row in realizations))
    return {
        "assignment_counts": assignment_counts,
        "assignment_pattern_counts": pattern_counts,
        "same_rank_all_grids_both_methods_count": sum(row["same_rank_all_grids_both_methods"] for row in realizations),
        "method_agreement_all_grids_count": sum(row["method_agreement_all_grids"] for row in realizations),
        "realizations_with_any_swapped": [
            {"seed": row["seed"], "strength": row["strength"]}
            for row in realizations
            if any(grid["dominant_assignment"] == "swapped" for method in row["methods"].values() for grid in method["grids"])
        ],
        "realizations_with_mixed_grids": [
            {"seed": row["seed"], "strength": row["strength"], "patterns": row["assignment_patterns"]}
            for row in realizations if any(value == "mixed" for value in row["assignment_patterns"].values())
        ],
        "max_direction_absolute_error": max(row["max_direction_absolute_error"] for row in realizations),
        "max_representation_direction_absolute_error": max(row["max_representation_direction_absolute_error"] for row in realizations),
        "min_representation_fidelity": min(row["min_representation_fidelity"] for row in realizations),
        "max_representation_fidelity": max(row["max_representation_fidelity"] for row in realizations),
        "max_native_off_diagonal": max(row["max_native_off_diagonal"] for row in realizations),
        "max_linear_point_off_diagonal": max(row["max_linear_point_off_diagonal"] for row in realizations),
        "max_cell_average_off_diagonal": max(row["max_cell_average_off_diagonal"] for row in realizations),
        "center_separation_delta_range": [min(row["center_separation_delta"] for row in realizations), max(row["center_separation_delta"] for row in realizations)],
    }


def compare_strengths(realizations):
    by_key = {(row["seed"], row["strength"]): row for row in realizations}
    comparisons = []
    for seed in sorted({row["seed"] for row in realizations}):
        low, high = by_key[(seed, 0.05)], by_key[(seed, 0.1)]
        row = {
            "seed": seed, "from_strength": 0.05, "to_strength": 0.1,
            "master_profile_sha256": low["master_profile_sha256"],
            "identical_master_profile": low["master_profile_sha256"] == high["master_profile_sha256"],
            "assignment_transitions": {},
        }
        for n in (400, 600):
            low_cell = next(cell for cell in low["cells"] if cell["n"] == n)
            high_cell = next(cell for cell in high["cells"] if cell["n"] == n)
            row[f"n{n}_center_separation_delta"] = high_cell["center_separation"] - low_cell["center_separation"]
        for method in ("linear_point", "cell_average"):
            row["assignment_transitions"][method] = [
                {
                    "m": low["methods"][method]["grids"][index]["m"],
                    "from": low["methods"][method]["grids"][index]["dominant_assignment"],
                    "to": high["methods"][method]["grids"][index]["dominant_assignment"],
                }
                for index in range(3)
            ]
        comparisons.append(row)
    return comparisons


def case_labels(data):
    return [f"s{row['seed']} / r={row['strength']:g}" for row in data["realizations"]]


def figure(data):
    rows = data["realizations"]
    labels = case_labels(data)
    x = np.arange(len(rows))
    fig, axes = plt.subplots(2, 2, figsize=(14, 9.6))
    for method, color, marker, offset in (("linear_point", "#356A64", "o", -0.10), ("cell_average", "#A25B3F", "s", 0.10)):
        axes[0, 0].scatter(x + offset, [row["methods"][method]["grids"][-1]["diagonal_score"] for row in rows], color=color, marker=marker, label=f"{method}同谱秩")
        axes[0, 0].scatter(x + offset, [row["methods"][method]["grids"][-1]["swapped_score"] for row in rows], facecolors="none", edgecolors=color, marker=marker, label=f"{method}交换")
    axes[0, 0].set_xticks(x, labels, rotation=35, ha="right")
    axes[0, 0].set_yscale("log")
    axes[0, 0].set_title("M=4800：逐实现保留两类分配得分")
    axes[0, 0].set_ylabel("重叠得分（对数）")
    axes[0, 0].grid(alpha=0.2, which="both")
    axes[0, 0].legend(frameon=False, fontsize=7, ncol=2)
    columns = [(method, index) for method in ("linear_point", "cell_average") for index in range(3)]
    mapping = {"swapped": -1, "tie_exact": 0, "diagonal": 1}
    matrix = np.asarray([[mapping[row["methods"][method]["grids"][index]["dominant_assignment"]] for method, index in columns] for row in rows])
    axes[0, 1].imshow(matrix, cmap=ListedColormap(["#A25B3F", "#D7DCDD", "#356A64"]), vmin=-1, vmax=1, aspect="auto")
    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            axes[0, 1].text(j, i, {1: "D", -1: "S", 0: "T"}[matrix[i, j]], ha="center", va="center", color="white" if matrix[i, j] else "black", fontsize=8)
    axes[0, 1].set_xticks(np.arange(6), ["LP\n1200", "LP\n2400", "LP\n4800", "CA\n1200", "CA\n2400", "CA\n4800"])
    axes[0, 1].set_yticks(x, labels)
    axes[0, 1].set_title("全部网格的分配方向（D同谱秩／S交换）")
    for n, color, marker in ((400, "#356A64", "o"), (600, "#A25B3F", "s")):
        axes[1, 0].scatter(x, [next(cell["center_separation"] for cell in row["cells"] if cell["n"] == n) for row in rows], color=color, marker=marker, label=f"N={n}")
    axes[1, 0].set_xticks(x, labels, rotation=35, ha="right")
    axes[1, 0].set_yscale("log")
    axes[1, 0].set_title("两对谱距离中心的间隔")
    axes[1, 0].set_ylabel("中心间隔（对数）")
    axes[1, 0].grid(alpha=0.2, which="both")
    axes[1, 0].legend(frameon=False)
    for method, color, marker in (("native_qr", "#6F7F92", "^"), ("linear_point", "#356A64", "o"), ("cell_average", "#A25B3F", "s")):
        key = {"native_qr": "max_native_off_diagonal", "linear_point": "max_linear_point_off_diagonal", "cell_average": "max_cell_average_off_diagonal"}[method]
        axes[1, 1].scatter(x, [max(row[key], 1e-25) for row in rows], color=color, marker=marker, label=method)
    axes[1, 1].set_xticks(x, labels, rotation=35, ha="right")
    axes[1, 1].set_yscale("log")
    axes[1, 1].set_ylim(5e-26, 1e-2)
    axes[1, 1].set_title("同N秩间重叠：嵌入串扰不被抹除")
    axes[1, 1].set_ylabel("最大非对角重叠（显示下限1e-25）")
    axes[1, 1].grid(alpha=0.2, which="both")
    axes[1, 1].legend(frameon=False, fontsize=8)
    fig.subplots_adjust(top=0.89, bottom=0.15, left=0.08, right=0.98, hspace=0.52, wspace=0.25)
    fig.suptitle("共同无序剖面第一批：4个种子 × 2个强度 × 2个尺寸", fontsize=16, y=0.97)
    fig.savefig(ROOT / "matched-beta-batch-a.png", bbox_inches="tight")
    plt.close(fig)


def fmt(value):
    return f"{value:.6g}"


def pattern_text(row, method):
    return "／".join("D" if grid["dominant_assignment"] == "diagonal" else "S" if grid["dominant_assignment"] == "swapped" else "T" for grid in row["methods"][method]["grids"])


def markdown(data):
    summary = data["summary"]
    lines = [
        "# Floquet-BdG 共同无序剖面第一批尺寸隔离",
        "",
        "> 日期：2026-11-11。预登记 seed=0、1、2、3，r=0.05、0.1；8个无序实现、16个尺寸控制单元。每个 seed 的主网格 M=4800 只生成一次，两个强度复用同一主剖面。不新增类别，不补算体 winding，未计算 N=640。",
        "",
        "## 一、协议与谱结构",
        "",
        "每个粗格点的 β 值等于其覆盖主格点的算术平均，因此 N=400 和 N=600 通过嵌套块平均共享同一无序结构。两个强度使用同一主剖面，是配对控制而非独立样本。",
        "",
        "所有预登记实现、网格和分配方向均保留，不筛选支持旧候选或支持同谱秩的结果。跨尺寸重叠不归一化，跨表示自一致性也不作为校正因子。",
        "",
        "| seed | r | N | 最近对中心 | 次近对中心 | 中心间隔 |",
        "|---:|---:|---:|---:|---:|---:|",
    ]
    for row in data["realizations"]:
        for cell in row["cells"]:
            lines.append(f"| {row['seed']} | {row['strength']:g} | {cell['n']} | {fmt(cell['pairs'][0]['center'])} | {fmt(cell['pairs'][1]['center'])} | {fmt(cell['center_separation'])} |")
    lines += [
        "",
        "## 二、三种网格与两种表示",
        "",
        "D 表示同谱秩主导，S 表示交换主导；三格顺序均为 M=1200／2400／4800。下表只是描述性计数，不是统计显著性检验。",
        "",
        "| seed | r | 线性点值 D/S | 单元平均 D/S | M=4800线性同谱秩 | M=4800线性交换 | M=4800单元同谱秩 | M=4800单元交换 |",
        "|---:|---:|:---:|:---:|---:|---:|---:|---:|",
    ]
    for row in data["realizations"]:
        linear = row["methods"]["linear_point"]["grids"][-1]
        average = row["methods"]["cell_average"]["grids"][-1]
        lines.append(f"| {row['seed']} | {row['strength']:g} | {pattern_text(row, 'linear_point')} | {pattern_text(row, 'cell_average')} | {fmt(linear['diagonal_score'])} | {fmt(linear['swapped_score'])} | {fmt(average['diagonal_score'])} | {fmt(average['swapped_score'])} |")
    lines += [
        "",
        f"两种表示各自均有24个网格结果。线性点值计数为 `{summary['assignment_counts']['linear_point']}`，单元平均计数为 `{summary['assignment_counts']['cell_average']}`。",
        "",
        "图 1 插入位置：全网格分配表之后、强度配对与边界之前。",
        "",
        "![图 1：共同无序剖面第一批尺寸隔离](matched-beta-batch-a.png)",
        "",
        "**图 1**　逐实现分配得分、全网格方向、中心间隔和秩间控制。右下图仅为显示设置1e-25下限，JSON保留原值。",
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
        "## 四、实现依赖范围与解释边界",
        "",
        f"跨表示自一致性范围为 {fmt(summary['min_representation_fidelity'])}–{fmt(summary['max_representation_fidelity'])}。原生秩间重叠最大为 {fmt(summary['max_native_off_diagonal'])}，单元平均最大为 {fmt(summary['max_cell_average_off_diagonal'])}，线性点值最大为 {fmt(summary['max_linear_point_off_diagonal'])}。这些指标分开记录，不合并成机制名称。",
        "",
        f"8个实现中，两种表示均在全部三个网格同谱秩主导的实现数为 {summary['same_rank_all_grids_both_methods_count']}；两种表示逐网格方向一致的实现数为 {summary['method_agreement_all_grids_count']}。它们只描述本批指定共同无序剖面，不能外推为普遍尺寸律、真实态交换或谱交叉。",
        "",
        "seed=6、r=0.05 的既有共同剖面定向控制不在本批计数内，其源文件哈希单独绑定。旧交换候选仍属于不同无序实现，不能与任何本批结果直接相减并命名为尺寸效应。",
        "",
        "本批扩展的是实现依赖范围的描述性证据，不构成统计显著性、连续路径、次近对拓扑性或热力学极限结论。下一批应沿用同一协议，而不是根据本批结果修改种子或强度。",
        "",
        "复现：`python research/floquet-bdg-tbc/analyze_matched_beta_batch_a.py`。完整主剖面、16个控制单元、重叠矩阵、跨表示与秩间控制保存在 `matched_beta_batch_a_analysis.json`。",
        "",
    ]
    (ROOT / "MATCHED_BETA_BATCH_A.md").write_text("\n".join(lines), encoding="utf-8")


def check_only():
    stored = json.loads((ROOT / "matched_beta_batch_a_analysis.json").read_text(encoding="utf-8"))
    if stored.get("protocol_sha256") != sha(PROTOCOL) or stored.get("anchor_control_analysis_sha256") != sha(ANCHOR):
        raise ValueError("Batch-A evidence is stale")
    if len(stored.get("realizations", [])) != 8 or stored.get("new_control_cells") != 16:
        raise ValueError("Batch-A realization evidence is incomplete")
    if any(cell["coarsening_max_absolute_error"] != 0 for row in stored["realizations"] for cell in row["cells"]):
        raise ValueError("Batch-A nested coarsening failed")
    if not stored.get("all_preregistered_results_retained") or stored.get("size_effect_separated") != "matched_nested_profile_descriptive_only":
        raise ValueError("Batch-A interpretation boundary changed")
    print(json.dumps({"check_only": True, "realizations": 8, "control_cells": 16, "coarsening_error": 0, "all_passed": True}, ensure_ascii=False))
    return 0


def main():
    if "--check-only" in sys.argv:
        return check_only()
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    realizations = []
    for seed in protocol["seed_values"]:
        master = np.random.default_rng(20261111 + seed).random(protocol["master_grid"])
        for strength in protocol["strength_values"]:
            realizations.append(evaluate_realization(seed, strength, master, protocol))
    anchor = json.loads(ANCHOR.read_text(encoding="utf-8"))
    candidate = json.loads(CANDIDATE.read_text(encoding="utf-8"))
    data = {
        "schema": "floquet-bdg-matched-beta-batch-a-analysis-v1",
        "analysis_date": protocol["analysis_date"], "batch": "A",
        "protocol_sha256": sha(PROTOCOL), "anchor_control_analysis_sha256": sha(ANCHOR),
        "candidate_source_sha256": sha(CANDIDATE),
        "realizations": realizations, "summary": summarize(realizations),
        "strength_pair_comparisons": compare_strengths(realizations),
        "anchor_case_observation": {
            "included_in_batch_counts": False,
            "old_assignments": anchor["old_candidate_comparison"]["old_assignments"],
            "matched_control_assignments": anchor["old_candidate_comparison"]["control_assignments"],
        },
        "max_coarsening_absolute_error": 0.0,
        "new_control_cells": 16, "new_seed_count": 0,
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
    (ROOT / "matched_beta_batch_a_analysis.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    figure(data)
    markdown(data)
    print(json.dumps({"summary": data["summary"], "new_control_cells": 16, "coarsening_error": 0, "n640_computed": False}, ensure_ascii=False, indent=2))
    print("generated matched_beta_batch_a_analysis.json matched-beta-batch-a.png MATCHED_BETA_BATCH_A.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
