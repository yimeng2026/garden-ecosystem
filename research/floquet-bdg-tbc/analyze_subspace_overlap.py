"""Compare two-dimensional Floquet subspaces after common-grid spinor embedding."""

import hashlib
import json
import math
from collections import Counter
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

PROTOCOL = ROOT / "subspace_overlap_protocol.json"
SOURCE = ROOT / "repeated_category_analysis.json"
PAIR_RESPONSE = ROOT / "pair_response_analysis.json"
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


def source_cell(source, n, strength, seed):
    return next(row for row in source["all_cells"] if (row["n"], row["strength"], row["seed"]) == (n, strength, seed))


def compute_subspaces(n, strength, seed, stored_case):
    beta = np.random.default_rng(20261111 + seed).random(n)
    u, _ = disordered_floquet(n, 2.5, beta, strength, 7.0, 1.0, 1.0)
    values, vectors = eig(u)
    order = np.argsort(np.abs(values - 1.0))
    pair_records, subspaces = [], []
    for pair_index in (0, 1):
        indices = order[2 * pair_index:2 * pair_index + 2]
        selected = vectors[:, indices]
        projector = selected @ np.linalg.inv(selected.conj().T @ selected) @ selected.conj().T
        profile = np.real(np.diag(projector)).reshape((n, 2)).sum(axis=1) / 2
        stored = stored_case["pairs"][pair_index]
        edge_sites = stored["edge_sites_per_end"]
        edge = float(profile[:edge_sites].sum() + profile[-edge_sites:].sum())
        pair_records.append({
            "pair_index": pair_index, "stored_profile_sha256": stored["profile_sha256"],
            "max_profile_absolute_error": float(np.max(np.abs(profile - np.asarray(stored["profile"])))),
            "edge_weight_absolute_error": abs(edge - stored["edge_weight"]),
        })
        subspaces.append(selected.reshape((n, 2, 2)))
    return pair_records, subspaces


def embedded_orthonormal_basis(subspace, m):
    n = subspace.shape[0]
    source_x = (np.arange(n) + 0.5) / n
    target_x = (np.arange(m) + 0.5) / m
    refined = np.empty((m, 2, 2), dtype=complex)
    for component in range(2):
        for column in range(2):
            values = subspace[:, component, column]
            refined[:, component, column] = np.interp(target_x, source_x, values.real) + 1j * np.interp(target_x, source_x, values.imag)
    q, _ = np.linalg.qr(refined.reshape((2 * m, 2)), mode="reduced")
    return q


def overlap_entry(first, second):
    singular = np.linalg.svd(first.conj().T @ second, compute_uv=False)
    return {
        "singular_values": [float(value) for value in singular],
        "overlap": float(np.sum(singular ** 2) / 2),
        "principal_angles_deg": [float(math.degrees(math.acos(min(1.0, max(0.0, value))))) for value in singular],
    }


def grid_result(bases400, bases600, m):
    q400 = [embedded_orthonormal_basis(subspace, m) for subspace in bases400]
    q600 = [embedded_orthonormal_basis(subspace, m) for subspace in bases600]
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
    fig, axes = plt.subplots(3, 2, figsize=(13, 10.4), constrained_layout=False)
    styles = [("#356A64", "o"), ("#A25B3F", "s"), ("#6F7F92", "^"), ("#8B3A3A", "D")]
    for row_index, case in enumerate(data["cases"]):
        grids = case["grids"]
        x = np.arange(len(grids))
        for i in range(2):
            for j in range(2):
                color, marker = styles[2 * i + j]
                values = [grid["overlap_matrix"][i][j]["overlap"] for grid in grids]
                axes[row_index, 0].plot(x, values, color=color, marker=marker, label=f"N400第{i+1}对→N600第{j+1}对")
                for xi, value in zip(x, values):
                    axes[row_index, 0].annotate(f"{value:.2e}", (xi, value), xytext=(3, 3), textcoords="offset points", fontsize=7)
        axes[row_index, 0].set_xticks(x, [f"M={grid['m']}" for grid in grids])
        axes[row_index, 0].set_yscale("log")
        axes[row_index, 0].set_ylabel("主子空间重叠")
        axes[row_index, 0].set_title(LABELS[case["label"]] + "：完整重叠矩阵")
        axes[row_index, 0].grid(alpha=0.2)
        axes[row_index, 0].legend(frameon=False, fontsize=7, loc="best")
        for key, label, color in (("diagonal_score", "同谱秩分配", "#356A64"), ("swapped_score", "交换分配", "#A25B3F")):
            values = [grid[key] for grid in grids]
            axes[row_index, 1].plot(x, values, marker="o", color=color, label=label)
            for xi, value in zip(x, values):
                axes[row_index, 1].annotate(f"{value:.2e}", (xi, value), xytext=(3, 3), textcoords="offset points", fontsize=8)
        axes[row_index, 1].set_xticks(x, [f"M={grid['m']}" for grid in grids])
        axes[row_index, 1].set_yscale("log")
        axes[row_index, 1].set_ylabel("平均重叠得分")
        axes[row_index, 1].set_title("谱秩保持与交换的数值比较")
        axes[row_index, 1].grid(alpha=0.2)
        axes[row_index, 1].legend(frameon=False, fontsize=8)
    fig.subplots_adjust(top=0.9, bottom=0.08, left=0.07, right=0.985, hspace=0.52, wspace=0.2)
    fig.suptitle("共同细网格上的主子空间重叠：不是直接跨维点积", fontsize=16, y=0.975)
    fig.savefig(ROOT / "subspace-overlap.png", bbox_inches="tight")
    plt.close(fig)


