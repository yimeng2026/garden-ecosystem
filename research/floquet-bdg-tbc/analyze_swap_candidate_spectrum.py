"""Resolve spectral gaps and overlap terms for the unique swap candidate."""

import hashlib
import json
from pathlib import Path
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.linalg import eig

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / "floquet-bdg-disorder"))
from disorder_model import disordered_floquet  # noqa: E402
sys.path.insert(0, str(ROOT))
from analyze_subspace_overlap import source_cell  # noqa: E402

PROTOCOL = ROOT / "swap_candidate_spectrum_protocol.json"
SOURCE = ROOT / "repeated_category_analysis.json"
CENSUS = ROOT / "embedding_census_analysis.json"
OLD_INDEPENDENT = ROOT / "multi_seed_independent.json"
NEW_INDEPENDENT = ROOT / "category_new_cells_independent.json"
plt.rcParams.update({
    "font.sans-serif": ["Microsoft YaHei", "SimHei", "Noto Sans CJK SC", "DejaVu Sans"],
    "axes.unicode_minus": False, "font.size": 10, "figure.dpi": 160,
})


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compute_cell(n, seed, strength, stored):
    beta = np.random.default_rng(20261111 + seed).random(n)
    u, _ = disordered_floquet(n, 2.5, beta, strength, 7.0, 1.0, 1.0)
    values, vectors = eig(u)
    distances = np.abs(values - 1.0)
    order = np.argsort(distances)
    spectrum = []
    for rank, index in enumerate(order[:6]):
        value = values[index]
        spectrum.append({
            "rank": rank, "eigenvalue_real": float(value.real), "eigenvalue_imag": float(value.imag),
            "phase": float(np.angle(value)), "distance": float(abs(value - 1.0)),
        })
    ranked_distances = [row["distance"] for row in spectrum]
    pairs = []
    for pair_index in (0, 1):
        indices = order[2 * pair_index:2 * pair_index + 2]
        selected = vectors[:, indices]
        projector = selected @ np.linalg.inv(selected.conj().T @ selected) @ selected.conj().T
        profile = np.real(np.diag(projector)).reshape((n, 2)).sum(axis=1) / 2
        old = stored["pairs"][pair_index]
        width = old["edge_sites_per_end"]
        edge = float(profile[:width].sum() + profile[-width:].sum())
        pair_distances = ranked_distances[2 * pair_index:2 * pair_index + 2]
        pairs.append({
            "pair_index": pair_index, "stored_profile_sha256": old["profile_sha256"],
            "max_profile_absolute_error": float(np.max(np.abs(profile - np.asarray(old["profile"])))),
            "edge_weight_absolute_error": abs(edge - old["edge_weight"]),
            "stored_distance_max_absolute_error": max(abs(pair_distances[i] - old["distances"][i]) for i in range(2)),
            "center": float(np.mean(pair_distances)), "within_distance_difference": abs(pair_distances[1] - pair_distances[0]),
            "max_separation_ratio": old["max_separation_ratio"], "diagnostic_joint_pass": old["diagnostic_joint_pass"],
        })
    center_separation = abs(pairs[1]["center"] - pairs[0]["center"])
    return {
        "n": n, "seed": seed, "strength": strength, "spectrum": spectrum, "pairs": pairs,
        "center_separation": center_separation,
        "center_separation_ratio": center_separation / max(pair["center"] for pair in pairs),
        "max_stored_distance_absolute_error": max(pair["stored_distance_max_absolute_error"] for pair in pairs),
    }


def fmt(value):
    return f"{value:.6g}"


