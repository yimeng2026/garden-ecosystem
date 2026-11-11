"""Separate rank, embedding and disorder-profile confounding in cross-size overlaps."""

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
from analyze_subspace_overlap import (  # noqa: E402
    compute_subspaces, embedded_orthonormal_basis, overlap_entry, source_cell,
)
from analyze_embedding_robustness import embedded_cell_average_basis  # noqa: E402
from analyze_embedding_census import case_label  # noqa: E402

PROTOCOL = ROOT / "overlap_confounding_protocol.json"
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


def cross_size_result(q400, q600, m):
    matrix = [[overlap_entry(q400[i], q600[j]) for j in range(2)] for i in range(2)]
    diagonal = (matrix[0][0]["overlap"] + matrix[1][1]["overlap"]) / 2
    swapped = (matrix[0][1]["overlap"] + matrix[1][0]["overlap"]) / 2
    return {
        "m": m, "overlap_matrix": matrix,
        "diagonal_score": diagonal, "swapped_score": swapped,
        "dominant_assignment": "diagonal" if diagonal > swapped else "swapped" if swapped > diagonal else "tie_exact",
    }


def scalar_embedding(values, m, method):
    n = len(values)
    if method == "linear_point":
        source_x = (np.arange(n) + 0.5) / n
        target_x = (np.arange(m) + 0.5) / m
        return np.interp(target_x, source_x, values)
    if method == "cell_average":
        if m % n:
            raise ValueError(f"Cell-average scalar embedding requires M divisible by N: M={m}, N={n}")
        return np.repeat(values, m // n)
    raise ValueError(f"Unknown scalar embedding: {method}")


def beta_mismatch(beta400, beta600, m, method):
    refined400 = scalar_embedding(beta400, m, method)
    refined600 = scalar_embedding(beta600, m, method)
    difference = refined400 - refined600
    return {
        "method": method, "m": m,
        "rms_absolute_difference": float(np.sqrt(np.mean(difference ** 2))),
        "mean_absolute_difference": float(np.mean(np.abs(difference))),
        "max_absolute_difference": float(np.max(np.abs(difference))),
        "pearson_correlation": float(np.corrcoef(refined400, refined600)[0, 1]),
    }


def location(case, grid, row):
    return {
        "seed": case["seed"], "strength": case["strength"], "n": row.get("n"),
        "pair_index": row.get("pair_index"), "m": grid["m"], "method": row.get("method"),
    }


def figure(data):
    fig, axes = plt.subplots(2, 2, figsize=(13, 9.8), constrained_layout=False)
    cases = data["cases"]
    x = np.arange(len(cases))
    labels = [f"s{case['seed']}/r{case['strength']}" for case in cases]
    for method, color, marker in (("linear_point", "#356A64", "o"), ("cell_average", "#A25B3F", "s")):
        values = [case["methods"][method]["grids"][-1]["diagonal_score"] for case in cases]
        axes[0, 0].scatter(x, values, color=color, marker=marker, s=42, label=method)
    axes[0, 0].set_yscale("log")
    axes[0, 0].set_title("M=4800：原始跨尺寸同谱秩得分")
    axes[0, 0].set_ylabel("重叠得分（对数）")
    axes[0, 0].legend(frameon=False)
    minima, maxima = [], []
    for case in cases:
        grid = case["diagnostics"][-1]
        values = [row["forward"] for row in grid["representation_fidelity"]]
        minima.append(min(values))
        maxima.append(max(values))
    axes[0, 1].vlines(x, minima, maxima, color="#8A9BA8", lw=1.2)
    axes[0, 1].scatter(x, minima, color="#6F7F92", s=42, label="每例最小值")
    axes[0, 1].scatter(x, maxima, color="#B08B57", s=30, marker="^", label="每例最大值")
    axes[0, 1].set_yscale("log")
    axes[0, 1].set_title("M=4800：同一本征子空间的跨表示自一致性")
    axes[0, 1].set_ylabel("线性点值 vs 单元平均")
    axes[0, 1].legend(frameon=False, fontsize=8)
    for method, color, marker in (("linear_point", "#356A64", "o"), ("cell_average", "#A25B3F", "s")):
        values = [case["diagnostics"][-1]["beta_profile_methods"][method]["rms_absolute_difference"] for case in cases]
        axes[1, 0].scatter(x, values, color=color, marker=marker, s=42, label=method)
    axes[1, 0].set_title("M=4800：同一 seed 不等于同一 β(x)")
    axes[1, 0].set_ylabel("N400／N600 剖面 RMS 差")
    axes[1, 0].legend(frameon=False)
    for axis in axes.flat[:3]:
        axis.set_xticks(x, labels, rotation=65, ha="right", fontsize=7)
        axis.grid(alpha=0.2, which="both")
    for method, color, marker in (("linear_point", "#356A64", "o"), ("cell_average", "#A25B3F", "s")):
        for m_index, m in enumerate(data["protocol_common_grids"]):
            values = [max(row["max_off_diagonal"] for row in case["diagnostics"][m_index]["same_n_rank_controls"] if row["method"] == method) for case in cases]
            axes[1, 1].scatter(np.full(len(cases), m_index) + (-0.08 if method == "linear_point" else 0.08), np.maximum(values, 1e-18), color=color, marker=marker, s=28, alpha=0.75)
    axes[1, 1].set_xticks(range(3), [f"M={m}" for m in data["protocol_common_grids"]])
    axes[1, 1].set_yscale("log")
    axes[1, 1].set_ylim(5e-19, 1e-2)
    axes[1, 1].set_title("共同网格嵌入后的秩间重叠")
    axes[1, 1].set_ylabel("最大非对角重叠（显示下限1e-18）")
    axes[1, 1].grid(alpha=0.2, which="both")
    fig.subplots_adjust(top=0.89, bottom=0.16, left=0.08, right=0.98, hspace=0.48, wspace=0.28)
    fig.suptitle("跨尺寸重叠差异的可分离性审计", fontsize=16, y=0.97)
    fig.savefig(ROOT / "overlap-confounding-audit.png", bbox_inches="tight")
    plt.close(fig)


def fmt(value):
    return f"{value:.6g}"


def markdown(data):
    summary = data["summary"]
    lines = [
        "# Floquet-BdG 重叠差异混杂审计",
        "",
        "> 日期：2026-11-11。全部16个既有对照、32个尺寸单元、三个共同网格和两种表示。只重算既有本征对，不新增物理单元或类别，不补算体 winding，未计算 N=640。",
        "",
        "## 一、四类测量必须分开",
        "",
        "跨尺寸重叠沿用 Oᵢⱼ=(s₁²+s₂²)/2。新增的同尺寸秩间控制比较同一 N 的最近对与次近对；跨表示自一致性比较同一本征子空间的线性点值基与单元平均基；β(x) 失配则直接比较两条实际无序数组在共同网格上的差异。",
        "",
        "本轮不做归一化修正，不把跨尺寸得分除以跨表示自一致性，也不把这些描述量转换成物理态保真度。",
        "",
        f"全部跨尺寸矩阵已复现，最大误差 {data['max_cross_size_reproduction_error']:.3e}；冻结剖面最大误差 {data['max_profile_absolute_error']:.3e}。",
        "",
        "## 二、全样本汇总",
        "",
        "| 诊断 | 数量 | 实测范围或上界 | 能排除什么 | 不能推出什么 |",
        "|:---|---:|:---|:---|:---|",
        f"| 同尺寸秩间控制 | {summary['same_n_rank_control_count']}＋{summary['native_same_n_rank_control_count']}原生 | 原生最大 {fmt(summary['max_native_same_n_off_diagonal'])}；线性嵌入 {fmt(summary['max_linear_point_same_n_off_diagonal'])}；单元平均 {fmt(summary['max_cell_average_same_n_off_diagonal'])} | 原生本征矢正交性丢失 | 线性嵌入门槛通过或真实态交换 |",
        f"| 跨表示自一致性 | {summary['representation_fidelity_count']} | {fmt(summary['min_representation_fidelity'])}–{fmt(summary['max_representation_fidelity'])} | 只改变表示不影响读数 | 表示不变性或尺寸不变性 |",
        f"| β(x) 剖面比较 | {summary['beta_profile_comparison_count']} | RMS {fmt(summary['min_beta_rms_absolute_difference'])}–{fmt(summary['max_beta_rms_absolute_difference'])}；最大｜相关｜ {fmt(summary['max_absolute_beta_pearson_correlation'])} | 同 seed 就是同一无序实现 | 未匹配尺寸差的唯一来源 |",
        f"| 跨尺寸复现 | {summary['method_grid_count']} | 最大复现差 {fmt(data['max_cross_size_reproduction_error'])} | 旧结果无法复算 | 尺寸因果、统计显著性 |",
        "",
        "图 1 插入位置：全样本汇总之后、逐案例表之前。",
        "",
        "![图 1：重叠差异混杂审计](overlap-confounding-audit.png)",
        "",
        "**图 1**　原始跨尺寸得分、跨表示范围、β(x) RMS 差和同尺寸秩间控制。右下图仅为显示设置10⁻¹⁸下限，JSON保留原值。",
        "",
        "## 三、M=4800 逐案例对照",
        "",
        "| 对照 | 线性同谱秩 | 单元平均同谱秩 | 跨表示最小值 | 线性β RMS | 单元平均β RMS | 主导一致 |",
        "|:---|---:|---:|---:|---:|---:|:---:|",
    ]
    for case in data["cases"]:
        diagnostic = case["diagnostics"][-1]
        fidelity = min(row["forward"] for row in diagnostic["representation_fidelity"])
        linear = case["methods"]["linear_point"]["grids"][-1]
        cell = case["methods"]["cell_average"]["grids"][-1]
        lines.append(f"| s{case['seed']}／r{case['strength']} | {fmt(linear['diagonal_score'])} | {fmt(cell['diagonal_score'])} | {fmt(fidelity)} | {fmt(diagnostic['beta_profile_methods']['linear_point']['rms_absolute_difference'])} | {fmt(diagnostic['beta_profile_methods']['cell_average']['rms_absolute_difference'])} | {linear['dominant_assignment'] == cell['dominant_assignment']} |")
    lines += [
        "",
        "## 四、结论与未竟控制",
        "",
        f"原生 QR 的秩间重叠最大为 {fmt(summary['max_native_same_n_off_diagonal'])}，单元平均嵌入最大为 {fmt(summary['max_cell_average_same_n_off_diagonal'])}，但线性点值嵌入达到 {fmt(summary['max_linear_point_same_n_off_diagonal'])}。预登记10⁻¹²秩间门槛未通过，说明线性插值可诱导秩间串扰；这不是原始谱排序交换证明。",
        "",
        f"跨表示自一致性最低为 {fmt(summary['min_representation_fidelity'])}，位置为 {json.dumps(summary['min_representation_fidelity_location'], ensure_ascii=False)}。它直接量化了表示选择的影响，但不能作为跨尺寸得分的校正因子。",
        "",
        f"96个 β(x) 比较中，RMS 低于0.1的项目有 {summary['beta_rms_below_0p1_count']} 个。相同随机种子分别生成不同长度数组后，格心坐标并不对齐，因此同一 seed 不等于同一无序实现。现有跨尺寸差异**不能归因于尺寸**单独作用：尺寸、无序实现与共同表示选择仍然混杂。",
        "",
        "下一步需要预先固定同一个连续或嵌套无序剖面 β(x)，在 N=400 与 N=600 上采样，再重算相同诊断；这才构成尺寸隔离控制。未完成该控制前，不宣称尺寸因果、普适标度、真实态交换或体 winding。",
        "",
        "复现：`python research/floquet-bdg-tbc/analyze_overlap_confounding.py`。完整矩阵、192个跨表示记录、192个嵌入后秩间控制、32个原生秩间控制和96个无序剖面比较保存在 `overlap_confounding_analysis.json`。",
        "",
    ]
    (ROOT / "OVERLAP_CONFOUNDING_AUDIT.md").write_text("\n".join(lines), encoding="utf-8")


def check_only():
    stored = json.loads((ROOT / "overlap_confounding_analysis.json").read_text(encoding="utf-8"))
    expected = {"protocol_sha256": sha(PROTOCOL), "source_sha256": sha(CENSUS)}
    if any(stored.get(key) != value for key, value in expected.items()):
        raise ValueError("Overlap-confounding evidence is stale")
    if len(stored.get("cases", [])) != 16 or len(stored.get("cells", [])) != 32:
        raise ValueError("Overlap-confounding evidence has wrong census scope")
    if stored.get("size_effect_separated") or stored.get("normalization_correction_applied"):
        raise ValueError("Overlap-confounding evidence violates its interpretation boundary")
    if stored.get("same_n_embedding_rank_gate_passed") is not False:
        raise ValueError("The failed preregistered same-N embedding rank gate was not preserved")
    print(json.dumps({"check_only": True, "cases": 16, "cells": 32, "same_n_embedding_rank_gate_passed": False, "all_passed": True}, ensure_ascii=False))
    return 0


def main():
    if "--check-only" in sys.argv:
        return check_only()
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    census = json.loads(CENSUS.read_text(encoding="utf-8"))
    if not json.loads(OLD_INDEPENDENT.read_text(encoding="utf-8")).get("all_passed"):
        raise ValueError("Original independent profile verification has not passed")
    if not json.loads(NEW_INDEPENDENT.read_text(encoding="utf-8")).get("all_passed"):
        raise ValueError("New-cell independent profile verification has not passed")
    embeddings = {"linear_point": embedded_orthonormal_basis, "cell_average": embedded_cell_average_basis}
    cells, cases = [], []
    max_cross_error = 0.0
    for strength in protocol["strengths"]:
        for seed in protocol["seeds"]:
            label = case_label(seed, strength)
            old_case = next(row for row in census["cases"] if row["label"] == label)
            original = next(row for row in source["cases"] if (row["seed"], row["strength"]) == (seed, strength))
            computed, betas = {}, {}
            for n in protocol["n_values"]:
                stored = source_cell(source, n, strength, seed)
                pair_records, subspaces = compute_subspaces(n, strength, seed, stored)
                if any(row["max_profile_absolute_error"] > 1e-10 or row["edge_weight_absolute_error"] > 1e-10 for row in pair_records):
                    raise ValueError(f"Frozen profile gate failed: N={n}, seed={seed}, r={strength}")
                cells.append({"n": n, "strength": strength, "seed": seed, "pairs": pair_records})
                computed[n] = subspaces
                betas[n] = np.random.default_rng(20261111 + seed).random(n)
            native_rank_rows = []
            for n in protocol["n_values"]:
                native = [np.linalg.qr(subspace.reshape((2 * n, 2)), mode="reduced")[0] for subspace in computed[n]]
                first, second = native
                self00 = overlap_entry(first, first)["overlap"]
                self11 = overlap_entry(second, second)["overlap"]
                off01 = overlap_entry(first, second)["overlap"]
                off10 = overlap_entry(second, first)["overlap"]
                native_rank_rows.append({
                    "n": n, "method": "native_qr", "self00": self00, "self11": self11,
                    "off01": off01, "off10": off10,
                    "max_self_error": max(abs(self00 - 1), abs(self11 - 1)),
                    "max_off_diagonal": max(off01, off10),
                })
            methods = {name: {"grids": []} for name in embeddings}
            diagnostics = []
            for grid_index, m in enumerate(protocol["common_grids"]):
                bases = {n: {name: [embedding(subspace, m) for subspace in computed[n]] for name, embedding in embeddings.items()} for n in protocol["n_values"]}
                for name in embeddings:
                    grid = cross_size_result(bases[400][name], bases[600][name], m)
                    old_grid = old_case["methods"][name]["grids"][grid_index]
                    if grid["dominant_assignment"] != old_grid["dominant_assignment"]:
                        raise ValueError(f"Previous assignment changed: {label}, {name}, M={m}")
                    max_cross_error = max(max_cross_error, abs(grid["diagonal_score"] - old_grid["diagonal_score"]), abs(grid["swapped_score"] - old_grid["swapped_score"]))
                    for i in range(2):
                        for j in range(2):
                            max_cross_error = max(max_cross_error, abs(grid["overlap_matrix"][i][j]["overlap"] - old_grid["overlap_matrix"][i][j]["overlap"]))
                    methods[name]["grids"].append(grid)
                rank_rows = []
                for n in protocol["n_values"]:
                    for name in embeddings:
                        first, second = bases[n][name]
                        self00 = overlap_entry(first, first)["overlap"]
                        self11 = overlap_entry(second, second)["overlap"]
                        off01 = overlap_entry(first, second)["overlap"]
                        off10 = overlap_entry(second, first)["overlap"]
                        rank_rows.append({
                            "n": n, "method": name, "self00": self00, "self11": self11,
                            "off01": off01, "off10": off10,
                            "max_self_error": max(abs(self00 - 1), abs(self11 - 1)),
                            "max_off_diagonal": max(off01, off10),
                        })
                fidelity_rows = []
                for n in protocol["n_values"]:
                    for pair_index in protocol["pair_indices"]:
                        forward_entry = overlap_entry(bases[n]["linear_point"][pair_index], bases[n]["cell_average"][pair_index])
                        reverse_entry = overlap_entry(bases[n]["cell_average"][pair_index], bases[n]["linear_point"][pair_index])
                        fidelity_rows.append({
                            "n": n, "pair_index": pair_index, "method": "linear_point_vs_cell_average",
                            "forward": forward_entry["overlap"], "reverse": reverse_entry["overlap"],
                            "direction_absolute_error": abs(forward_entry["overlap"] - reverse_entry["overlap"]),
                            "singular_values": forward_entry["singular_values"],
                            "principal_angles_deg": forward_entry["principal_angles_deg"],
                        })
                diagnostics.append({
                    "m": m, "same_n_rank_controls": rank_rows, "representation_fidelity": fidelity_rows,
                    "beta_profile_methods": {name: beta_mismatch(betas[400], betas[600], m, name) for name in embeddings},
                })
            cases.append({
                "label": label, "seed": seed, "strength": strength, "original_category": original["category"],
                "native_same_n_rank_controls": native_rank_rows, "methods": methods, "diagnostics": diagnostics,
            })
            print(json.dumps({"completed": label, "grids": len(diagnostics)}, ensure_ascii=False), flush=True)
    if max_cross_error > 1e-12:
        raise ValueError("Previous full-census cross-size evidence was not reproduced")
    rank_rows = [row for case in cases for grid in case["diagnostics"] for row in grid["same_n_rank_controls"]]
    native_rank_rows = [row for case in cases for row in case["native_same_n_rank_controls"]]
    fidelity_rows = [row for case in cases for grid in case["diagnostics"] for row in grid["representation_fidelity"]]
    beta_rows = [row for case in cases for grid in case["diagnostics"] for row in grid["beta_profile_methods"].values()]
    min_fidelity = min(row["forward"] for row in fidelity_rows)
    min_fidelity_location = next(location(case, grid, row) for case in cases for grid in case["diagnostics"] for row in grid["representation_fidelity"] if row["forward"] == min_fidelity)
    assignments = Counter(grid["dominant_assignment"] for case in cases for method in case["methods"].values() for grid in method["grids"])
    summary = {
        "method_grid_count": len(cases) * 2 * 3,
        "same_n_rank_control_count": len(rank_rows),
        "native_same_n_rank_control_count": len(native_rank_rows),
        "representation_fidelity_count": len(fidelity_rows),
        "beta_profile_comparison_count": len(beta_rows),
        "assignment_counts": dict(assignments),
        "max_same_n_self_error": max(row["max_self_error"] for row in rank_rows),
        "max_same_n_off_diagonal": max(row["max_off_diagonal"] for row in rank_rows),
        "max_native_same_n_off_diagonal": max(row["max_off_diagonal"] for row in native_rank_rows),
        "max_linear_point_same_n_off_diagonal": max(row["max_off_diagonal"] for row in rank_rows if row["method"] == "linear_point"),
        "max_cell_average_same_n_off_diagonal": max(row["max_off_diagonal"] for row in rank_rows if row["method"] == "cell_average"),
        "max_representation_direction_absolute_error": max(row["direction_absolute_error"] for row in fidelity_rows),
        "min_representation_fidelity": min_fidelity,
        "median_representation_fidelity": float(np.median([row["forward"] for row in fidelity_rows])),
        "max_representation_fidelity": max(row["forward"] for row in fidelity_rows),
        "min_representation_fidelity_location": min_fidelity_location,
        "min_beta_rms_absolute_difference": min(row["rms_absolute_difference"] for row in beta_rows),
        "median_beta_rms_absolute_difference": float(np.median([row["rms_absolute_difference"] for row in beta_rows])),
        "max_beta_rms_absolute_difference": max(row["rms_absolute_difference"] for row in beta_rows),
        "max_absolute_beta_pearson_correlation": max(abs(row["pearson_correlation"]) for row in beta_rows),
        "beta_rms_below_0p1_count": sum(row["rms_absolute_difference"] < 0.1 for row in beta_rows),
    }
    data = {
        "schema": "floquet-bdg-overlap-confounding-analysis-v1", "analysis_date": protocol["analysis_date"],
        "protocol_sha256": sha(PROTOCOL), "source_sha256": sha(CENSUS), "frozen_source_sha256": sha(SOURCE),
        "original_independent_source_sha256": sha(OLD_INDEPENDENT), "new_independent_source_sha256": sha(NEW_INDEPENDENT),
        "protocol_common_grids": protocol["common_grids"],
        "verification_eigenvectors_recomputed": True, "new_physics_cells": 0, "new_seed_count": 0,
        "new_winding_computed": False, "n640_computed": False,
        "same_n_embedding_rank_gate_passed": summary["max_same_n_off_diagonal"] <= protocol["same_n_rank_gate"],
        "native_control_added_after_observed_leakage": True,
        "normalization_correction_applied": False, "size_effect_separated": False,
        "same_disorder_realization": False, "common_disorder_profile_control_computed": False,
        "representation_invariant_claim": False, "same_physics_state_tracking_claim": False,
        "rank_exchange_proven": False, "second_pair_topological_claim": False,
        "new_taxonomy_claim": False, "statistical_significance_claim": False,
        "thermodynamic_limit_proof": False, "categories_changed": False,
        "original_category_counts": source["category_counts"], "cells": cells, "cases": cases,
        "summary": summary, "max_cross_size_reproduction_error": max_cross_error,
        "max_profile_absolute_error": max(pair["max_profile_absolute_error"] for cell in cells for pair in cell["pairs"]),
    }
    (ROOT / "overlap_confounding_analysis.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    figure(data)
    markdown(data)
    print(json.dumps({"summary": summary, "max_cross_size_reproduction_error": max_cross_error, "max_profile_absolute_error": data["max_profile_absolute_error"], "new_physics_cells": 0, "n640_computed": False}, ensure_ascii=False, indent=2))
    print("generated overlap_confounding_analysis.json overlap-confounding-audit.png OVERLAP_CONFOUNDING_AUDIT.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
