"""Audit rank-matched first/second-pair size responses across all frozen contrasts."""

import hashlib
import json
import math
from collections import Counter
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent
PROTOCOL = ROOT / "pair_response_protocol.json"
SOURCE = ROOT / "repeated_category_analysis.json"
NEAR_MISS = ROOT / "near_miss_spatial_analysis.json"
OLD_INDEPENDENT = ROOT / "multi_seed_independent.json"
NEW_INDEPENDENT = ROOT / "category_new_cells_independent.json"
plt.rcParams.update({
    "font.sans-serif": ["Microsoft YaHei", "SimHei", "Noto Sans CJK SC", "DejaVu Sans"],
    "axes.unicode_minus": False, "font.size": 10, "figure.dpi": 160,
})


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sign(value):
    return (value > 0) - (value < 0)


def record(pair, n, strength, seed):
    profile = pair["profile"]
    width = pair["edge_sites_per_end"]
    left = math.fsum(profile[:width])
    right = math.fsum(profile[-width:])
    edge = left + right
    asymmetry = abs(left - right) / edge
    error = max(abs(left - pair["left_edge_weight"]), abs(right - pair["right_edge_weight"]), abs(edge - pair["edge_weight"]))
    return {
        "n": n, "strength": strength, "seed": seed, "pair_index": pair["pair_index"],
        "profile_sha256": pair["profile_sha256"], "left": left, "right": right, "edge": edge,
        "asymmetry": asymmetry, "L50": pair["L50"],
        "max_separation_ratio": pair["max_separation_ratio"],
        "diagnostic_joint_pass": pair["diagnostic_joint_pass"],
        "original_metric_recompute_error": error,
    }


def get_response(data, seed, strength, pair_index):
    return next(row for row in data["responses"] if (row["seed"], row["strength"], row["pair_index"]) == (seed, strength, pair_index))


def relation_counts(responses, key):
    counts = Counter()
    for strength in (0.05, 0.1):
        for seed in range(8):
            first = next(row for row in responses if (row["seed"], row["strength"], row["pair_index"]) == (seed, strength, 0))
            second = next(row for row in responses if (row["seed"], row["strength"], row["pair_index"]) == (seed, strength, 1))
            product = sign(first[key]) * sign(second[key])
            counts["same_nonzero" if product > 0 else "opposite_nonzero" if product < 0 else "at_least_one_zero"] += 1
    return dict(counts)


def crosstab(responses, key):
    table = {str(first): {str(second): 0 for second in (-1, 0, 1)} for first in (-1, 0, 1)}
    for strength in (0.05, 0.1):
        for seed in range(8):
            first = next(row for row in responses if (row["seed"], row["strength"], row["pair_index"]) == (seed, strength, 0))
            second = next(row for row in responses if (row["seed"], row["strength"], row["pair_index"]) == (seed, strength, 1))
            table[str(sign(first[key]))][str(sign(second[key]))] += 1
    return table


def relation(first, second, key):
    product = sign(first[key]) * sign(second[key])
    return "同号" if product > 0 else "反号" if product < 0 else "含零"


def fmt(value):
    return f"{value:.5g}"


def heatmap_text_color(value, maximum):
    """Keep counts legible on the green sequential heatmap."""
    return "#FFFFFF" if maximum > 0 and value > maximum * 0.6 else "#203B35"