def figure(data):
    fig, axes = plt.subplots(2, 2, figsize=(13, 9.2), constrained_layout=False)
    x = np.arange(6)
    for cell, color, offset in zip(data["cells"], ("#356A64", "#A25B3F"), (-0.12, 0.12)):
        distances = [row["distance"] for row in cell["spectrum"]]
        axes[0, 0].vlines(x + offset, 0, distances, color=color, label=f"N={cell['n']}")
        axes[0, 0].scatter(x + offset, distances, color=color, s=30)
    axes[0, 0].set_yscale("log")
    axes[0, 0].set_xticks(x, [f"秩{i}" for i in x])
    axes[0, 0].set_ylabel("|λ−1|（对数坐标）")
    axes[0, 0].set_title("前六个近零谱距离")
    axes[0, 0].grid(alpha=0.2, which="both")
    axes[0, 0].legend(frameon=False)
    for pair_index, color in ((0, "#356A64"), (1, "#A25B3F")):
        centers = [cell["pairs"][pair_index]["center"] for cell in data["cells"]]
        axes[0, 1].plot([400, 600], centers, marker="o", color=color, label=f"第{pair_index+1}对中心")
        for cell, center in zip(data["cells"], centers):
            axes[0, 1].annotate(f"{center:.3e}", (cell["n"], center), xytext=(4, 4), textcoords="offset points", fontsize=8)
    axes[0, 1].set_xticks([400, 600], ["N=400", "N=600"])
    axes[0, 1].set_ylabel("谱距离中心")
    axes[0, 1].set_title("对内简并之外：两对中心并不重合")
    axes[0, 1].grid(alpha=0.2)
    axes[0, 1].legend(frameon=False)
    width = 0.34
    x2 = np.arange(2)
    for index, cell in enumerate(data["cells"]):
        values = [pair["max_separation_ratio"] for pair in cell["pairs"]]
        axes[1, 0].bar(x2 + (index - 0.5) * width, values, width, color=("#356A64", "#A25B3F")[index], label=f"N={cell['n']}")
        for xi, value in zip(x2 + (index - 0.5) * width, values):
            axes[1, 0].text(xi, value + 0.025, f"{value:.3g}", ha="center", fontsize=8)
    axes[1, 0].set_xticks(x2, ["最近对", "次近对"])
    axes[1, 0].set_ylim(0, 1.18)
    axes[1, 0].set_ylabel("既有分离比")
    axes[1, 0].set_title("次近对没有额外的谱隔离")
    axes[1, 0].grid(axis="y", alpha=0.2)
    axes[1, 0].legend(frameon=False)
    labels = ["O00", "O01", "O10", "O11"]
    x4 = np.arange(4)
    for index, (method, label, color) in enumerate((("linear_point", "线性点值", "#356A64"), ("cell_average", "单元平均", "#A25B3F"))):
        matrix = data["candidate_overlap"][method]["overlap_matrix"]
        values = [matrix[i][j]["overlap"] for i in range(2) for j in range(2)]
        axes[1, 1].bar(x4 + (index - 0.5) * width, values, width, color=color, label=label)
        for xi, value in zip(x4 + (index - 0.5) * width, values):
            axes[1, 1].text(xi, value + 0.0001, f"{value:.2e}", ha="center", fontsize=7, rotation=45)
    axes[1, 1].set_xticks(x4, labels)
    axes[1, 1].margins(y=0.25)
    axes[1, 1].set_ylabel("M=4800 重叠")
    axes[1, 1].set_title("交换优势来自交叉项略高")
    axes[1, 1].grid(axis="y", alpha=0.2)
    axes[1, 1].legend(frameon=False)
    fig.subplots_adjust(top=0.88, bottom=0.11, left=0.08, right=0.97, hspace=0.43, wspace=0.3)
    fig.suptitle("seed=6，r=0.05：谱结构与交换候选", fontsize=16, y=0.97)
    fig.savefig(ROOT / "swap-candidate-spectrum.png", bbox_inches="tight")
    plt.close(fig)


