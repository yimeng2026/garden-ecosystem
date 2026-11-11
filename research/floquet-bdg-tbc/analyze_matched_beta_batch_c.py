"""Preregistered r=0.2 batch-C controls and unique three-batch descriptive coverage."""

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
from analyze_matched_beta_batch_a import evaluate_realization, fmt, pattern_text, sha, summarize  # noqa: E402

PROTOCOL = ROOT / "matched_beta_batch_c_protocol.json"
BATCH_A = ROOT / "matched_beta_batch_a_analysis.json"
BATCH_B = ROOT / "matched_beta_batch_b_analysis.json"
CANDIDATE = ROOT / "swap_candidate_spectrum_analysis.json"
REPORT_DATE = "2026-11-12"
plt.rcParams.update({
    "font.sans-serif": ["Microsoft YaHei", "SimHei", "Noto Sans CJK SC", "DejaVu Sans"],
    "axes.unicode_minus": False, "font.size": 9, "figure.dpi": 160,
})


def compare_high_strengths(realizations, prior_realizations):
    current_by_seed = {row["seed"]: row for row in realizations}
    prior_by_key = {(row["seed"], row["strength"]): row for row in prior_realizations}
    comparisons = []
    for seed in sorted(current_by_seed):
        old = prior_by_key[(seed, 0.1)]
        new = current_by_seed[seed]
        row = {
            "seed": seed, "from_strength": 0.1, "to_strength": 0.2,
            "source_batch": "A" if seed <= 3 else "B",
            "master_profile_sha256": new["master_profile_sha256"],
            "identical_master_profile": new["master_profile_sha256"] == old["master_profile_sha256"],
            "assignment_transitions": {},
        }
        for n in (400, 600):
            old_cell = next(cell for cell in old["cells"] if cell["n"] == n)
            new_cell = next(cell for cell in new["cells"] if cell["n"] == n)
            row[f"n{n}_center_separation_delta"] = new_cell["center_separation"] - old_cell["center_separation"]
        for method in ("linear_point", "cell_average"):
            transitions = []
            for index in range(3):
                before = old["methods"][method]["grids"][index]
                after = new["methods"][method]["grids"][index]
                transitions.append({
                    "m": after["m"], "from": before["dominant_assignment"], "to": after["dominant_assignment"],
                    "diagonal_score_ratio": after["diagonal_score"] / before["diagonal_score"] if before["diagonal_score"] else None,
                    "swapped_score_ratio": after["swapped_score"] / before["swapped_score"] if before["swapped_score"] else None,
                })
            row["assignment_transitions"][method] = transitions
        comparisons.append(row)
    return comparisons


def ratio_range(comparisons, method, key):
    values = [row[key] for comparison in comparisons for row in comparison["assignment_transitions"][method] if row[key] is not None]
    return [min(values), max(values)] if values else [None, None]


def summarize_strength_pairs(comparisons):
    transition_counts = {}
    for method in ("linear_point", "cell_average"):
        transitions = [row for comparison in comparisons for row in comparison["assignment_transitions"][method]]
        transition_counts[method] = {
            "changed": sum(row["from"] != row["to"] for row in transitions),
            "diagonal_to_swapped": sum(row["from"] == "diagonal" and row["to"] == "swapped" for row in transitions),
            "swapped_to_diagonal": sum(row["from"] == "swapped" and row["to"] == "diagonal" for row in transitions),
            "other_changes": sum(row["from"] != row["to"] and not {row["from"], row["to"]} == {"diagonal", "swapped"} for row in transitions),
            "diagonal_score_ratio_range": ratio_range(comparisons, method, "diagonal_score_ratio"),
            "swapped_score_ratio_range": ratio_range(comparisons, method, "swapped_score_ratio"),
        }
    return {
        "n400_center_separation_delta_range": [min(row["n400_center_separation_delta"] for row in comparisons), max(row["n400_center_separation_delta"] for row in comparisons)],
        "n600_center_separation_delta_range": [min(row["n600_center_separation_delta"] for row in comparisons), max(row["n600_center_separation_delta"] for row in comparisons)],
        "assignment_transition_counts": transition_counts,
    }


