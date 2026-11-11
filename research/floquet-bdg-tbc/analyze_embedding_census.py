"""Run both common embeddings over all sixteen preregistered size contrasts."""

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
from analyze_subspace_overlap import compute_subspaces, embedded_orthonormal_basis, source_cell  # noqa: E402
from analyze_embedding_robustness import embedded_cell_average_basis, grid_result  # noqa: E402

PROTOCOL = ROOT / "embedding_census_protocol.json"
SOURCE = ROOT / "repeated_category_analysis.json"
PREVIOUS_LINEAR = ROOT / "subspace_overlap_analysis.json"
PREVIOUS_ROBUST = ROOT / "embedding_robustness_analysis.json"
OLD_INDEPENDENT = ROOT / "multi_seed_independent.json"
NEW_INDEPENDENT = ROOT / "category_new_cells_independent.json"
PREVIOUS_LABELS = {(5, 0.05): "near_miss_low", (5, 0.1): "near_miss_high", (2, 0.1): "reference_weakening"}
plt.rcParams.update({
    "font.sans-serif": ["Microsoft YaHei", "SimHei", "Noto Sans CJK SC", "DejaVu Sans"],
    "axes.unicode_minus": False, "font.size": 10, "figure.dpi": 160,
})


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def case_label(seed, strength):
    return PREVIOUS_LABELS.get((seed, strength), f"seed_{seed}_r_{str(strength).replace('.', 'p')}")


def assignment_counts(cases, method=None, finest=False):
    counts = Counter()
    for case in cases:
        for name, method_data in case["methods"].items():
            if method is not None and name != method:
                continue
            grids = method_data["grids"][-1:] if finest else method_data["grids"]
            counts.update(grid["dominant_assignment"] for grid in grids)
    return dict(counts)


def fmt(value):
    return f"{value:.5g}"


def figure(data):
    fig, axes = plt.subplots(2, 2, figsize=(13, 9.6), constrained_layout=False)
    for case in data["cases"]:
        row = case["method_comparisons"][-1]
        color = "#356A64" if case["strength"] == 0.05 else "#A25B3F"
        for axis, xkey, ykey in ((axes[0, 0], "linear_diagonal_score", "cell_average_diagonal_score"), (axes[0, 1], "linear_swapped_score", "cell_average_swapped_score")):
            axis.scatter(row[xkey], row[ykey], s=48, color=color)
            axis.annotate(f"s{case['seed']},r{case['strength']}", (row[xkey], row[ykey]), xytext=(3, 3), textcoords="offset points", fontsize=7)
            axis.set_xscale("log")
            axis.set_yscale("log")
            axis.grid(alpha=0.2, which="both")
    axes[0, 0].set_title("同谱秩得分：线性 vs 单元平均")
    axes[0, 1].set_title("交换得分：线性 vs 单元平均")
    for axis in axes.flat[:2]:
        axis.set_xlabel("线性点值")
        axis.set_ylabel("单元平均")
    ordered = sorted((row for case in data["cases"] for row in [case["method_comparisons"][-1]]), key=lambda row: row["diagonal_score_change_cell_minus_linear"])
    labels = [f"{case['seed']}/{case['strength']}" for case in sorted(data["cases"], key=lambda case: case["method_comparisons"][-1]["diagonal_score_change_cell_minus_linear"])]
    axes[1, 0].scatter(np.arange(16), [row["diagonal_score_change_cell_minus_linear"] for row in ordered], color="#6F7F92", s=48)
    axes[1, 0].axhline(0, color="#777777", lw=0.8, ls="--")
    axes[1, 0].set_xticks(np.arange(16), labels, rotation=65, ha="right", fontsize=7)
    axes[1, 0].set_ylabel("单元平均同谱秩−线性")
    axes[1, 0].set_title("同谱秩得分的方法差")
    axes[1, 0].grid(axis="y", alpha=0.2)
    joint = Counter()
    for case in data["cases"]:
        row = case["method_comparisons"][-1]
        joint[(row["linear_assignment"], row["cell_average_assignment"])] += 1
    keys = [("diagonal", "diagonal"), ("diagonal", "swapped"), ("swapped", "diagonal"), ("swapped", "swapped")]
    names = ["同谱秩／同谱秩", "同谱秩／交换", "交换／同谱秩", "交换／交换"]
    values = [joint[key] for key in keys]
    axes[1, 1].bar(names, values, color=["#356A64", "#8A9BA8", "#A25B3F", "#8B3A3A"], width=0.6)
    for index, value in enumerate(values):
        axes[1, 1].text(index, value + 0.15, str(value), ha="center", fontsize=12)
    axes[1, 1].set_ylim(0, max(1, max(values) + 2))
    axes[1, 1].set_ylabel("对照数")
    axes[1, 1].set_title("M=4800：线性／单元平均主导分配")
    axes[1, 1].tick_params(axis="x", labelsize=8)
    axes[1, 1].grid(axis="y", alpha=0.2)
    fig.subplots_adjust(top=0.88, bottom=0.17, left=0.08, right=0.97, hspace=0.43, wspace=0.3)
    fig.suptitle("全部16个对照的共同表示审计（M=4800）", fontsize=16, y=0.97)
    fig.savefig(ROOT / "embedding-census.png", bbox_inches="tight")
    plt.close(fig)