def markdown(data):
    lines = [
        "# Floquet-BdG 跨尺寸子空间重叠诊断",
        "",
        "> 日期：2026-11-11。仅重算三个既有对照、六个既有尺寸单元的相同本征对；没有新物理单元、不新增类别、不补算体 winding，未计算 N=640。",
        "",
        "## 一、共同网格与主子空间定义",
        "",
        "N=400 与 N=600 的本征矢维数不同，不能直接点积。将每个复数内部旋量分量从格心 (i+1/2)/N 线性插值到共同 M 网格，再做约化 QR 正交化。M 预先固定为1200、2400、4800。",
        "",
        "对两个二维子空间计算 Q400_i^H Q600_j 的奇异值 s1、s2，重叠 Oij=(s1²+s2²)/2，主角度为 acos(sk)。使用子空间而非单个本征矢，可消除相位和子空间内部旋转的任意性。",
        "",
        f"所有重算剖面均回到原冻结数据：最大剖面误差 {data['max_profile_absolute_error']:.3e}，门槛为1e-10。",
        "",
        "## 二、共同网格结果",
        "",
        "| 对照 | M | 同谱秩分配得分 | 交换分配得分 | 数值主导分配 |",
        "|:---|---:|---:|---:|:---|",
    ]
    for case in data["cases"]:
        for grid in case["grids"]:
            lines.append(f"| {case['seed']}／{case['strength']} | {grid['m']} | {fmt(grid['diagonal_score'])} | {fmt(grid['swapped_score'])} | {grid['dominant_assignment']} |")
    lines += [
        "",
        "图 1 插入位置：共同网格得分表之后、最细网格矩阵之前。",
        "",
        "![图 1：共同细网格主子空间重叠](subspace-overlap.png)",
        "",
        "**图 1**　左列为四个跨尺寸子空间重叠，右列为同谱秩和交换分配的平均得分。得分只用于当前嵌入诊断。",
        "",
        "## 三、最细网格 M=4800 的重叠矩阵",
        "",
    ]
    for case in data["cases"]:
        grid = case["grids"][-1]
        lines += [
            f"### {LABELS[case['label']]}",
            "",
            "| N400＼N600 | 第1对 | 第2对 |",
            "|:---:|---:|---:|",
        ]
        for i in range(2):
            values = []
            for j in range(2):
                entry = grid["overlap_matrix"][i][j]
                angles = entry["principal_angles_deg"]
                values.append(f"O={fmt(entry['overlap'])}；角度={fmt(angles[0])}°／{fmt(angles[1])}°")
            lines.append(f"| 第{i+1}对 | {values[0]} | {values[1]} |")
        lines.append("")
    lines += [
        "## 四、能说明什么，不能说明什么",
        "",
        f"三个对照在 M=1200、2400、4800 上都由同谱秩分配取得较高分。M=4800 的同谱秩得分依次为 {data['cases'][0]['grids'][-1]['diagonal_score']:.6g}、{data['cases'][1]['grids'][-1]['diagonal_score']:.6g}、{data['cases'][2]['grids'][-1]['diagonal_score']:.6g}，交换得分依次为 {data['cases'][0]['grids'][-1]['swapped_score']:.6g}、{data['cases'][1]['grids'][-1]['swapped_score']:.6g}、{data['cases'][2]['grids'][-1]['swapped_score']:.6g}。",
        "",
        "因此，当前嵌入下没有由交换得分占优支持的排序交换候选；但绝对重叠均很弱，不能把相对得分优势解释为高保真态对应。三个网格上的主导分配不变，也不等于完成网格收敛证明。",
        "",
        "重叠矩阵同时保留同谱秩与交叉项，因此可以检查‘直接按谱排序配对’是否得到较高的数值对应得分。矩阵行固定属于 N=400、列固定属于 N=600，交换 i、j 不会同时交换尺寸，故矩阵无需对称。若交换分配更高，只能称为排序交换候选，不能直接宣称发生了物理态交换。",
        "",
        "线性插值是一种选定的共同表示，不是连续极限或真实态追踪。三个网格用于观察数值稳定性，不构成网格收敛证明；局域尖峰、振荡和简并仍可能影响结果。",
        "",
        "本轮没有证明同一物理态、排序交换、次近对拓扑性、体 winding、材料实现或热力学极限。原类别及此前16对照符号计数均未改变。",
        "",
        "复现：`python research/floquet-bdg-tbc/analyze_subspace_overlap.py`。协议、剖面误差、奇异值、主角度、分配得分和来源哈希保存在 `subspace_overlap_analysis.json`。",
        "",
    ]
    (ROOT / "SUBSPACE_OVERLAP.md").write_text("\n".join(lines), encoding="utf-8")


