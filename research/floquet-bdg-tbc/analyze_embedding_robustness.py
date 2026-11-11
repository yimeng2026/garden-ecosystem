"""Test whether cross-size subspace diagnostics depend on the common embedding."""

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
from analyze_subspace_overlap import (  # noqa: E402
    compute_subspaces, embedded_orthonormal_basis, overlap_entry, source_cell,
)

PROTOCOL = ROOT / "embedding_robustness_protocol.json"
SOURCE = ROOT / "repeated_category_analysis.json"
PREVIOUS = ROOT / "subspace_overlap_analysis.json"
OLD_INDEPENDENT = ROOT / "multi_seed_independent.json"
NEW_INDEPENDENT = ROOT / "category_new_cells_independent.json"
LABELS = {
    "near_miss_low": "近 miss：seed=5，r=0.05",
    "near_miss_high": "近 miss：seed=5，r=0.1",
    "reference_weakening": "参考：seed=2，r=0.1",
}
plt.rcParams.update({
    "font.sans-serif": ["Microsoft YaHei", "SimHei", "Noto Sans CJK SC", "DejaVu Sans"],
    "axes.unicode_minus": False, "font.size": 10, "figure.dpi": 160,
})


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def embedded_cell_average_basis(subspace, m):
    """Exact nested-grid average of a piecewise-constant complex cell function."""
    n = subspace.shape[0]
    if m % n:
        raise ValueError(f"Cell-average nested-grid embedding requires M divisible by N: M={m}, N={n}")
    refined = np.repeat(subspace, m // n, axis=0)
    q, _ = np.linalg.qr(refined.reshape((2 * m, 2)), mode="reduced")
    return q


def grid_result(bases400, bases600, m, embedding):
    q400 = [embedding(subspace, m) for subspace in bases400]
    q600 = [embedding(subspace, m) for subspace in bases600]
    matrix = [[overlap_entry(q400[i], q600[j]) for j in range(2)] for i in range(2)]
    diagonal = (matrix[0][0]["overlap"] + matrix[1][1]["overlap"]) / 2
    swapped = (matrix[0][1]["overlap"] + matrix[1][0]["overlap"]) / 2
    return {
        "m": m, "overlap_matrix": matrix,
        "diagonal_score": diagonal, "swapped_score": swapped,
        "dominant_assignment": "diagonal" if diagonal > swapped else "swapped" if swapped > diagonal else "tie_exact",
    }


def fmt(value):
    return f"{value:.6g}"


def figure(data):
    fig, axes = plt.subplots(3, 2, figsize=(13, 10.2), constrained_layout=False)
    for row_index, case in enumerate(data["cases"]):
        x = np.arange(3)
        for column, key, title in ((0, "diagonal_score", "同谱秩分配"), (1, "swapped_score", "交换分配")):
            axis = axes[row_index, column]
            for method, label, color, marker in (("linear_point", "线性点值", "#356A64", "o"), ("cell_average", "单元平均", "#A25B3F", "s")):
                values = [grid[key] for grid in case["methods"][method]["grids"]]
                axis.plot(x, values, color=color, marker=marker, label=label)
                for xi, value in zip(x, values):
                    axis.annotate(f"{value:.2e}", (xi, value), xytext=(3, 3), textcoords="offset points", fontsize=8)
            axis.set_xticks(x, ["M=1200", "M=2400", "M=4800"])
            axis.set_yscale("log")
            axis.set_ylabel("平均重叠得分")
            axis.set_title(f"{LABELS[case['label']]}｜{title}")
            axis.grid(alpha=0.2, which="both")
            axis.legend(frameon=False, fontsize=8)
    fig.subplots_adjust(top=0.9, bottom=0.08, left=0.07, right=0.985, hspace=0.5, wspace=0.2)
    fig.suptitle("同一本征矢、同一网格：只改变共同表示", fontsize=16, y=0.975)
    fig.savefig(ROOT / "embedding-robustness.png", bbox_inches="tight")
    plt.close(fig)


def markdown(data):
    summary = data["summary"]
    lines = [
        "# Floquet-BdG 共同表示稳健性检验",
        "",
        "> 日期：2026-11-11。仅重算三个既有对照、六个既有单元的相同本征对；比较线性点值与分片常数单元平均嵌入。不新增类别、不补算体 winding，未计算 N=640。",
        "",
        "## 一、只改变共同表示",
        "",
        "线性点值嵌入沿用上一轮的 np.interp 与 QR。单元平均嵌入把每个原始格点的复数旋量分量视为该格点单元上的常数；在 M 可整除 N 的嵌套网格上，每个原始值恰好复制到 M/N 个目标单元，再做 QR。",
        "",
        "两种方法使用同一批本征矢、同一组 M=1200／2400／4800 和同一个主子空间重叠定义。上一轮线性结果必须逐项复现到1e-12，原冻结剖面必须复现到1e-10。",
        "",
        f"实测线性结果最大复现差 {data['max_linear_reproduction_error']:.3e}；原剖面最大误差 {data['max_profile_absolute_error']:.3e}。",
        "",
        "## 二、逐网格比较",
        "",
        "| 对照 | M | 线性同谱秩 | 单元平均同谱秩 | 单元平均−线性 | 线性交换 | 单元平均交换 | 主导分配一致 |",
        "|:---|---:|---:|---:|---:|---:|---:|:---:|",
    ]
    for case in data["cases"]:
        for row in case["method_comparisons"]:
            lines.append(f"| {case['seed']}／{case['strength']} | {row['m']} | {fmt(row['linear_diagonal_score'])} | {fmt(row['cell_average_diagonal_score'])} | {fmt(row['diagonal_score_change_cell_minus_linear'])} | {fmt(row['linear_swapped_score'])} | {fmt(row['cell_average_swapped_score'])} | {row['same_dominant_assignment']} |")
    lines += [
        "",
        "图 1 插入位置：逐网格比较表之后、结论之前。",
        "",
        "![图 1：共同表示稳健性](embedding-robustness.png)",
        "",
        "**图 1**　两种嵌入只改变共同表示；对数坐标显示弱重叠的不同数量级，不改变原始数值。",
        "",
        "## 三、结论与解释边界",
        "",
        f"18个方法×案例×网格组合中，同谱秩分配占优 {summary['diagonal_dominant_count']}/18；M=4800 上两种方法主导分配一致 {summary['finest_same_assignment_count']}/3。两种方法的同谱秩得分最大绝对变化为 {fmt(summary['max_absolute_diagonal_score_change'])}。",
        "",
        f"单元平均的同谱秩得分在 {sum(row['diagonal_score_change_cell_minus_linear'] < 0 for case in data['cases'] for row in case['method_comparisons'])}/9 个比较中更低。M=4800 的单元平均得分依次为 {fmt(data['cases'][0]['methods']['cell_average']['grids'][-1]['diagonal_score'])}、{fmt(data['cases'][1]['methods']['cell_average']['grids'][-1]['diagonal_score'])}、{fmt(data['cases'][2]['methods']['cell_average']['grids'][-1]['diagonal_score'])}，绝对重叠仍弱。方向稳定不等于高保真对应。",
        "",
        "方法之间应分别比较分配方向和重叠幅度。即使方向一致，也不等于重叠不变；即使数值相近，也不等于物理态已经唯一确定。若方向改变，则先说明嵌入依赖，而不是选择更符合预期的方法。",
        "",
        "本轮没有证明表示不变性、同一物理态或真实态追踪，也没有证明排序交换、网格收敛、次近对拓扑性或体 winding。原类别及此前响应计数未改变。",
        "",
        "复现：`python research/floquet-bdg-tbc/analyze_embedding_robustness.py`。协议、两种完整重叠矩阵、逐网格差值和来源哈希保存在 `embedding_robustness_analysis.json`。",
        "",
    ]
    (ROOT / "EMBEDDING_ROBUSTNESS.md").write_text("\n".join(lines), encoding="utf-8")


def main():
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    previous = json.loads(PREVIOUS.read_text(encoding="utf-8"))
    if not json.loads(OLD_INDEPENDENT.read_text(encoding="utf-8")).get("all_passed"):
        raise ValueError("Original independent profile verification has not passed")
    if not json.loads(NEW_INDEPENDENT.read_text(encoding="utf-8")).get("all_passed"):
        raise ValueError("New-cell independent profile verification has not passed")
    embeddings = {"linear_point": embedded_orthonormal_basis, "cell_average": embedded_cell_average_basis}
    cells, cases = [], []
    linear_error = 0.0
    for selected in protocol["selected_cases"]:
        label, seed, strength = selected["label"], selected["seed"], selected["strength"]
        old = next(row for row in source["cases"] if (row["seed"], row["strength"]) == (seed, strength))
        old_linear = next(row for row in previous["cases"] if row["label"] == label)
        computed = {}
        for n in protocol["n_values"]:
            stored = source_cell(source, n, strength, seed)
            pair_records, subspaces = compute_subspaces(n, strength, seed, stored)
            if any(row["max_profile_absolute_error"] > 1e-10 or row["edge_weight_absolute_error"] > 1e-10 for row in pair_records):
                raise ValueError(f"Frozen profile gate failed: N={n}, seed={seed}, r={strength}")
            cells.append({"n": n, "strength": strength, "seed": seed, "pairs": pair_records})
            computed[n] = subspaces
        methods = {name: {"grids": [grid_result(computed[400], computed[600], m, embedding) for m in protocol["common_grids"]]} for name, embedding in embeddings.items()}
        for index, grid in enumerate(methods["linear_point"]["grids"]):
            previous_grid = old_linear["grids"][index]
            linear_error = max(linear_error, abs(grid["diagonal_score"] - previous_grid["diagonal_score"]), abs(grid["swapped_score"] - previous_grid["swapped_score"]))
            for i in range(2):
                for j in range(2):
                    linear_error = max(linear_error, abs(grid["overlap_matrix"][i][j]["overlap"] - previous_grid["overlap_matrix"][i][j]["overlap"]))
        comparisons = []
        for index, m in enumerate(protocol["common_grids"]):
            linear = methods["linear_point"]["grids"][index]
            cell = methods["cell_average"]["grids"][index]
            comparisons.append({
                "m": m,
                "linear_diagonal_score": linear["diagonal_score"], "cell_average_diagonal_score": cell["diagonal_score"],
                "diagonal_score_change_cell_minus_linear": cell["diagonal_score"] - linear["diagonal_score"],
                "linear_swapped_score": linear["swapped_score"], "cell_average_swapped_score": cell["swapped_score"],
                "max_overlap_entry_absolute_change": max(abs(linear["overlap_matrix"][i][j]["overlap"] - cell["overlap_matrix"][i][j]["overlap"]) for i in range(2) for j in range(2)),
                "linear_assignment": linear["dominant_assignment"], "cell_average_assignment": cell["dominant_assignment"],
                "same_dominant_assignment": linear["dominant_assignment"] == cell["dominant_assignment"],
            })
        cases.append({"label": label, "seed": seed, "strength": strength, "original_category": old["category"], "methods": methods, "method_comparisons": comparisons})
        print(json.dumps({"completed": label, "comparisons": comparisons}, ensure_ascii=False), flush=True)
    if linear_error > 1e-12:
        raise ValueError("Previous linear embedding result was not reproduced")
    summary = {
        "method_grid_count": 18,
        "diagonal_dominant_count": sum(grid["dominant_assignment"] == "diagonal" for case in cases for method in case["methods"].values() for grid in method["grids"]),
        "finest_same_assignment_count": sum(row["m"] == 4800 and row["same_dominant_assignment"] for case in cases for row in case["method_comparisons"]),
        "max_absolute_diagonal_score_change": max(abs(row["diagonal_score_change_cell_minus_linear"]) for case in cases for row in case["method_comparisons"]),
    }
    data = {
        "schema": "floquet-bdg-embedding-robustness-analysis-v1",
        "analysis_date": protocol["analysis_date"],
        "protocol_sha256": sha(PROTOCOL), "source_sha256": sha(SOURCE), "previous_linear_source_sha256": sha(PREVIOUS),
        "original_independent_source_sha256": sha(OLD_INDEPENDENT), "new_independent_source_sha256": sha(NEW_INDEPENDENT),
        "verification_eigenvectors_recomputed": True, "new_physics_cells": 0, "new_seed_count": 0,
        "new_winding_computed": False, "n640_computed": False,
        "representation_invariant_claim": False, "embedding_convergence_proof": False,
        "same_physics_state_tracking_claim": False, "rank_exchange_proven": False,
        "second_pair_topological_claim": False, "new_taxonomy_claim": False,
        "categories_changed": False, "universal_mechanism_claim": False,
        "original_category_counts": source["category_counts"], "cells": cells, "cases": cases,
        "summary": summary, "max_linear_reproduction_error": linear_error,
        "max_profile_absolute_error": max(pair["max_profile_absolute_error"] for cell in cells for pair in cell["pairs"]),
    }
    (ROOT / "embedding_robustness_analysis.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    figure(data)
    markdown(data)
    print(json.dumps({"summary": summary, "max_linear_reproduction_error": linear_error, "max_profile_absolute_error": data["max_profile_absolute_error"], "new_physics_cells": 0, "n640_computed": False}, ensure_ascii=False, indent=2))
    print("generated embedding_robustness_analysis.json embedding-robustness.png EMBEDDING_ROBUSTNESS.md")


if __name__ == "__main__":
    main()
