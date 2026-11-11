"""Entry-resolved overlap-matrix and singular-channel response decomposition."""

import copy
import hashlib
import json
import math
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
from analyze_matched_beta_batch_a import fmt, sha  # noqa: E402

PROTOCOL = ROOT / "overlap_matrix_response_protocol.json"
SOURCES = {name: ROOT / f"matched_beta_batch_{name}_analysis.json" for name in ("a", "b", "c")}
INDEPENDENT_SOURCES = {name: ROOT / f"matched_beta_batch_{name}_independent.json" for name in ("a", "b", "c")}
CANDIDATE = ROOT / "swap_candidate_spectrum_analysis.json"
REPORT_DATE = "2026-11-12"
ENTRIES = ((0, 0), (0, 1), (1, 0), (1, 1))
plt.rcParams.update({
    "font.sans-serif": ["Microsoft YaHei", "SimHei", "Noto Sans CJK SC", "DejaVu Sans"],
    "axes.unicode_minus": False, "font.size": 9, "figure.dpi": 160,
})


def ratio(after, before):
    if before == 0:
        return None
    return after / before


def sign(value):
    return 1 if value > 0 else -1 if value < 0 else 0


def load_sources():
    data = {name: json.loads(path.read_text(encoding="utf-8")) for name, path in SOURCES.items()}
    rows = data["a"]["realizations"] + data["b"]["realizations"] + data["c"]["realizations"]
    return data, {(row["seed"], row["strength"]): row for row in rows}


def build_transitions(protocol, by_key):
    method_grid_transitions = []
    entry_transitions = []
    for seed in protocol["seed_values"]:
        before_row = by_key[(seed, protocol["from_strength"])]
        after_row = by_key[(seed, protocol["to_strength"])]
        for method in protocol["methods"]:
            for grid_index, m in enumerate(protocol["common_grids"]):
                before_grid = before_row["methods"][method]["grids"][grid_index]
                after_grid = after_row["methods"][method]["grids"][grid_index]
                before, after = before_grid["overlap_matrix"], after_grid["overlap_matrix"]
                entries_for_grid = {}
                for i, j in ENTRIES:
                    old, new = before[i][j], after[i][j]
                    delta = new["overlap"] - old["overlap"]
                    channels = []
                    for k in range(2):
                        delta_s_squared = new["singular_values"][k] ** 2 - old["singular_values"][k] ** 2
                        channels.append({
                            "channel_index": k, "before_s": old["singular_values"][k], "after_s": new["singular_values"][k],
                            "delta_s_squared": delta_s_squared, "score_contribution": delta_s_squared / 2,
                        })
                    value_ratio = ratio(new["overlap"], old["overlap"])
                    entry = {
                        "seed": seed, "from_strength": protocol["from_strength"], "to_strength": protocol["to_strength"],
                        "method": method, "m": m, "i": i, "j": j, "entry": f"O{i}{j}",
                        "before": copy.deepcopy(old), "after": copy.deepcopy(new),
                        "delta_overlap": delta, "ratio": value_ratio,
                        "log2_ratio": math.log2(value_ratio) if value_ratio is not None and value_ratio > 0 else None,
                        "score_group": "diagonal" if i == j else "swapped",
                        "score_contribution": delta / 2,
                        "singular_channels": channels,
                        "dominant_singular_channel_index": max((0, 1), key=lambda k: abs(channels[k]["score_contribution"])),
                    }
                    entry_transitions.append(entry)
                    entries_for_grid[(i, j)] = entry
                delta_diagonal = after_grid["diagonal_score"] - before_grid["diagonal_score"]
                delta_swapped = after_grid["swapped_score"] - before_grid["swapped_score"]
                diagonal_driver = max(((0, 0), (1, 1)), key=lambda ij: abs(entries_for_grid[ij]["score_contribution"]))
                swapped_driver = max(((0, 1), (1, 0)), key=lambda ij: abs(entries_for_grid[ij]["score_contribution"]))
                method_grid_transitions.append({
                    "seed": seed, "from_strength": protocol["from_strength"], "to_strength": protocol["to_strength"],
                    "method": method, "m": m,
                    "before_dominant_assignment": before_grid["dominant_assignment"],
                    "after_dominant_assignment": after_grid["dominant_assignment"],
                    "delta_diagonal_score": delta_diagonal, "delta_swapped_score": delta_swapped,
                    "diagonal_score_ratio": ratio(after_grid["diagonal_score"], before_grid["diagonal_score"]),
                    "swapped_score_ratio": ratio(after_grid["swapped_score"], before_grid["swapped_score"]),
                    "dominant_diagonal_entry": f"O{diagonal_driver[0]}{diagonal_driver[1]}",
                    "dominant_diagonal_entry_contribution": entries_for_grid[diagonal_driver]["score_contribution"],
                    "dominant_swapped_entry": f"O{swapped_driver[0]}{swapped_driver[1]}",
                    "dominant_swapped_entry_contribution": entries_for_grid[swapped_driver]["score_contribution"],
                })
    return method_grid_transitions, entry_transitions