def markdown(data):
    first, second = data["cells"]
    lines = [
        "# Floquet-BdG 交换候选谱结构审计",
        "",
        "> 日期：2026-11-11。只重算 seed=6、r=0.05 的两个既有尺寸单元，前六个近零谱距离与两对子空间。不新增类别、不补算体 winding，未计算 N=640。",
        "",
        "## 一、谱距离与对内 TBC 简并",
        "",
        "按 |λ−1| 升序排列，报告前六个距离和相位。对内距离差用于数值复现 TBC 简并；1e-10 仅是复现容差，不是物理近简并阈值。",
        "",
        "| N | 谱秩 | λ实部 | λ虚部 | 相位 | \\|λ−1\\| |",
        "|---:|---:|---:|---:|---:|---:|",
    ]
    for cell in data["cells"]:
        for row in cell["spectrum"]:
            lines.append(f"| {cell['n']} | {row['rank']} | {fmt(row['eigenvalue_real'])} | {fmt(row['eigenvalue_imag'])} | {fmt(row['phase'])} | {fmt(row['distance'])} |")
    lines += [
        "",
        "## 二、两对中心间隔与既有谱隔离",
        "",
        "| N | 对 | 距离中心 | 对内距离差 | 既有分离比 | profile联合诊断 |",
        "|---:|---:|---:|---:|---:|:---:|",
    ]
    for cell in data["cells"]:
        for pair in cell["pairs"]:
            lines.append(f"| {cell['n']} | {pair['pair_index']} | {fmt(pair['center'])} | {fmt(pair['within_distance_difference'])} | {fmt(pair['max_separation_ratio'])} | {pair['diagnostic_joint_pass']} |")
    lines += [
        "",
        f"N=400 的两对中心间隔为 {fmt(first['center_separation'])}，相对中心间隔为 {fmt(first['center_separation_ratio'])}；N=600 分别为 {fmt(second['center_separation'])} 和 {fmt(second['center_separation_ratio'])}。两对中心不精确重合，但这里没有另设近简并判据。",
        "",
        f"中心间隔的尺寸差为 {fmt(data['size_comparison']['center_separation_delta'])}。次近对的既有分离比在两种尺寸均为1，且 profile 联合诊断均不通过，不能把交换候选解释为新的孤立拓扑端点。",
        "",
        "图 1 插入位置：谱结构表之后、重叠矩阵之前。",
        "",
        "![图 1：交换候选谱结构](swap-candidate-spectrum.png)",
        "",
        "**图 1**　谱距离、两对中心、既有分离比与交换矩阵并列。谱秩由排序构造，不是参数路径上的态追踪。",
        "",
        "## 三、交换优势的矩阵来源",
        "",
        "| 方法 | O00 | O01 | O10 | O11 | 同谱秩得分 | 交换得分 |",
        "|:---|---:|---:|---:|---:|---:|---:|",
    ]
    for method, label in (("linear_point", "线性点值"), ("cell_average", "单元平均")):
        row = data["candidate_overlap"][method]
        values = [row["overlap_matrix"][i][j]["overlap"] for i in range(2) for j in range(2)]
        lines.append(f"| {label} | {fmt(values[0])} | {fmt(values[1])} | {fmt(values[2])} | {fmt(values[3])} | {fmt(row['diagonal_score'])} | {fmt(row['swapped_score'])} |")
    lines += [
        "",
        "两种方法的 O01 都分别大于 O00 和 O11，使交换平均分略高。该矩阵关系在三个网格和两种共同表示上成立，但主角度仍大，且次近对没有额外谱隔离。",
        "",
        "## 四、结论：交换候选不等于谱交叉",
        "",
        "对内 TBC 简并与两对中心间隔是不同问题。静态尺寸中的谱秩按定义排序，不能观察到排序自己发生交换；两个尺寸之间也没有连续参数路径，因此不能证明谱交叉或避免交叉。",
        "",
        "当前结果只支持：交换候选来自特定交叉重叠项，而不是已经证明的物理态交换、近简并相变或体 winding 改变。后续若要检验态交换，应在固定尺寸上构造连续参数路径并追踪子空间。",
        "",
        "复现：`python research/floquet-bdg-tbc/analyze_swap_candidate_spectrum.py`。原始谱值、距离中心、间隔、重叠矩阵和来源哈希保存在 `swap_candidate_spectrum_analysis.json`。",
        "",
    ]
    (ROOT / "SWAP_CANDIDATE_SPECTRUM.md").write_text("\n".join(lines), encoding="utf-8")