def figure(data):
    fig, axes = plt.subplots(2, 2, figsize=(13, 9.6), constrained_layout=False)
    for case in data["cases"]:
        first = get_response(data, case["seed"], case["strength"], 0)
        second = get_response(data, case["seed"], case["strength"], 1)
        color = "#356A64" if case["strength"] == 0.05 else "#A25B3F"
        axes[0, 0].scatter(first["edge_delta"], second["edge_delta"], s=50, color=color)
        axes[0, 0].annotate(f"s{case['seed']},r{case['strength']}", (first["edge_delta"], second["edge_delta"]), xytext=(4, 4), textcoords="offset points", fontsize=7)
        axes[0, 1].scatter(first["L50_delta"], second["L50_delta"], s=50, color=color)
        axes[0, 1].annotate(f"s{case['seed']}", (first["L50_delta"], second["L50_delta"]), xytext=(4, 4), textcoords="offset points", fontsize=7)
    for axis, xlabel, ylabel, title in (
        (axes[0, 0], "最近对 Δedge", "次近对 Δedge", "端点响应并不同步"),
        (axes[0, 1], "最近对 ΔL50", "次近对 ΔL50", "尾长响应的符号关系"),
    ):
        axis.axhline(0, color="#777777", lw=0.8, ls="--")
        axis.axvline(0, color="#777777", lw=0.8, ls="--")
        axis.set_xlabel(xlabel)
        axis.set_ylabel(ylabel)
        axis.set_title(title)
        axis.grid(alpha=0.2)
    for axis, metric, title in ((axes[1, 0], "edge", "Δedge 符号列联"), (axes[1, 1], "L50", "ΔL50 符号列联")):
        table = data[f"{metric}_sign_crosstab"]
        matrix = np.asarray([[table[str(first)][str(second)] for second in (-1, 0, 1)] for first in (-1, 0, 1)])
        image = axis.imshow(matrix, cmap="Greens", vmin=0, vmax=max(1, int(matrix.max())))
        for i in range(3):
            for j in range(3):
                axis.text(j, i, str(matrix[i, j]), ha="center", va="center", fontsize=15, color=heatmap_text_color(matrix[i, j], matrix.max()))
        axis.set_xticks(range(3), ["−", "0", "+"])
        axis.set_yticks(range(3), ["−", "0", "+"])
        axis.set_xlabel("次近对差的符号")
        axis.set_ylabel("最近对差的符号")
        axis.set_title(title)
        fig.colorbar(image, ax=axis, shrink=0.8)
    fig.subplots_adjust(top=0.88, bottom=0.1, left=0.08, right=0.96, hspace=0.42, wspace=0.35)
    fig.suptitle("全部16个尺寸对照：最近对与次近对的谱排序匹配审计", fontsize=16, y=0.97)
    fig.savefig(ROOT / "pair-response-audit.png", bbox_inches="tight")
    plt.close(fig)


def sign_table(table):
    lines = ["| 最近对＼次近对 | − | 0 | + |", "|:---:|---:|---:|---:|"]
    for first in ("-1", "0", "1"):
        label = {"-1": "−", "0": "0", "1": "+"}[first]
        lines.append(f"| {label} | {table[first]['-1']} | {table[first]['0']} | {table[first]['1']} |")
    return lines