def combined_summary(batch_a, batch_b, batch_c):
    batches = [batch_a, batch_b, batch_c]
    key_sets = [{(row["seed"], row["strength"]) for row in batch["realizations"]} for batch in batches]
    if key_sets[0] & key_sets[1] or key_sets[0] & key_sets[2] or key_sets[1] & key_sets[2]:
        raise ValueError("Duplicate seed-strength keys across A+B+C")
    keys = set().union(*key_sets)
    assignment_counts = {}
    for method in ("linear_point", "cell_average"):
        counts = Counter()
        for batch in batches:
            counts.update(batch["summary"]["assignment_counts"][method])
        assignment_counts[method] = dict(counts)
    by_strength = {}
    all_rows = [row for batch in batches for row in batch["realizations"]]
    for strength in (0.05, 0.1, 0.2):
        rows = [row for row in all_rows if row["strength"] == strength]
        by_strength[str(strength)] = {
            "realization_count": len(rows),
            "assignment_counts": {
                method: dict(Counter(grid["dominant_assignment"] for row in rows for grid in row["methods"][method]["grids"]))
                for method in ("linear_point", "cell_average")
            },
        }
    lower = min(batch["summary"]["center_separation_delta_range"][0] for batch in batches)
    upper = max(batch["summary"]["center_separation_delta_range"][1] for batch in batches)
    return {
        "realization_count": len(keys), "control_cells": 2 * len(keys),
        "unique_seed_strength_keys": True, "reused_anchor_count": 1,
        "assignment_counts": assignment_counts, "by_strength": by_strength,
        "same_rank_all_grids_both_methods_count": sum(batch["summary"]["same_rank_all_grids_both_methods_count"] for batch in batches),
        "method_agreement_all_grids_count": sum(batch["summary"]["method_agreement_all_grids_count"] for batch in batches),
        "min_representation_fidelity": min(batch["summary"]["min_representation_fidelity"] for batch in batches),
        "max_representation_fidelity": max(batch["summary"]["max_representation_fidelity"] for batch in batches),
        "center_separation_delta_range": [lower, upper],
        "size_effect_separated": "matched_nested_profile_descriptive_only",
        "universal_size_law_claim": False, "statistical_significance_claim": False,
        "spectral_crossing_proven": False, "state_exchange_proven": False,
    }


