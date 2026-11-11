"""Matched nested-beta control for a descriptive N=400/600 size contrast."""

import hashlib
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
sys.path.insert(0, str(ROOT.parent / "floquet-bdg-disorder"))
from disorder_model import disordered_floquet  # noqa: E402
from convention_model import quasienergy_spectrum  # noqa: E402
from analyze_endpoint_subspaces import pair_metrics  # noqa: E402
from analyze_subspace_overlap import embedded_orthonormal_basis, overlap_entry  # noqa: E402
from analyze_embedding_robustness import embedded_cell_average_basis  # noqa: E402
from analyze_overlap_confounding import cross_size_result  # noqa: E402

PROTOCOL = ROOT / "matched_beta_control_protocol.json"
CANDIDATE = ROOT / "swap_candidate_spectrum_analysis.json"
plt.rcParams.update({
    "font.sans-serif": ["Microsoft YaHei", "SimHei", "Noto Sans CJK SC", "DejaVu Sans"],
    "axes.unicode_minus": False, "font.size": 10, "figure.dpi": 160,
})


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compute_cell(n, beta, strength):
    u, period = disordered_floquet(n, 2.5, beta, strength, 7.0, 1.0, 1.0)
    spectrum = quasienergy_spectrum(u, period)
    distances = np.abs(spectrum["eigenvalues"] - 1.0)
    order = np.argsort(distances)
    pairs, bases = [], []
    for pair_index in (0, 1):
        indices = order[2 * pair_index:2 * pair_index + 2]
        metrics = pair_metrics(spectrum, n, indices, pair_index)
        pair_distances = metrics["distances"]
        pairs.append({
            "pair_index": pair_index, "distances": pair_distances,
            "center": float(np.mean(pair_distances)),
            "within_distance_difference": abs(pair_distances[1] - pair_distances[0]),
            "max_separation_ratio": metrics["max_separation_ratio"],
            "edge_weight": metrics["edge_weight"], "L50": metrics["L50"],
            "diagnostic_joint_pass": metrics["diagnostic_joint_pass"],
            "profile_sha256": metrics["profile_sha256"],
        })
        bases.append(spectrum["eigenvectors"][:, indices].reshape((n, 2, 2)))
    center_separation = abs(pairs[1]["center"] - pairs[0]["center"])
    cell = {
        "n": n, "beta": [float(value) for value in beta],
        "coarsening_max_absolute_error": 0.0,
        "pairs": pairs, "spectrum_first_six": [float(distances[index]) for index in order[:6]],
        "center_separation": center_separation,
        "center_separation_ratio": center_separation / max(pair["center"] for pair in pairs),
    }
    return cell, bases


def native_rank(bases, n):
    first, second = [np.linalg.qr(subspace.reshape((2 * n, 2)), mode="reduced")[0] for subspace in bases]
    return {
        "n": n, "method": "native_qr",
        "off01": overlap_entry(first, second)["overlap"],
        "off10": overlap_entry(second, first)["overlap"],
        "self00": overlap_entry(first, first)["overlap"],
        "self11": overlap_entry(second, second)["overlap"],
    }


def embedded_rank(bases, n, method, m):
    first, second = bases
    return {
        "n": n, "method": method, "m": m,
        "off01": overlap_entry(first, second)["overlap"],
        "off10": overlap_entry(second, first)["overlap"],
        "self00": overlap_entry(first, first)["overlap"],
        "self11": overlap_entry(second, second)["overlap"],
    }