def build_entry_summary(entry_transitions, method_grid_transitions):
    summaries = []
    for method in ("linear_point", "cell_average"):
        for m in (1200, 2400, 4800):
            for i, j in ENTRIES:
                entry_name = f"O{i}{j}"
                rows = [row for row in entry_transitions if row["method"] == method and row["m"] == m and row["entry"] == entry_name]
                ratios = [row["ratio"] for row in rows if row["ratio"] is not None]
                log2_ratios = [row["log2_ratio"] for row in rows if row["log2_ratio"] is not None]
                group = rows[0]["score_group"]
                summaries.append({
                    "method": method, "m": m, "entry": entry_name, "score_group": group,
                    "delta_sign_counts": {
                        "positive": sum(row["delta_overlap"] > 0 for row in rows),
                        "negative": sum(row["delta_overlap"] < 0 for row in rows),
                        "zero_exact": sum(row["delta_overlap"] == 0 for row in rows),
                    },
                    "ratio_range": [min(ratios), max(ratios)] if ratios else [None, None],
                    "log2_ratio_range": [min(log2_ratios), max(log2_ratios)] if log2_ratios else [None, None],
                    "before_overlap_range": [min(row["before"]["overlap"] for row in rows), max(row["before"]["overlap"] for row in rows)],
                    "after_overlap_range": [min(row["after"]["overlap"] for row in rows), max(row["after"]["overlap"] for row in rows)],
                    "mean_delta_overlap": float(np.mean([row["delta_overlap"] for row in rows])),
                    "driver_count_in_score_group": sum(row[f"dominant_{group}_entry"] == entry_name for row in method_grid_transitions if row["method"] == method and row["m"] == m),
                    "dominant_singular_channel_counts": dict(Counter(row["dominant_singular_channel_index"] for row in rows)),
                })
    return summaries


def build_representation_agreements(entry_transitions):
    agreements = []
    for seed in range(8):
        for m in (1200, 2400, 4800):
            for i, j in ENTRIES:
                entry_name = f"O{i}{j}"
                lp = next(row for row in entry_transitions if row["seed"] == seed and row["m"] == m and row["entry"] == entry_name and row["method"] == "linear_point")
                ca = next(row for row in entry_transitions if row["seed"] == seed and row["m"] == m and row["entry"] == entry_name and row["method"] == "cell_average")
                lp_sign, ca_sign = sign(lp["delta_overlap"]), sign(ca["delta_overlap"])
                agreements.append({
                    "seed": seed, "m": m, "entry": entry_name,
                    "linear_point_sign": lp_sign, "cell_average_sign": ca_sign,
                    "agreement": lp_sign == ca_sign,
                })
    return agreements