def markdown(data):
    edge = data["edge_relation_counts"]
    tail = data["L50_relation_counts"]
    lines = [
        "# Floquet-BdG 最近对与次近对尺寸响应审计",
        "",
        "> 日期：2026-11-11。全部8个既有种子、2个强度、16个 N=400→600 对照，最近对与次近对分别审计。只使用冻结剖面，不新增类别、不补算体 winding，未计算 N=640。",
        "",
        "## 一、配对和指标定义",
        "",
        "pair_index 只是在每个尺寸内按 |λ−1| 排序后的谱秩。相同 pair_index 不代表跨尺寸追踪到同一个物理态，本审计因此是谱排序匹配，不是绝热态追踪。",
        "",
        "端点沿用原定义：每端 N/10 格，edge=L+R，A=|R−L|/edge；尺寸差均为 N=600−N=400。符号列联使用精确符号，不增加数值阈值，不作统计显著性推断。",
        "",
        "## 二、逐对照响应",
        "",
        "| seed | r | 最近对Δedge | 次近对Δedge | edge符号关系 | 最近对ΔL50 | 次近对ΔL50 | L50符号关系 |",
        "|---:|---:|---:|---:|:---:|---:|---:|:---:|",
    ]
    for case in data["cases"]:
        first = get_response(data, case["seed"], case["strength"], 0)
        second = get_response(data, case["seed"], case["strength"], 1)
        lines.append(f"| {case['seed']} | {case['strength']} | {fmt(first['edge_delta'])} | {fmt(second['edge_delta'])} | {relation(first, second, 'edge_delta')} | {first['L50_delta']:+d} | {second['L50_delta']:+d} | {relation(first, second, 'L50_delta')} |")
    lines += [
        "",
        "图 1 插入位置：逐对照响应表之后、符号列联统计之前。",
        "",
        "![图 1：最近对与次近对响应审计](pair-response-audit.png)",
        "",
        "**图 1**　上排为逐案例散点，下排为精确符号列联。不同谱秩分别展示，不把两对质量相加。",
        "",
        "## 三、符号列联与关系计数",
        "",
        "### Δedge",
        "",
        *sign_table(data["edge_sign_crosstab"]),
        "",
        "### ΔL50",
        "",
        *sign_table(data["L50_sign_crosstab"]),
        "",
        f"Δedge：同号且非零 {edge.get('same_nonzero', 0)} 例，反号且非零 {edge.get('opposite_nonzero', 0)} 例，至少一个零 {edge.get('at_least_one_zero', 0)} 例。",
        "",
        f"ΔL50：同号且非零 {tail.get('same_nonzero', 0)} 例，反号且非零 {tail.get('opposite_nonzero', 0)} 例，至少一个零 {tail.get('at_least_one_zero', 0)} 例。",
        "",
        f"次近对在两种尺寸均满足既有 profile 联合诊断的对照数为 {data['second_pair_joint_pass_contrasts']}/16。该计数只描述原有判据，不把次近对提升为拓扑端点。",
        "",
        "这些计数直接检验‘最近对变化会自动传给次近对’这一直觉是否成立；它们不是相关系数、显著性检验或因果证明。",
        "",
        "## 四、结论与未竟问题",
        "",
        f"实测端点响应有 {edge.get('opposite_nonzero', 0)}/16 反号、{edge.get('same_nonzero', 0)}/16 同号，因此在这组有限样本中，最近对端点变化不能预设为次近对同向变化。尾长则有 {tail.get('same_nonzero', 0)}/16 同号、{tail.get('opposite_nonzero', 0)}/16 反号，端点与尾长呈现不同的符号结构。",
        "",
        "最近对与次近对必须分开记录。即使某些对照同号，也不能把谱秩匹配解释为同一态的连续变化；反号或含零则更不能被平均掉。次近对联合 profile 判据通过数为0，不构成端点消失或拓扑否证。原类别及其计数完全保留。",
        "",
        "下一步若要把‘响应’升级为态机制，需要在不同尺寸间建立可复核的子空间对应，例如基于投影重叠的匹配，并检查排序交换与简并；当前数据只支持谱秩层面的描述。",
        "",
        "本轮没有计算新本征对、新种子或 N=640，没有证明体 winding、材料实现、统计规律或热力学极限。",
        "",
        "复现：`python research/floquet-bdg-tbc/analyze_pair_responses.py`。64条原始记录、32条尺寸响应、符号列联和来源哈希保存在 `pair_response_analysis.json`。",
        "",
    ]
    (ROOT / "PAIR_RESPONSE_AUDIT.md").write_text("\n".join(lines), encoding="utf-8")