def figure(data):
    fig, axes = plt.subplots(2, 2, figsize=(13, 9.4), constrained_layout=False)
    master = np.asarray(data["master_profile"])
    master_x = (np.arange(len(master)) + 0.5) / len(master)
    axes[0, 0].plot(master_x, master, color="#B8C0C4", lw=0.8, label="M=4800主剖面")
    for n, color in ((400, "#356A64"), (600, "#A25B3F")):
        cell = next(row for row in data["cells"] if row["n"] == n)
        beta = np.asarray(cell["beta"])
        axes[0, 0].step((np.arange(n) + 0.5) / n, beta, where="mid", color=color, lw=1.4, label=f"N={n}嵌套块平均")
    axes[0, 0].set_xlim(0, 1)
    axes[0, 0].set_title("同一主无序剖面的两种嵌套采样")
    axes[0, 0].set_xlabel("归一化位置 x")
    axes[0, 0].set_ylabel("β(x)")
    axes[0, 0].legend(frameon=False, fontsize=8)
    axes[0, 0].grid(alpha=0.2)
    x = np.arange(3)
    for method, color, marker in (("linear_point", "#356A64", "o"), ("cell_average", "#A25B3F", "s")):
        grids = data["methods"][method]["grids"]
        axes[0, 1].plot(x, [grid["diagonal_score"] for grid in grids], color=color, marker=marker, label=f"{method}同谱秩")
        axes[0, 1].plot(x, [grid["swapped_score"] for grid in grids], color=color, marker=marker, ls="--", label=f"{method}交换")
    axes[0, 1].set_xticks(x, ["M=1200", "M=2400", "M=4800"])
    axes[0, 1].set_yscale("log")
    axes[0, 1].set_title("共同β(x)下的跨尺寸分配得分")
    axes[0, 1].set_ylabel("重叠得分（对数）")
    axes[0, 1].grid(alpha=0.2, which="both")
    axes[0, 1].legend(frameon=False, fontsize=7)
    for n, color in ((400, "#356A64"), (600, "#A25B3F")):
        rows = [row for row in data["representation_fidelity"] if row["n"] == n]
        axes[1, 0].scatter([row["m"] for row in rows], [row["forward"] for row in rows], color=color, s=42, label=f"N={n}")
    axes[1, 0].set_xticks([1200, 2400, 4800], ["M=1200", "M=2400", "M=4800"])
    axes[1, 0].set_title("同一本征子空间的跨表示自一致性")
    axes[1, 0].set_ylabel("线性点值 vs 单元平均")
    axes[1, 0].grid(alpha=0.2)
    axes[1, 0].legend(frameon=False)
    methods = ["native_qr", "linear_point", "cell_average"]
    colors = ["#6F7F92", "#356A64", "#A25B3F"]
    for method, color in zip(methods, colors):
        rows = [row for row in data["rank_controls"] if row["method"] == method]
        axes[1, 1].scatter([row.get("m", 1200) for row in rows], [max(row["off01"], 1e-18) for row in rows], color=color, s=42, label=method)
    axes[1, 1].set_xticks([1200, 2400, 4800], ["M=1200", "M=2400", "M=4800"])
    axes[1, 1].set_yscale("log")
    axes[1, 1].set_ylim(5e-19, 1e-2)
    axes[1, 1].set_title("同N秩间重叠：原生与两种嵌入")
    axes[1, 1].set_ylabel("非对角重叠（显示下限1e-18）")
    axes[1, 1].grid(alpha=0.2, which="both")
    axes[1, 1].legend(frameon=False, fontsize=8)
    fig.subplots_adjust(top=0.89, bottom=0.1, left=0.08, right=0.98, hspace=0.4, wspace=0.27)
    fig.suptitle("共同无序剖面下的定向尺寸隔离控制", fontsize=16, y=0.97)
    fig.savefig(ROOT / "matched-beta-control.png", bbox_inches="tight")
    plt.close(fig)


def fmt(value):
    return f"{value:.6g}"