def summarize(method_grid_transitions, entry_transitions, agreements, batch_c):
    disagreements = [row for row in agreements if not row["agreement"]]
    return {
        "method_grid_assignment_change_count": sum(row["before_dominant_assignment"] != row["after_dominant_assignment"] for row in method_grid_transitions),
        "representation_sign_agreement_count": sum(row["agreement"] for row in agreements),
        "representation_sign_disagreement_count": len(disagreements),
        "representation_sign_disagreements": disagreements,
        "entry_ratio_range_by_method": {
            method: [
                min(row["ratio"] for row in entry_transitions if row["method"] == method and row["ratio"] is not None),
                max(row["ratio"] for row in entry_transitions if row["method"] == method and row["ratio"] is not None),
            ]
            for method in ("linear_point", "cell_average")
        },
        "high_strength_controls": {
            "representation_fidelity_range": [batch_c["summary"]["min_representation_fidelity"], batch_c["summary"]["max_representation_fidelity"]],
            "max_native_off_diagonal": batch_c["summary"]["max_native_off_diagonal"],
            "max_linear_point_off_diagonal": batch_c["summary"]["max_linear_point_off_diagonal"],
            "max_cell_average_off_diagonal": batch_c["summary"]["max_cell_average_off_diagonal"],
        },
    }


def figure(data):
    entries = [f"O{i}{j}" for i, j in ENTRIES]
    fig, axes = plt.subplots(2, 2, figsize=(14, 9.8))
    for method, color, marker, method_offset in (("linear_point", "#356A64", "o", -0.035), ("cell_average", "#A25B3F", "s", 0.035)):
        for entry_index, entry in enumerate(entries):
            rows = [row for row in data["entry_transitions"] if row["method"] == method and row["m"] == 4800 and row["entry"] == entry]
            for row in rows:
                jitter = (row["seed"] - 3.5) * 0.065
                axes[0, 0].scatter(entry_index + jitter + method_offset, row["log2_ratio"], color=color, marker=marker, s=27, alpha=0.82)
    axes[0, 0].axhline(0, color="#4F5E63", lw=0.8)
    axes[0, 0].set_xticks(range(4), entries)
    axes[0, 0].set_ylabel(r"$\log_2\,[O_{ij}(0.2)/O_{ij}(0.1)]$")
    axes[0, 0].set_title("M=4800：矩阵项比值的逐种子分布")
    axes[0, 0].grid(alpha=0.2)
    axes[0, 0].text(0.02, 0.03, "圆点：线性点值；方块：单元平均", transform=axes[0, 0].transAxes, fontsize=8, color="#4F5E63")
    summary_lookup = {(row["method"], row["m"], row["entry"]): row for row in data["entry_summary"]}
    sign_matrix = np.zeros((4, 6))
    columns = [(method, m) for method in ("linear_point", "cell_average") for m in (1200, 2400, 4800)]
    for i, entry in enumerate(entries):
        for j, (method, m) in enumerate(columns):
            counts = summary_lookup[(method, m, entry)]["delta_sign_counts"]
            sign_matrix[i, j] = 1 if counts["negative"] == 0 and counts["positive"] > 0 else -1 if counts["positive"] == 0 and counts["negative"] > 0 else 0
    axes[0, 1].imshow(sign_matrix, cmap=ListedColormap(["#A25B3F", "#D7DCDD", "#356A64"]), vmin=-1, vmax=1, aspect="auto")
    for i, entry in enumerate(entries):
        for j, (method, m) in enumerate(columns):
            counts = summary_lookup[(method, m, entry)]["delta_sign_counts"]
            text = f"{counts['positive']}+／{counts['negative']}−"
            axes[0, 1].text(j, i, text, ha="center", va="center", color="white" if sign_matrix[i, j] else "black", fontsize=8)
    axes[0, 1].set_xticks(range(6), ["LP\n1200", "LP\n2400", "LP\n4800", "CA\n1200", "CA\n2400", "CA\n4800"])
    axes[0, 1].set_yticks(range(4), entries)
    axes[0, 1].set_title("ΔOij 符号计数：8个种子")
    groups = [("diagonal", ((0, 0), (1, 1))), ("swapped", ((0, 1), (1, 0)))]
    positions = [0, 1, 2.5, 3.5]
    for (group, pair_entries), (method, position) in zip([group for group in groups for _method in ("linear_point", "cell_average")], [("linear_point", 0), ("cell_average", 1), ("linear_point", 2.5), ("cell_average", 3.5)]):
        rows = [row for row in data["method_grid_transitions"] if row["method"] == method and row["m"] == 4800]
        entry_names = [f"O{i}{j}" for i, j in pair_entries]
        counts = [sum(row[f"dominant_{group}_entry"] == entry for row in rows) for entry in entry_names]
        bottom = 0
        for entry, count, color in zip(entry_names, counts, ("#356A64", "#A25B3F")):
            axes[1, 0].bar([position], [count], bottom=bottom, color=color, width=0.72)
            if count:
                axes[1, 0].text(position, bottom + count / 2, f"{entry}\n{count}", ha="center", va="center", color="white", fontsize=8)
            bottom += count
    axes[1, 0].set_xticks(positions, ["对角\nLP", "对角\nCA", "交换\nLP", "交换\nCA"])
    axes[1, 0].set_ylim(0, 8.8)
    axes[1, 0].set_ylabel("成为最大绝对贡献项的种子数")
    axes[1, 0].set_title("M=4800：得分变化的主导矩阵项")
    axes[1, 0].grid(alpha=0.2, axis="y")
    positions = np.arange(8)
    for index, (entry, method) in enumerate((entry, method) for entry in entries for method in ("linear_point", "cell_average")):
        rows = [row for row in data["entry_transitions"] if row["method"] == method and row["m"] == 4800 and row["entry"] == entry]
        counts = Counter(row["dominant_singular_channel_index"] for row in rows)
        axes[1, 1].bar([index], [counts.get(0, 0)], color="#356A64", width=0.72, label="第一通道" if index == 0 else None)
        axes[1, 1].bar([index], [counts.get(1, 0)], bottom=[counts.get(0, 0)], color="#B08B57", width=0.72, label="第二通道" if index == 0 else None)
        axes[1, 1].text(index, counts.get(0, 0) / 2 if counts.get(0, 0) else 0, str(counts.get(0, 0)), ha="center", va="center", color="white", fontsize=8)
        if counts.get(1, 0):
            axes[1, 1].text(index, counts.get(0, 0) + counts.get(1, 0) / 2, str(counts.get(1, 0)), ha="center", va="center", color="white", fontsize=8)
    axes[1, 1].set_xticks(positions, [f"{entry}\n{'LP' if method == 'linear_point' else 'CA'}" for entry in entries for method in ("linear_point", "cell_average")])
    axes[1, 1].set_ylim(0, 8.8)
    axes[1, 1].set_ylabel("主导通道种子数")
    axes[1, 1].set_title("M=4800：第一／第二主奇异值通道")
    axes[1, 1].grid(alpha=0.2, axis="y")
    axes[1, 1].legend(frameon=False, fontsize=8)
    fig.subplots_adjust(top=0.89, bottom=0.15, left=0.08, right=0.98, hspace=0.52, wspace=0.25)
    fig.suptitle("重叠矩阵响应：矩阵项与主奇异值通道分解", fontsize=16, y=0.97)
    fig.savefig(ROOT / "overlap-matrix-response.png", bbox_inches="tight")
    plt.close(fig)