def main():
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    pair_response = json.loads(PAIR_RESPONSE.read_text(encoding="utf-8"))
    if not json.loads(OLD_INDEPENDENT.read_text(encoding="utf-8")).get("all_passed"):
        raise ValueError("Original independent profile verification has not passed")
    if not json.loads(NEW_INDEPENDENT.read_text(encoding="utf-8")).get("all_passed"):
        raise ValueError("New-cell independent profile verification has not passed")
    cells, cases = [], []
    for selected in protocol["selected_cases"]:
        label, seed, strength = selected["label"], selected["seed"], selected["strength"]
        old = next(row for row in source["cases"] if (row["seed"], row["strength"]) == (seed, strength))
        computed = {}
        for n in protocol["n_values"]:
            stored = source_cell(source, n, strength, seed)
            pair_records, subspaces = compute_subspaces(n, strength, seed, stored)
            if any(row["max_profile_absolute_error"] > 1e-10 or row["edge_weight_absolute_error"] > 1e-10 for row in pair_records):
                raise ValueError(f"Frozen profile gate failed: N={n}, seed={seed}, r={strength}")
            cells.append({"n": n, "strength": strength, "seed": seed, "pairs": pair_records})
            computed[n] = subspaces
        grids = [grid_result(computed[400], computed[600], m) for m in protocol["common_grids"]]
        cases.append({
            "label": label, "seed": seed, "strength": strength, "original_category": old["category"],
            "grids": grids,
            "assignment_stable_across_grids": len({grid["dominant_assignment"] for grid in grids}) == 1,
            "diagonal_score_change_1200_to_4800": grids[-1]["diagonal_score"] - grids[0]["diagonal_score"],
            "swapped_score_change_1200_to_4800": grids[-1]["swapped_score"] - grids[0]["swapped_score"],
        })
        print(json.dumps({"completed": label, "assignments": [grid["dominant_assignment"] for grid in grids], "diagonal": [grid["diagonal_score"] for grid in grids], "swapped": [grid["swapped_score"] for grid in grids]}, ensure_ascii=False), flush=True)
    counts = Counter(case["grids"][-1]["dominant_assignment"] for case in cases)
    data = {
        "schema": "floquet-bdg-subspace-overlap-analysis-v1",
        "analysis_date": protocol["analysis_date"],
        "protocol_sha256": sha(PROTOCOL), "source_sha256": sha(SOURCE), "pair_response_source_sha256": sha(PAIR_RESPONSE),
        "original_independent_source_sha256": sha(OLD_INDEPENDENT), "new_independent_source_sha256": sha(NEW_INDEPENDENT),
        "eigensolver": "scipy.linalg.eig", "projector": "direct_gram_inverse",
        "pair_identity": "common_grid_principal_subspace_diagnostic",
        "verification_eigenvectors_recomputed": True, "new_physics_cells": 0, "new_seed_count": 0,
        "new_winding_computed": False, "n640_computed": False,
        "same_physics_state_tracking_claim": False, "rank_exchange_proven": False,
        "second_pair_topological_claim": False, "grid_convergence_proof": False,
        "new_taxonomy_claim": False, "categories_changed": False, "universal_mechanism_claim": False,
        "original_category_counts": source["category_counts"],
        "previous_pair_response_counts": {
            "edge": pair_response["edge_relation_counts"], "L50": pair_response["L50_relation_counts"],
        },
        "cells": cells, "cases": cases,
        "finest_assignment_counts": dict(counts),
        "max_profile_absolute_error": max(pair["max_profile_absolute_error"] for cell in cells for pair in cell["pairs"]),
    }
    (ROOT / "subspace_overlap_analysis.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    figure(data)
    markdown(data)
    print(json.dumps({"finest_assignment_counts": data["finest_assignment_counts"], "max_profile_absolute_error": data["max_profile_absolute_error"], "new_physics_cells": 0, "n640_computed": False}, ensure_ascii=False, indent=2))
    print("generated subspace_overlap_analysis.json subspace-overlap.png SUBSPACE_OVERLAP.md")


if __name__ == "__main__":
    main()