def figure(data):
    rows = data["realizations"]
    labels = [f"s{row['seed']}" for row in rows]
    x = np.arange(len(rows))
    fig, axes = plt.subplots(2, 2, figsize=(14, 9.6))
    for method, color, marker, offset in (("linear_point", "#356A64", "o", -0.10), ("cell_average", "#A25B3F", "s", 0.10)):
        axes[0, 0].scatter(x + offset, [row["methods"][method]["grids"][-1]["diagonal_score"] for row in rows], color=color, marker=marker, label=f"{method}同谱秩")
        axes[0, 0].scatter(x + offset, [row["methods"][method]["grids"][-1]["swapped_score"] for row in rows], facecolors="none", edgecolors=color, marker=marker, label=f"{method}交换")
    axes[0, 0].set_xticks(x, labels)
    axes[0, 0].set_yscale("log")
    axes[0, 0].set_title("r=0.2：M=4800逐种子分配得分")
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
    axes[0, 1].set_yticks(x, [f"seed={row['seed']}" for row in rows])
    axes[0, 1].set_title("r=0.2全部网格方向")
    width = 0.34
    for n, color, offset in ((400, "#356A64", -width / 2), (600, "#A25B3F", width / 2)):
        values = [row[f"n{n}_center_separation_delta"] for row in data["strength_pair_comparisons"]]
        axes[1, 0].bar(x + offset, values, width=width, color=color, label=f"N={n}")
    axes[1, 0].axhline(0, color="#4F5E63", lw=0.8)
    axes[1, 0].set_xticks(x, labels)
    axes[1, 0].set_title("同一主剖面：r=0.2−r=0.1中心间隔差")
    axes[1, 0].set_ylabel("中心间隔变化（带符号）")
    axes[1, 0].grid(alpha=0.2, axis="y")
    axes[1, 0].legend(frameon=False)
    combined = data["combined_with_batches_a_b"]["by_strength"]
    series = []
    for strength_index, strength in enumerate((0.05, 0.1, 0.2)):
        for method_index, method in enumerate(("linear_point", "cell_average")):
            series.append((strength, method, strength_index * 2.5 + method_index * 0.85, combined[str(strength)]["assignment_counts"][method]))
    for strength, method, position, counts in series:
        diagonal = counts.get("diagonal", 0)
        swapped = counts.get("swapped", 0)
        tie = counts.get("tie_exact", 0)
        axes[1, 1].bar([position], [diagonal], color="#356A64", width=0.72)
        axes[1, 1].bar([position], [swapped], bottom=[diagonal], color="#A25B3F", width=0.72)
        axes[1, 1].bar([position], [tie], bottom=[diagonal + swapped], color="#B8C0C4", width=0.72)
        axes[1, 1].text(position, diagonal / 2 if diagonal else 0, str(diagonal), ha="center", va="center", color="white", fontsize=8)
        if swapped:
            axes[1, 1].text(position, diagonal + swapped / 2, str(swapped), ha="center", va="center", color="white", fontsize=8)
    axes[1, 1].set_xticks([row[2] for row in series], [f"{strength:g}\n{'LP' if method == 'linear_point' else 'CA'}" for strength, method, _position, _counts in series])
    axes[1, 1].set_ylim(0, 26)
    axes[1, 1].set_ylabel("网格数（每系列24）")
    axes[1, 1].set_title("A+B+C：三种强度的分配计数")
    axes[1, 1].grid(alpha=0.2, axis="y")
    fig.subplots_adjust(top=0.89, bottom=0.15, left=0.08, right=0.98, hspace=0.52, wspace=0.25)
    fig.suptitle("共同无序剖面第三批高强度配对与三批联合审计", fontsize=16, y=0.97)
    fig.savefig(ROOT / "matched-beta-batch-c.png", bbox_inches="tight")
    plt.close(fig)


def count_text(counts):
    return f"同谱秩 {counts.get('diagonal', 0)}、交换 {counts.get('swapped', 0)}、平局 {counts.get('tie_exact', 0)}"