def ratio_range_text(row):
    return f"{fmt(row['ratio_range'][0])}–{fmt(row['ratio_range'][1])}"


def sign_text(row):
    counts = row["delta_sign_counts"]
    return f"{counts['positive']}+／{counts['negative']}−"


def channel_text(row):
    counts = row["dominant_singular_channel_counts"]
    return f"s₁:{counts.get('0', counts.get(0, 0))}／s₂:{counts.get('1', counts.get(1, 0))}"


def markdown(data):
    summary = data["summary"]
    controls = summary["high_strength_controls"]
    lines = [
        "# Floquet-BdG 重叠矩阵响应分解",
        "",
        f"> 日期：{REPORT_DATE}。r=0.1→0.2 的8组配对、48个方法—网格配对、192个矩阵项配对、384个主奇异值通道配对。只读取既有证据，不新增 Floquet 单元，不补算体 winding，未计算 N=640。",
        "",
        "## 一、完整2×2矩阵与差分定义",
        "",
        "每个矩阵项保留 Oᵢⱼ=(s₁²+s₂²)/2。ΔOᵢⱼ 是 r=0.2 减去 r=0.1；对角与交换得分变化分别是 (ΔO₀₀+ΔO₁₁)/2 和 (ΔO₀₁+ΔO₁₀)/2。主奇异通道贡献为 Δ(sₖ²)/2。",
        "",
        "所有预登记结果保留，不筛选有利案例。比值和 log₂ 比值只在分母为正时计算；不归一化重叠，不把跨表示自一致性作为校正因子。所谓“主导项”仅指最大绝对数值贡献，不是因果机制证明。",
        "",
        "极大比值可能来自近零分母，必须同时查看 before_overlap_range、after_overlap_range、ΔOᵢⱼ 和原始主奇异值，不能把放大倍数直接当成同等大小的物理效应。",
        "",
        "## 二、M=4800 的矩阵项响应",
        "",
        "| 矩阵项 | LP比值范围 | LP Δ符号 | LP主导通道 | CA比值范围 | CA Δ符号 | CA主导通道 |",
        "|:---:|---:|:---:|:---:|---:|:---:|:---:|",
    ]
    for entry in ("O00", "O01", "O10", "O11"):
        lp = next(row for row in data["entry_summary"] if row["method"] == "linear_point" and row["m"] == 4800 and row["entry"] == entry)
        ca = next(row for row in data["entry_summary"] if row["method"] == "cell_average" and row["m"] == 4800 and row["entry"] == entry)
        lines.append(f"| {entry} | {ratio_range_text(lp)} | {sign_text(lp)} | {channel_text(lp)} | {ratio_range_text(ca)} | {sign_text(ca)} | {channel_text(ca)} |")
    lines += [
        "",
        "图 1 插入位置：矩阵项表之后、跨表示控制与边界之前。",
        "",
        "![图 1：重叠矩阵与主奇异值响应分解](overlap-matrix-response.png)",
        "",
        "**图 1**　矩阵项 log₂ 比值、三种网格的差分符号、主导矩阵项和主奇异通道。所有计数均来自8个同主剖面配对。",
        "",
        "## 三、得分变化的主导项与跨表示一致性",
        "",
        "| 得分组 | 方法 | 主导项计数（8个种子） | 得分比范围 |",
        "|:---|:---|:---|---:|",
    ]
    for group, entries in (("diagonal", ("O00", "O11")), ("swapped", ("O01", "O10"))):
        for method in ("linear_point", "cell_average"):
            rows = [row for row in data["method_grid_transitions"] if row["method"] == method and row["m"] == 4800]
            counts = {entry: sum(row[f"dominant_{group}_entry"] == entry for row in rows) for entry in entries}
            ratios = [row[f"{group}_score_ratio"] for row in rows if row[f"{group}_score_ratio"] is not None]
            lines.append(f"| {group} | {method} | {counts} | {fmt(min(ratios))}–{fmt(max(ratios))} |")
    lines += [
        "",
        f"96个跨表示差分符号比较中，一致 {summary['representation_sign_agreement_count']} 个，不一致 {summary['representation_sign_disagreement_count']} 个。该一致性检查不证明表示不变性，也不把两种表示合并为校正后的重叠。",
        "",
        f"r=0.2 的跨表示自一致性范围为 {fmt(controls['representation_fidelity_range'][0])}–{fmt(controls['representation_fidelity_range'][1])}；线性点值秩间重叠最大 {fmt(controls['max_linear_point_off_diagonal'])}，单元平均最大 {fmt(controls['max_cell_average_off_diagonal'])}，原生最大 {fmt(controls['max_native_off_diagonal'])}。这些控制与矩阵项分解分开记录。",
        "",
        "## 四、结论与边界",
        "",
        "矩阵项分解可以定位同谱秩得分上升和交换得分比分化的具体数值来源，同时保留不同种子、不同网格和不同表示之间的差异。它不能外推为普遍尺寸律、真实态交换、谱交叉或统计显著性，也不能把最大贡献项直接命名为物理机制。",
        "",
        "旧交换候选仍属于不同无序实现，不能与本次配对差分直接相减。后续若提出机制解释，应继续检查相同矩阵项在固定尺寸连续路径上的演化，而不是仅依据横断面的比值命名过程。",
        "",
        "复现：`python research/floquet-bdg-tbc/analyze_overlap_matrix_response.py`。完整矩阵项、差分、比值、主奇异通道、跨表示符号比较和来源哈希保存在 `overlap_matrix_response_analysis.json`。",
        "",
    ]
    (ROOT / "OVERLAP_MATRIX_RESPONSE.md").write_text("\n".join(lines), encoding="utf-8")