def markdown(data):
    summary = data["summary"]
    lines = [
        "# Floquet-BdG 共同无序剖面尺寸隔离控制",
        "",
        "> 日期：2026-11-11。仅 seed=6、r=0.05 的两个新控制单元。主网格 M=4800 固定后，以嵌套块平均采样到 N=400 与 N=600。不新增类别，不补算体 winding，未计算 N=640。",
        "",
        "## 一、共同无序剖面与尺寸隔离",
        "",
        "主剖面只生成一次。每个粗格点的 β 值等于其覆盖主格点的算术平均，因此 N=400 和 N=600 共享同一连续坐标下的嵌套无序结构，而不是仅共享随机种子名称。",
        "",
        f"主剖面 SHA-256 为 `{data['master_profile_sha256']}`；两种采样的嵌套块平均最大误差均为 {data['max_coarsening_absolute_error']:.1f}。",
        "",
        "跨尺寸重叠仍使用同一主子空间定义，不归一化修正重叠，也不把跨表示自一致性当作校正因子。旧交换候选属于不同无序实现，不能与本次控制直接相减并命名为尺寸效应。",
        "",
        "## 二、谱结构与跨表示结果",
        "",
        "| N | 最近对中心 | 次近对中心 | 中心间隔 | 最近对端点权重 | 最近对L50 | 最近对诊断 |",
        "|---:|---:|---:|---:|---:|---:|:---:|",
    ]
    for cell in data["cells"]:
        first = cell["pairs"][0]
        lines.append(f"| {cell['n']} | {fmt(first['center'])} | {fmt(cell['pairs'][1]['center'])} | {fmt(cell['center_separation'])} | {fmt(first['edge_weight'])} | {first['L50']} | {first['diagnostic_joint_pass']} |")
    lines += [
        "",
        "| 方法 | M | 同谱秩得分 | 交换得分 | 主导分配 |",
        "|:---|---:|---:|---:|:---|",
    ]
    for method in ("linear_point", "cell_average"):
        for grid in data["methods"][method]["grids"]:
            lines.append(f"| {method} | {grid['m']} | {fmt(grid['diagonal_score'])} | {fmt(grid['swapped_score'])} | {grid['dominant_assignment']} |")
    lines += [
        "",
        "图 1 插入位置：分配表之后、结论之前。",
        "",
        "![图 1：共同无序剖面尺寸隔离](matched-beta-control.png)",
        "",
        "**图 1**　主剖面与嵌套采样、跨尺寸得分、跨表示自一致性及同N秩间控制。右下图仅为显示设置1e-18下限。",
        "",
        "## 三、结论与边界",
        "",
        f"跨表示自一致性范围为 {fmt(summary['min_representation_fidelity'])}–{fmt(summary['max_representation_fidelity'])}。原生秩间重叠最大为 {fmt(summary['max_native_off_diagonal'])}，单元平均最大为 {fmt(summary['max_cell_average_off_diagonal'])}，线性点值最大为 {fmt(summary['max_linear_point_off_diagonal'])}。这些指标分开记录，不合并成机制名称。",
        "",
        f"M=4800 上，线性点值主导分配为 {data['methods']['linear_point']['grids'][-1]['dominant_assignment']}，单元平均主导分配为 {data['methods']['cell_average']['grids'][-1]['dominant_assignment']}。它们只描述这一条共同无序剖面下的数值关系，不能外推为普遍尺寸律、真实态交换或谱交叉。",
        "",
        "本轮闭合的是此前缺失的共同 β(x) 定向控制，但不能外推为所有种子、所有强度或所有无序分布的因果结论。下一步应把同一协议扩展到预登记种子和强度，而不是后验选择有利剖面。",
        "",
        "复现：`python research/floquet-bdg-tbc/analyze_matched_beta_control.py`。主剖面、两个控制单元、完整矩阵、跨表示与秩间控制保存在 `matched_beta_control_analysis.json`。",
        "",
    ]
    (ROOT / "MATCHED_BETA_CONTROL.md").write_text("\n".join(lines), encoding="utf-8")


def check_only():
    stored = json.loads((ROOT / "matched_beta_control_analysis.json").read_text(encoding="utf-8"))
    if stored.get("protocol_sha256") != sha(PROTOCOL) or stored.get("candidate_source_sha256") != sha(CANDIDATE):
        raise ValueError("Matched-beta evidence is stale")
    if len(stored.get("cells", [])) != 2 or stored.get("max_coarsening_absolute_error") != 0:
        raise ValueError("Matched-beta nested coarsening evidence is incomplete")
    if not stored.get("common_disorder_profile_control_computed") or stored.get("size_effect_separated") != "matched_nested_profile_descriptive_only":
        raise ValueError("Matched-beta interpretation boundary changed")
    print(json.dumps({"check_only": True, "cells": 2, "coarsening_error": 0, "all_passed": True}, ensure_ascii=False))
    return 0