def markdown(data):
    summary = data["summary"]
    pair_summary = data["high_strength_summary"]
    combined = data["combined_with_batches_a_b"]
    lines = [
        "# Floquet-BdG 共同无序剖面第三批高强度配对",
        "",
        f"> 协议登记与报告复核：{REPORT_DATE}。既有8个主剖面统一新增 r=0.2，共8个新实现、16个尺寸单元，与既有 r=0.1 结果配对。不新增类别，不补算体 winding，未计算 N=640。",
        "",
        "## 一、协议与谱结构",
        "",
        "每个粗格点的 β 值等于其覆盖主格点的算术平均，因此 N=400 和 N=600 通过嵌套块平均共享同一无序结构。r=0.2 与 r=0.1 使用完全相同的主剖面，是配对控制而非独立样本。",
        "",
        "此前结果只读不重算。所有预登记实现、网格和分配方向均保留，不筛选有利案例，也不根据本批结果选择下一强度。跨尺寸重叠不归一化。",
        "",
        "| seed | r | N | 最近对中心 | 次近对中心 | 中心间隔 |",
        "|---:|---:|---:|---:|---:|---:|",
    ]
    for row in data["realizations"]:
        for cell in row["cells"]:
            lines.append(f"| {row['seed']} | 0.2 | {cell['n']} | {fmt(cell['pairs'][0]['center'])} | {fmt(cell['pairs'][1]['center'])} | {fmt(cell['center_separation'])} |")
    lines += [
        "",
        "## 二、三种网格与两种表示",
        "",
        "D 表示同谱秩主导，S 表示交换主导；三格顺序均为 M=1200／2400／4800。下表只是描述性计数，不是统计显著性检验。",
        "",
        "| seed | 线性点值 D/S | 单元平均 D/S | M=4800线性同谱秩 | M=4800线性交换 | M=4800单元同谱秩 | M=4800单元交换 |",
        "|---:|:---:|:---:|---:|---:|---:|---:|",
    ]
    for row in data["realizations"]:
        linear = row["methods"]["linear_point"]["grids"][-1]
        average = row["methods"]["cell_average"]["grids"][-1]
        lines.append(f"| {row['seed']} | {pattern_text(row, 'linear_point')} | {pattern_text(row, 'cell_average')} | {fmt(linear['diagonal_score'])} | {fmt(linear['swapped_score'])} | {fmt(average['diagonal_score'])} | {fmt(average['swapped_score'])} |")
    lines += [
        "",
        f"第三批两种表示各自均有24个网格结果。线性点值：{count_text(summary['assignment_counts']['linear_point'])}；单元平均：{count_text(summary['assignment_counts']['cell_average'])}。",
        "",
        "图 1 插入位置：全网格分配表之后、高强度配对与联合审计之前。",
        "",
        "![图 1：共同无序剖面第三批高强度配对](matched-beta-batch-c.png)",
        "",
        "**图 1**　r=0.2分配得分与方向、相对r=0.1的中心间隔变化，以及三种强度的联合分配计数。",
        "",
        "## 三、同主剖面的高强度配对",
        "",
        "| seed | N=400中心间隔差（0.2−0.1） | N=600中心间隔差（0.2−0.1） | 线性方向改变网格数 | 单元方向改变网格数 |",
        "|---:|---:|---:|---:|---:|",
    ]
    for row in data["strength_pair_comparisons"]:
        changes = {method: sum(item["from"] != item["to"] for item in row["assignment_transitions"][method]) for method in ("linear_point", "cell_average")}
        lines.append(f"| {row['seed']} | {fmt(row['n400_center_separation_delta'])} | {fmt(row['n600_center_separation_delta'])} | {changes['linear_point']} | {changes['cell_average']} |")
    lines += [
        "",
        f"N=400中心间隔变化范围为 {fmt(pair_summary['n400_center_separation_delta_range'][0])} 至 {fmt(pair_summary['n400_center_separation_delta_range'][1])}；N=600为 {fmt(pair_summary['n600_center_separation_delta_range'][0])} 至 {fmt(pair_summary['n600_center_separation_delta_range'][1])}。",
        "",
        f"线性点值同谱秩得分比范围为 {fmt(pair_summary['assignment_transition_counts']['linear_point']['diagonal_score_ratio_range'][0])}–{fmt(pair_summary['assignment_transition_counts']['linear_point']['diagonal_score_ratio_range'][1])}，单元平均为 {fmt(pair_summary['assignment_transition_counts']['cell_average']['diagonal_score_ratio_range'][0])}–{fmt(pair_summary['assignment_transition_counts']['cell_average']['diagonal_score_ratio_range'][1])}。比值只描述同一配对的数值变化，不归一化重叠。",
        "",
        "## 四、A+B+C联合描述性审计与边界",
        "",
        f"三批共有 {combined['realization_count']} 个互不重复的“种子—强度”键和 {combined['control_cells']} 个尺寸单元。联合线性点值：{count_text(combined['assignment_counts']['linear_point'])}；联合单元平均：{count_text(combined['assignment_counts']['cell_average'])}。每种表示均为72个网格结果，既有复用锚点在联合证据中仍只计一次。",
        "",
        f"联合跨表示自一致性范围为 {fmt(combined['min_representation_fidelity'])}–{fmt(combined['max_representation_fidelity'])}；联合中心间隔尺寸差范围为 {fmt(combined['center_separation_delta_range'][0])} 至 {fmt(combined['center_separation_delta_range'][1])}。第三批线性点值秩间重叠最大为 {fmt(summary['max_linear_point_off_diagonal'])}，嵌入诱导串扰仍单独保留。",
        "",
        "联合结果只描述当前指定的共同无序剖面，不能外推为普遍尺寸律、普遍强度律、真实态交换或谱交叉。旧交换候选仍属于不同无序实现，不能与联合结果直接相减并命名为尺寸效应。",
        "",
        "本批闭合的是 r=0.2 的预登记配对和三批联合描述性覆盖，不构成统计显著性、连续路径、次近对拓扑性或热力学极限结论。后续应围绕机制问题设计检验，而不是仅凭有利方向继续增加强度。",
        "",
        "复现：`python research/floquet-bdg-tbc/analyze_matched_beta_batch_c.py`。完整主剖面、配对、重叠矩阵、跨表示与秩间控制保存在 `matched_beta_batch_c_analysis.json`。",
        "",
    ]
    (ROOT / "MATCHED_BETA_BATCH_C.md").write_text("\n".join(lines), encoding="utf-8")