def check_only():
    stored = json.loads((ROOT / "overlap_matrix_response_analysis.json").read_text(encoding="utf-8"))
    if stored.get("protocol_sha256") != sha(PROTOCOL) or any(stored.get(f"batch_{name}_analysis_sha256") != sha(path) for name, path in SOURCES.items()):
        raise ValueError("Overlap-matrix response evidence is stale")
    if len(stored.get("method_grid_transitions", [])) != 48 or len(stored.get("entry_transitions", [])) != 192:
        raise ValueError("Overlap-matrix response transitions are incomplete")
    if len(stored.get("representation_delta_agreements", [])) != 96 or not stored.get("all_preregistered_results_retained"):
        raise ValueError("Overlap-matrix representation comparisons are incomplete")
    print(json.dumps({"check_only": True, "method_grid_transitions": 48, "entry_transitions": 192, "singular_channels": 384, "new_floquet_cells": 0, "all_passed": True}, ensure_ascii=False))
    return 0


def main():
    if "--check-only" in sys.argv:
        return check_only()
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    batches, by_key = load_sources()
    method_grid_transitions, entry_transitions = build_transitions(protocol, by_key)
    agreements = build_representation_agreements(entry_transitions)
    summary = summarize(method_grid_transitions, entry_transitions, agreements, batches["c"])
    independent_all_passed = all(json.loads(path.read_text(encoding="utf-8")).get("all_passed") for path in INDEPENDENT_SOURCES.values())
    data = {
        "schema": "floquet-bdg-overlap-matrix-response-analysis-v1",
        "analysis_date": protocol["analysis_date"], "report_date": REPORT_DATE,
        "protocol_sha256": sha(PROTOCOL),
        **{f"batch_{name}_analysis_sha256": sha(path) for name, path in SOURCES.items()},
        **{f"batch_{name}_independent_sha256": sha(path) for name, path in INDEPENDENT_SOURCES.items()},
        "candidate_source_sha256": sha(CANDIDATE),
        "source_independent_rechecks_all_passed": independent_all_passed,
        "method_grid_transitions": method_grid_transitions,
        "entry_transitions": entry_transitions,
        "entry_summary": build_entry_summary(entry_transitions, method_grid_transitions),
        "representation_delta_agreements": agreements,
        "summary": summary,
        "high_strength_controls": summary["high_strength_controls"],
        "new_floquet_cells_computed": 0, "new_seed_count": 0,
        "new_winding_computed": False, "n640_computed": False,
        "all_preregistered_results_retained": True,
        "normalization_correction_applied": False, "representation_invariant_claim": False,
        "causal_mechanism_proven": False, "statistical_significance_claim": False,
        "universal_size_law_claim": False, "continuous_path_proof": False,
        "spectral_crossing_proven": False, "avoided_crossing_claim": False,
        "state_exchange_proven": False, "second_pair_topological_claim": False,
        "thermodynamic_limit_proof": False, "new_taxonomy_claim": False,
        "old_candidate_is_different_realization": True,
        "difference_from_original_is_not_size_effect": True,
        "categories_changed": False,
    }
    (ROOT / "overlap_matrix_response_analysis.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    figure(data)
    markdown(data)
    print(json.dumps({"summary": summary, "method_grid_transitions": 48, "entry_transitions": 192, "singular_channel_transitions": 384, "new_floquet_cells": 0}, ensure_ascii=False, indent=2))
    print("generated overlap_matrix_response_analysis.json overlap-matrix-response.png OVERLAP_MATRIX_RESPONSE.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