def markdown(data):
    summary = data["summary"]
    candidates = summary["swapped_candidate_cases"]
    lines = [
        "# Floquet-BdG 全样本共同表示审计",
        "",
        "> 日期：2026-11-11。全部8个既有种子、2个强度、16个对照；两种共同表示、三个网格。只重算相同本征对，不新增类别、不补算体 winding，未计算 N=640。",
        "",
        "## 一、全样本协议",
        "",
        "线性点值和分片常数单元平均沿用前两轮实现。M=1200／2400／4800，最近对与次近对分别形成二维子空间。原剖面误差门槛为1e-10；前三例两种方法均必须复现到1e-12。",
        "",
        f"实测原剖面最大误差 {data['max_profile_absolute_error']:.3e}；前三例线性最大复现差 {data['previous_linear_reproduction_error']:.3e}，单元平均最大复现差 {data['previous_cell_reproduction_error']:.3e}。",
        "",
        "## 二、M=4800 的全样本结果",
        "",
        "| seed | r | 线性同谱秩 | 单元平均同谱秩 | 线性交换 | 单元平均交换 | 线性主导 | 单元平均主导 |",
        "|---:|---:|---:|---:|---:|---:|:---|:---|",
    ]
    for case in data["cases"]:
        row = case["method_comparisons"][-1]
        lines.append(f"| {case['seed']} | {case['strength']} | {fmt(row['linear_diagonal_score'])} | {fmt(row['cell_average_diagonal_score'])} | {fmt(row['linear_swapped_score'])} | {fmt(row['cell_average_swapped_score'])} | {row['linear_assignment']} | {row['cell_average_assignment']} |")
    lines += [
        "",
        "图 1 插入位置：M=4800 全样本表之后、汇总结论之前。",
        "",
        "![图 1：全样本共同表示审计](embedding-census.png)",
        "",
        "**图 1**　上排为两种方法的得分比较，左下为方法差，右下为主导分配组合。所有图形只描述当前共同表示。",
        "",
        "## 三、全网格汇总与交换候选",
        "",
        f"96个方法×案例×网格组合中，同谱秩分配占优 {summary['diagonal_dominant_count']}/96；两种方法主导分配一致 {summary['same_assignment_count']}/48。全部六个方法网格均为同谱秩的对照有 {summary['fully_diagonal_case_count']}/16。",
        "",
        f"M=4800 上，两种方法主导分配一致 {summary['finest_same_assignment_count']}/16。线性主导计数为 {json.dumps(summary['finest_assignment_counts']['linear_point'], ensure_ascii=False)}，单元平均为 {json.dumps(summary['finest_assignment_counts']['cell_average'], ensure_ascii=False)}。",
        "",
        f"交换候选：{('、'.join(candidates)) if candidates else '无'}。这里的交换候选只表示至少一种方法在 M=4800 上交换得分更高，不是物理态交换证明。",
        "",
        f"两种方法同谱秩得分的最大绝对变化为 {fmt(summary['max_absolute_diagonal_score_change'])}。计数覆盖全部预登记对照，但不是统计总体推断或显著性检验。",
        "",
        "## 四、结论与边界",
        "",
        "前三例的方向结果不能未经验证就外推到全样本；本报告以全部16个对照的直接计算替代这种外推。若有交换候选，应检查其完整矩阵、网格变化和方法依赖，而不是直接命名态交换。",
        "",
        "本轮没有证明表示不变性、同一物理态、真实态追踪、排序交换、网格收敛、次近对拓扑性或体 winding。原类别和响应计数未改变。",
        "",
        "复现：`python research/floquet-bdg-tbc/analyze_embedding_census.py`。32个尺寸单元、96个方法网格、完整矩阵和来源哈希保存在 `embedding_census_analysis.json`。",
        "",
    ]
    for label in candidates:
        case = next(item for item in data["cases"] if item["label"] == label)
        linear = case["methods"]["linear_point"]["grids"][-1]
        cell = case["methods"]["cell_average"]["grids"][-1]
        smallest_angle = min(angle for method in (linear, cell) for row in method["overlap_matrix"] for entry in row for angle in entry["principal_angles_deg"])
        lines += [
            f"## 五、交换候选 {label} 的完整矩阵",
            "",
            f"线性同谱秩={fmt(linear['diagonal_score'])}、交换={fmt(linear['swapped_score'])}；单元平均同谱秩={fmt(cell['diagonal_score'])}、交换={fmt(cell['swapped_score'])}。两种方法在三个网格上均为交换分配占优。",
            "",
            f"矩阵最小主角度为 {fmt(smallest_angle)}°，绝对重叠仍弱，不能把这种相对优势写成高保真态交换。",
            "",
            "| 方法 | O00 | O01 | O10 | O11 |",
            "|:---|---:|---:|---:|---:|",
        ]
        for name, method in (("线性点值", linear), ("单元平均", cell)):
            values = [method["overlap_matrix"][i][j]["overlap"] for i in range(2) for j in range(2)]
            lines.append(f"| {name} | {fmt(values[0])} | {fmt(values[1])} | {fmt(values[2])} | {fmt(values[3])} |")
        lines.append("")
    (ROOT / "EMBEDDING_CENSUS.md").write_text("\n".join(lines), encoding="utf-8")