def check_only():
    stored = json.loads((ROOT / "matched_beta_batch_c_analysis.json").read_text(encoding="utf-8"))
    if stored.get("protocol_sha256") != sha(PROTOCOL) or stored.get("batch_a_analysis_sha256") != sha(BATCH_A) or stored.get("batch_b_analysis_sha256") != sha(BATCH_B):
        raise ValueError("Batch-C evidence is stale")
    if len(stored.get("realizations", [])) != 8 or stored.get("new_control_cells") != 16 or stored.get("reused_anchor_realizations_in_new_batch") != 0:
        raise ValueError("Batch-C realization evidence is incomplete")
    if any(cell["coarsening_max_absolute_error"] != 0 for row in stored["realizations"] for cell in row["cells"]):
        raise ValueError("Batch-C nested coarsening failed")
    if stored["combined_with_batches_a_b"]["realization_count"] != 24 or not stored.get("all_preregistered_results_retained"):
        raise ValueError("Batch-C combined coverage or retention changed")
    print(json.dumps({"check_only": True, "new_realizations": 8, "new_control_cells": 16, "combined_realizations": 24, "all_passed": True}, ensure_ascii=False))
    return 0


def main():
    if "--check-only" in sys.argv:
        return check_only()
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    realizations = []
    for seed in protocol["seed_values"]:
        master = np.random.default_rng(20261111 + seed).random(protocol["master_grid"])
        row = evaluate_realization(seed, protocol["new_strength"], master, protocol)
        row["evidence_role"] = "new_batch_c"
        row["recomputed_for_new_analysis"] = True
        realizations.append(row)
    batch_a = json.loads(BATCH_A.read_text(encoding="utf-8"))
    batch_b = json.loads(BATCH_B.read_text(encoding="utf-8"))
    comparisons = compare_high_strengths(realizations, batch_a["realizations"] + batch_b["realizations"])
    batch_c = {"realizations": realizations, "summary": summarize(realizations)}
    data = {
        "schema": "floquet-bdg-matched-beta-batch-c-analysis-v1",
        "analysis_date": protocol["analysis_date"], "report_date": REPORT_DATE, "batch": "C",
        "protocol_sha256": sha(PROTOCOL), "batch_a_analysis_sha256": sha(BATCH_A),
        "batch_b_analysis_sha256": sha(BATCH_B), "candidate_source_sha256": sha(CANDIDATE),
        "realizations": realizations, "summary": batch_c["summary"],
        "strength_pair_comparisons": comparisons,
        "high_strength_summary": summarize_strength_pairs(comparisons),
        "combined_with_batches_a_b": combined_summary(batch_a, batch_b, batch_c),
        "max_coarsening_absolute_error": 0.0,
        "new_realization_count": 8, "new_control_cells": 16,
        "reused_anchor_realizations_in_new_batch": 0,
        "prior_results_recomputed_for_pairing": False,
        "new_seed_count": 0, "new_winding_computed": False, "n640_computed": False,
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
    (ROOT / "matched_beta_batch_c_analysis.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    figure(data)
    markdown(data)
    print(json.dumps({"summary": data["summary"], "high_strength_summary": data["high_strength_summary"], "combined_with_batches_a_b": data["combined_with_batches_a_b"], "new_control_cells": 16, "n640_computed": False}, ensure_ascii=False, indent=2))
    print("generated matched_beta_batch_c_analysis.json matched-beta-batch-c.png MATCHED_BETA_BATCH_C.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