def main():
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    near_miss = json.loads(NEAR_MISS.read_text(encoding="utf-8"))
    if not json.loads(OLD_INDEPENDENT.read_text(encoding="utf-8")).get("all_passed"):
        raise ValueError("Original independent profile verification has not passed")
    if not json.loads(NEW_INDEPENDENT.read_text(encoding="utf-8")).get("all_passed"):
        raise ValueError("New-cell independent profile verification has not passed")
    records = []
    for strength in protocol["strengths"]:
        for seed in protocol["seeds"]:
            for n in protocol["n_values"]:
                case = next(row for row in source["all_cells"] if (row["n"], row["strength"], row["seed"]) == (n, strength, seed))
                for pair_index in protocol["pair_indices"]:
                    records.append(record(case["pairs"][pair_index], n, strength, seed))
    responses = []
    for old in source["cases"]:
        seed, strength = old["seed"], old["strength"]
        for pair_index in protocol["pair_indices"]:
            first = next(row for row in records if (row["n"], row["strength"], row["seed"], row["pair_index"]) == (400, strength, seed, pair_index))
            second = next(row for row in records if (row["n"], row["strength"], row["seed"], row["pair_index"]) == (600, strength, seed, pair_index))
            response = {
                "seed": seed, "strength": strength, "pair_index": pair_index,
                "original_category": old["category"],
                "left_delta": second["left"] - first["left"], "right_delta": second["right"] - first["right"],
                "edge_delta": second["edge"] - first["edge"], "asymmetry_delta": second["asymmetry"] - first["asymmetry"],
                "L50_delta": second["L50"] - first["L50"],
                "max_separation_ratio_delta": second["max_separation_ratio"] - first["max_separation_ratio"],
                "both_sizes_joint_pass": bool(first["diagnostic_joint_pass"] and second["diagnostic_joint_pass"]),
            }
            if pair_index == 0:
                comparison = old["comparison"]
                expected = {
                    "left_delta": comparison["left_delta"], "right_delta": comparison["right_delta"],
                    "edge_delta": comparison["edge_delta"], "asymmetry_delta": comparison["asymmetry_delta"],
                    "L50_delta": comparison["delta_L50"],
                }
                if any(abs(response[name] - value) > 1e-12 for name, value in expected.items()):
                    raise ValueError(f"Frozen first-pair comparison mismatch: seed={seed}, r={strength}")
            responses.append(response)
    cases = [{"seed": row["seed"], "strength": row["strength"], "original_category": row["category"]} for row in source["cases"]]
    data = {
        "schema": "floquet-bdg-pair-response-analysis-v1",
        "analysis_date": protocol["analysis_date"],
        "protocol_sha256": sha(PROTOCOL), "source_sha256": sha(SOURCE), "near_miss_source_sha256": sha(NEAR_MISS),
        "original_independent_source_sha256": sha(OLD_INDEPENDENT), "new_independent_source_sha256": sha(NEW_INDEPENDENT),
        "pair_identity": protocol["pair_identity"], "new_seed_count": 0,
        "new_eigenpairs_computed": False, "new_winding_computed": False, "n640_computed": False,
        "new_taxonomy_claim": False, "categories_changed": False, "second_pair_topological_claim": False,
        "statistical_significance_claim": False, "universal_mechanism_claim": False,
        "original_category_counts": source["category_counts"], "cases": cases,
        "records": records, "responses": responses,
        "edge_sign_crosstab": crosstab(responses, "edge_delta"),
        "L50_sign_crosstab": crosstab(responses, "L50_delta"),
        "edge_relation_counts": relation_counts(responses, "edge_delta"),
        "L50_relation_counts": relation_counts(responses, "L50_delta"),
        "second_pair_joint_pass_contrasts": sum(row["pair_index"] == 1 and row["both_sizes_joint_pass"] for row in responses),
        "max_original_metric_recompute_error": max(row["original_metric_recompute_error"] for row in records),
    }
    for old in near_miss["cases"]:
        previous = next(row for row in near_miss["size_deltas"] if row["label"] == old["label"] and row["pair_index"] == 1)
        current = get_response(data, old["seed"], old["strength"], 1)
        if abs(current["edge_delta"] - previous["edge10pct"]) > 1e-12 or current["L50_delta"] != previous["L50"]:
            raise ValueError("Previous near-miss second-pair evidence is not reproduced")
    (ROOT / "pair_response_analysis.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    figure(data)
    markdown(data)
    print(json.dumps({key: value for key, value in data.items() if key not in ("records", "responses", "cases")}, ensure_ascii=False, indent=2))
    print("generated pair_response_analysis.json pair-response-audit.png PAIR_RESPONSE_AUDIT.md")


if __name__ == "__main__":
    main()