def main():
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    census = json.loads(CENSUS.read_text(encoding="utf-8"))
    if not json.loads(OLD_INDEPENDENT.read_text(encoding="utf-8")).get("all_passed"):
        raise ValueError("Original independent profile verification has not passed")
    if not json.loads(NEW_INDEPENDENT.read_text(encoding="utf-8")).get("all_passed"):
        raise ValueError("New-cell independent profile verification has not passed")
    seed, strength = protocol["seed"], protocol["strength"]
    cells = []
    for n in protocol["n_values"]:
        stored = source_cell(source, n, strength, seed)
        cell = compute_cell(n, seed, strength, stored)
        if any(pair["max_profile_absolute_error"] > 1e-10 or pair["edge_weight_absolute_error"] > 1e-10 or pair["stored_distance_max_absolute_error"] > 1e-10 for pair in cell["pairs"]):
            raise ValueError(f"Frozen spectrum/profile gate failed: N={n}")
        cells.append(cell)
        print(json.dumps({"completed_cell": n, "center_separation": cell["center_separation"], "center_separation_ratio": cell["center_separation_ratio"], "pairs": cell["pairs"]}, ensure_ascii=False), flush=True)
    old = next(row for row in census["cases"] if row["label"] == "seed_6_r_0p05")
    overlap = {}
    for method in ("linear_point", "cell_average"):
        grid = old["methods"][method]["grids"][-1]
        matrix = grid["overlap_matrix"]
        overlap[method] = {
            "overlap_matrix": matrix, "diagonal_score": grid["diagonal_score"], "swapped_score": grid["swapped_score"],
            "cross_term_exceeds_each_diagonal_entry": matrix[0][1]["overlap"] > matrix[0][0]["overlap"] and matrix[0][1]["overlap"] > matrix[1][1]["overlap"],
        }
    first, second = cells
    data = {
        "schema": "floquet-bdg-swap-candidate-spectrum-analysis-v1", "analysis_date": protocol["analysis_date"],
        "protocol_sha256": sha(PROTOCOL), "source_sha256": sha(SOURCE), "census_source_sha256": sha(CENSUS),
        "original_independent_source_sha256": sha(OLD_INDEPENDENT), "new_independent_source_sha256": sha(NEW_INDEPENDENT),
        "verification_eigenvectors_recomputed": True, "new_physics_cells": 0, "new_seed_count": 0,
        "new_winding_computed": False, "n640_computed": False,
        "cross_pair_exact_degenerate": all(cell["center_separation"] == 0 for cell in cells),
        "near_degeneracy_threshold_added": False, "spectral_crossing_proven": False,
        "avoided_crossing_claim": False, "state_exchange_proven": False, "second_pair_topological_claim": False,
        "sorted_order_is_constructed_not_tracking": True, "rank_swap_observed": False,
        "new_taxonomy_claim": False, "categories_changed": False, "universal_mechanism_claim": False,
        "original_category_counts": source["category_counts"], "cells": cells,
        "size_comparison": {
            "center_separation_delta": second["center_separation"] - first["center_separation"],
            "pair0_center_delta": second["pairs"][0]["center"] - first["pairs"][0]["center"],
            "pair1_center_delta": second["pairs"][1]["center"] - first["pairs"][1]["center"],
        },
        "candidate_overlap": overlap,
        "max_profile_absolute_error": max(pair["max_profile_absolute_error"] for cell in cells for pair in cell["pairs"]),
    }
    (ROOT / "swap_candidate_spectrum_analysis.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    figure(data)
    markdown(data)
    print(json.dumps({"size_comparison": data["size_comparison"], "max_profile_absolute_error": data["max_profile_absolute_error"], "cross_pair_exact_degenerate": data["cross_pair_exact_degenerate"], "spectral_crossing_proven": False, "state_exchange_proven": False}, ensure_ascii=False, indent=2))
    print("generated swap_candidate_spectrum_analysis.json swap-candidate-spectrum.png SWAP_CANDIDATE_SPECTRUM.md")


if __name__ == "__main__":
    main()