def main():
    if "--check-only" in sys.argv:
        stored = json.loads((ROOT / "embedding_census_analysis.json").read_text(encoding="utf-8"))
        expected = {
            "protocol_sha256": sha(PROTOCOL), "source_sha256": sha(SOURCE),
            "previous_linear_source_sha256": sha(PREVIOUS_LINEAR),
            "previous_robustness_source_sha256": sha(PREVIOUS_ROBUST),
        }
        if any(stored.get(key) != value for key, value in expected.items()):
            raise ValueError("Full-census evidence is stale")
        if len(stored.get("cases", [])) != 16 or len(stored.get("cells", [])) != 32 or stored.get("new_physics_cells") != 0:
            raise ValueError("Full-census evidence has wrong scope")
        print(json.dumps({"check_only": True, "cases": 16, "cells": 32, "method_grid_count": stored["summary"]["method_grid_count"], "all_passed": True}, ensure_ascii=False))
        return 0
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    previous_linear = json.loads(PREVIOUS_LINEAR.read_text(encoding="utf-8"))
    previous_robust = json.loads(PREVIOUS_ROBUST.read_text(encoding="utf-8"))
    if not json.loads(OLD_INDEPENDENT.read_text(encoding="utf-8")).get("all_passed"):
        raise ValueError("Original independent profile verification has not passed")
    if not json.loads(NEW_INDEPENDENT.read_text(encoding="utf-8")).get("all_passed"):
        raise ValueError("New-cell independent profile verification has not passed")
    embeddings = {"linear_point": embedded_orthonormal_basis, "cell_average": embedded_cell_average_basis}
    cells, cases = [], []
    previous_errors = {"linear_point": 0.0, "cell_average": 0.0}
    for strength in protocol["strengths"]:
        for seed in protocol["seeds"]:
            label = case_label(seed, strength)
            old = next(row for row in source["cases"] if (row["seed"], row["strength"]) == (seed, strength))
            computed = {}
            for n in protocol["n_values"]:
                stored = source_cell(source, n, strength, seed)
                pair_records, subspaces = compute_subspaces(n, strength, seed, stored)
                if any(row["max_profile_absolute_error"] > 1e-10 or row["edge_weight_absolute_error"] > 1e-10 for row in pair_records):
                    raise ValueError(f"Frozen profile gate failed: N={n}, seed={seed}, r={strength}")
                cells.append({"n": n, "strength": strength, "seed": seed, "pairs": pair_records})
                computed[n] = subspaces
            methods = {name: {"grids": [grid_result(computed[400], computed[600], m, embedding) for m in protocol["common_grids"]]} for name, embedding in embeddings.items()}
            comparisons = []
            for index, m in enumerate(protocol["common_grids"]):
                linear = methods["linear_point"]["grids"][index]
                cell = methods["cell_average"]["grids"][index]
                comparisons.append({
                    "m": m, "linear_diagonal_score": linear["diagonal_score"], "cell_average_diagonal_score": cell["diagonal_score"],
                    "diagonal_score_change_cell_minus_linear": cell["diagonal_score"] - linear["diagonal_score"],
                    "linear_swapped_score": linear["swapped_score"], "cell_average_swapped_score": cell["swapped_score"],
                    "max_overlap_entry_absolute_change": max(abs(linear["overlap_matrix"][i][j]["overlap"] - cell["overlap_matrix"][i][j]["overlap"]) for i in range(2) for j in range(2)),
                    "linear_assignment": linear["dominant_assignment"], "cell_average_assignment": cell["dominant_assignment"],
                    "same_dominant_assignment": linear["dominant_assignment"] == cell["dominant_assignment"],
                })
            cases.append({"label": label, "seed": seed, "strength": strength, "original_category": old["category"], "methods": methods, "method_comparisons": comparisons})
            if label in PREVIOUS_LABELS.values():
                old_linear = next(row for row in previous_linear["cases"] if row["label"] == label)
                old_cell = next(row for row in previous_robust["cases"] if row["label"] == label)
                for index in range(3):
                    for method, old_grid in (("linear_point", old_linear["grids"][index]), ("cell_average", old_cell["methods"]["cell_average"]["grids"][index])):
                        grid = methods[method]["grids"][index]
                        previous_errors[method] = max(previous_errors[method], abs(grid["diagonal_score"] - old_grid["diagonal_score"]), abs(grid["swapped_score"] - old_grid["swapped_score"]))
                        for i in range(2):
                            for j in range(2):
                                previous_errors[method] = max(previous_errors[method], abs(grid["overlap_matrix"][i][j]["overlap"] - old_grid["overlap_matrix"][i][j]["overlap"]))
            print(json.dumps({"completed": label, "finest": comparisons[-1]}, ensure_ascii=False), flush=True)
    if max(previous_errors.values()) > 1e-12:
        raise ValueError("Previous three-case embedding evidence was not reproduced")
    comparisons = [row for case in cases for row in case["method_comparisons"]]
    candidates = sorted({case["label"] for case in cases for row in case["method_comparisons"] if row["m"] == 4800 and (row["linear_assignment"] == "swapped" or row["cell_average_assignment"] == "swapped")})
    summary = {
        "method_grid_count": 96, "diagonal_dominant_count": assignment_counts(cases).get("diagonal", 0),
        "method_assignment_counts": {name: assignment_counts(cases, name) for name in embeddings},
        "finest_assignment_counts": {name: assignment_counts(cases, name, True) for name in embeddings},
        "same_assignment_count": sum(row["same_dominant_assignment"] for row in comparisons),
        "finest_same_assignment_count": sum(row["m"] == 4800 and row["same_dominant_assignment"] for row in comparisons),
        "fully_diagonal_case_count": sum(all(grid["dominant_assignment"] == "diagonal" for method in case["methods"].values() for grid in method["grids"]) for case in cases),
        "swapped_candidate_cases": candidates,
        "max_absolute_diagonal_score_change": max(abs(row["diagonal_score_change_cell_minus_linear"]) for row in comparisons),
    }
    data = {
        "schema": "floquet-bdg-embedding-census-analysis-v1", "analysis_date": protocol["analysis_date"],
        "protocol_sha256": sha(PROTOCOL), "source_sha256": sha(SOURCE),
        "previous_linear_source_sha256": sha(PREVIOUS_LINEAR), "previous_robustness_source_sha256": sha(PREVIOUS_ROBUST),
        "original_independent_source_sha256": sha(OLD_INDEPENDENT), "new_independent_source_sha256": sha(NEW_INDEPENDENT),
        "verification_eigenvectors_recomputed": True, "new_physics_cells": 0, "new_seed_count": 0,
        "all_preregistered_contrasts": True, "new_winding_computed": False, "n640_computed": False,
        "representation_invariant_claim": False, "embedding_convergence_proof": False,
        "same_physics_state_tracking_claim": False, "rank_exchange_proven": False,
        "second_pair_topological_claim": False, "new_taxonomy_claim": False, "categories_changed": False,
        "statistical_significance_claim": False, "universal_mechanism_claim": False,
        "original_category_counts": source["category_counts"], "cells": cells, "cases": cases, "summary": summary,
        "previous_linear_reproduction_error": previous_errors["linear_point"],
        "previous_cell_reproduction_error": previous_errors["cell_average"],
        "max_profile_absolute_error": max(pair["max_profile_absolute_error"] for cell in cells for pair in cell["pairs"]),
    }
    (ROOT / "embedding_census_analysis.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    figure(data)
    markdown(data)
    print(json.dumps({"summary": summary, "previous_linear_reproduction_error": data["previous_linear_reproduction_error"], "previous_cell_reproduction_error": data["previous_cell_reproduction_error"], "max_profile_absolute_error": data["max_profile_absolute_error"]}, ensure_ascii=False, indent=2))
    print("generated embedding_census_analysis.json embedding-census.png EMBEDDING_CENSUS.md")


if __name__ == "__main__":
    main()