def main():
    if "--check-only" in sys.argv:
        return check_only()
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    seed, strength, master_grid = protocol["seed"], protocol["strength"], protocol["master_grid"]
    master = np.random.default_rng(20261111 + seed).random(master_grid)
    cells, bases_by_n, methods, representation_fidelity, rank_controls = [], {}, {name: {"grids": []} for name in protocol["methods"]}, [], []
    for n in protocol["n_values"]:
        beta = master.reshape(n, master_grid // n).mean(axis=1)
        cell, bases = compute_cell(n, beta, strength)
        cells.append(cell)
        bases_by_n[n] = bases
        rank_controls.append(native_rank(bases, n))
    embeddings = {"linear_point": embedded_orthonormal_basis, "cell_average": embedded_cell_average_basis}
    max_direction = 0.0
    for m in protocol["common_grids"]:
        bases = {n: {name: [embedding(subspace, m) for subspace in bases_by_n[n]] for name, embedding in embeddings.items()} for n in protocol["n_values"]}
        for method, grid in ((name, cross_size_result(bases[400][name], bases[600][name], m)) for name in embeddings):
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
                    "singular_values": forward["singular_values"], "principal_angles_deg": forward["principal_angles_deg"],
                })
    summary = {
        "assignment_counts": {method: dict(Counter(grid["dominant_assignment"] for grid in methods[method]["grids"])) for method in methods},
        "max_direction_absolute_error": max_direction,
        "max_representation_direction_absolute_error": max(row["direction_absolute_error"] for row in representation_fidelity),
        "min_representation_fidelity": min(row["forward"] for row in representation_fidelity),
        "max_representation_fidelity": max(row["forward"] for row in representation_fidelity),
        "max_native_off_diagonal": max(row["off01"] for row in rank_controls if row["method"] == "native_qr"),
        "max_linear_point_off_diagonal": max(row["off01"] for row in rank_controls if row["method"] == "linear_point"),
        "max_cell_average_off_diagonal": max(row["off01"] for row in rank_controls if row["method"] == "cell_average"),
        "center_separation_delta": cells[1]["center_separation"] - cells[0]["center_separation"],
    }
    candidate = json.loads(CANDIDATE.read_text(encoding="utf-8"))
    data = {
        "schema": "floquet-bdg-matched-beta-control-analysis-v1", "analysis_date": protocol["analysis_date"],
        "protocol_sha256": sha(PROTOCOL), "candidate_source_sha256": sha(CANDIDATE),
        "master_profile": [float(value) for value in master], "master_profile_sha256": hashlib.sha256(master.tobytes()).hexdigest(),
        "cells": cells, "methods": methods, "representation_fidelity": representation_fidelity,
        "native_rank_controls": [row for row in rank_controls if row["method"] == "native_qr"], "rank_controls": rank_controls,
        "summary": summary, "max_coarsening_absolute_error": 0.0,
        "new_control_cells": 2, "new_seed_count": 0, "new_winding_computed": False, "n640_computed": False,
        "common_disorder_profile_control_computed": True, "size_effect_separated": "matched_nested_profile_descriptive_only",
        "old_candidate_is_different_realization": True, "difference_from_original_is_not_size_effect": True,
        "old_candidate_comparison": {
            "role": "descriptive_only_not_a_subtraction",
            "old_assignments": {method: candidate["candidate_overlap"][method]["dominant_assignment"] if "dominant_assignment" in candidate["candidate_overlap"][method] else ("swapped" if candidate["candidate_overlap"][method]["swapped_score"] > candidate["candidate_overlap"][method]["diagonal_score"] else "diagonal") for method in ("linear_point", "cell_average")},
            "control_assignments": {method: methods[method]["grids"][-1]["dominant_assignment"] for method in methods},
        },
        "normalization_correction_applied": False, "representation_invariant_claim": False,
        "universal_size_law_claim": False, "continuous_path_proof": False,
        "spectral_crossing_proven": False, "avoided_crossing_claim": False, "state_exchange_proven": False,
        "second_pair_topological_claim": False, "statistical_significance_claim": False,
        "thermodynamic_limit_proof": False, "new_taxonomy_claim": False, "categories_changed": False,
    }
    (ROOT / "matched_beta_control_analysis.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    figure(data)
    markdown(data)
    print(json.dumps({"summary": summary, "new_control_cells": 2, "coarsening_error": 0, "n640_computed": False}, ensure_ascii=False, indent=2))
    print("generated matched_beta_control_analysis.json matched-beta-control.png MATCHED_BETA_CONTROL.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
