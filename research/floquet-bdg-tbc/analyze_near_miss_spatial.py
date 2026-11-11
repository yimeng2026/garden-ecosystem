"""Resolve two near misses and one reference using only frozen pair profiles."""

import hashlib
import json
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent
PROTOCOL = ROOT / "near_miss_spatial_protocol.json"
SOURCE = ROOT / "repeated_category_analysis.json"
UNCLASSIFIED = ROOT / "unclassified_signature_analysis.json"
OLD_INDEPENDENT = ROOT / "multi_seed_independent.json"
NEW_INDEPENDENT = ROOT / "category_new_cells_independent.json"
WINDOWS = ("left_outer40", "left_inner40", "central40", "right_inner40", "right_outer40")
DELTA_METRICS = WINDOWS + (
    "edge40", "signed_asymmetry40", "left10pct", "right10pct", "edge10pct",
    "asymmetry10pct", "L50", "max_separation_ratio",
)
LABELS = {
    "near_miss_low": "近 miss：seed=5，r=0.05",
    "near_miss_high": "近 miss：seed=5，r=0.1",
    "reference_weakening": "参考：seed=2，r=0.1",
}
WINDOW_LABELS = {
    "left_outer40": "左外40", "left_inner40": "左内40", "central40": "中央40",
    "right_inner40": "右内40", "right_outer40": "右外40",
}
plt.rcParams.update({
    "font.sans-serif": ["Microsoft YaHei", "SimHei", "Noto Sans CJK SC", "DejaVu Sans"],
    "axes.unicode_minus": False, "font.size": 10, "figure.dpi": 160,
})


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def cell(source, n, strength, seed):
    return next(row for row in source["all_cells"] if (row["n"], row["strength"], row["seed"]) == (n, strength, seed))


def spatial_metrics(pair, n):
    profile = pair["profile"]
    values = {
        "left_outer40": math.fsum(profile[:40]),
        "left_inner40": math.fsum(profile[40:80]),
        "central40": math.fsum(profile[n // 2 - 20:n // 2 + 20]),
        "right_inner40": math.fsum(profile[n - 80:n - 40]),
        "right_outer40": math.fsum(profile[n - 40:]),
    }
    edge40 = values["left_outer40"] + values["right_outer40"]
    edge_sites = pair["edge_sites_per_end"]
    left10 = math.fsum(profile[:edge_sites])
    right10 = math.fsum(profile[-edge_sites:])
    edge10 = left10 + right10
    asymmetry10 = abs(left10 - right10) / edge10
    errors = [
        abs(left10 - pair["left_edge_weight"]), abs(right10 - pair["right_edge_weight"]),
        abs(edge10 - pair["edge_weight"]), abs(asymmetry10 * edge10 - abs(left10 - right10)),
    ]
    return {
        "pair_index": pair["pair_index"], "profile_sha256": pair["profile_sha256"],
        "windows": values, "edge40": edge40,
        "signed_asymmetry40": (values["right_outer40"] - values["left_outer40"]) / edge40,
        "edge_sites_per_end": edge_sites, "left10pct": left10, "right10pct": right10,
        "edge10pct": edge10, "asymmetry10pct": asymmetry10,
        "L50": pair["L50"], "L90": pair["L90"],
        "max_separation_ratio": pair["max_separation_ratio"],
        "diagnostic_joint_pass": pair["diagnostic_joint_pass"],
        "original_metric_recompute_error": max(errors),
    }


def get_delta(data, label, pair_index):
    return next(row for row in data["size_deltas"] if row["label"] == label and row["pair_index"] == pair_index)


def fmt(value):
    return f"{value:.5g}"


def figure(data):
    fig, axes = plt.subplots(3, 2, figsize=(13, 11.2), constrained_layout=False)
    x = np.arange(len(WINDOWS))
    width = 0.36
    for row_index, case in enumerate(data["cases"]):
        label = case["label"]
        for pair_index in (0, 1):
            axis = axes[row_index, pair_index]
            first = next(row for row in data["records"] if row["label"] == label and row["n"] == 400 and row["pair_index"] == pair_index)
            second = next(row for row in data["records"] if row["label"] == label and row["n"] == 600 and row["pair_index"] == pair_index)
            for offset, n, color in ((-width / 2, 400, "#8A9BA8"), (width / 2, 600, "#356A64")):
                record = first if n == 400 else second
                axis.bar(x + offset, [record["windows"][name] for name in WINDOWS], width, color=color, label=f"N={n}")
            delta = get_delta(data, label, pair_index)
            for index, name in enumerate(WINDOWS):
                axis.annotate(f"Δ{delta[name]:+.3g}", (index, max(first["windows"][name], second["windows"][name])), ha="center", va="bottom", fontsize=7, rotation=90)
            axis.set_xticks(x)
            axis.set_xticklabels([WINDOW_LABELS[name] for name in WINDOWS])
            axis.set_title(f"{LABELS[label]}｜第 {pair_index + 1} 对\nΔedge40={delta['edge40']:+.4g}，ΔsignedA40={delta['signed_asymmetry40']:+.4g}，ΔL50={delta['L50']:+d}")
            axis.set_ylabel("固定40窗口内 profile 质量")
            axis.grid(axis="y", alpha=0.2)
            axis.legend(frameon=False, fontsize=8)
            axis.margins(y=0.24)
    fig.subplots_adjust(top=0.9, bottom=0.08, left=0.07, right=0.985, hspace=0.65, wspace=0.2)
    fig.suptitle("近 miss 的固定40窗口与次近对：柱上 Δ 为 N=600 − N=400", fontsize=16, y=0.975)
    fig.savefig(ROOT / "near-miss-spatial.png", bbox_inches="tight")
    plt.close(fig)


def delta_table(data, pair_index):
    lines = [
        "| 对照 | Δ左外10% | Δ左内40 | Δ中央40 | Δ右内40 | Δ右外10% | Δedge10% | ΔA10% | ΔL50 |",
        "|:---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for case in data["cases"]:
        row = get_delta(data, case["label"], pair_index)
        lines.append(f"| {case['seed']}／{case['strength']} | {fmt(row['left10pct'])} | {fmt(row['left_inner40'])} | {fmt(row['central40'])} | {fmt(row['right_inner40'])} | {fmt(row['right10pct'])} | {fmt(row['edge10pct'])} | {fmt(row['asymmetry10pct'])} | {row['L50']:+d} |")
    return lines


def markdown(data):
    low = get_delta(data, "near_miss_low", 0)
    high = get_delta(data, "near_miss_high", 0)
    reference = get_delta(data, "reference_weakening", 0)
    second_l50 = [get_delta(data, case["label"], 1)["L50"] for case in data["cases"]]
    lines = [
        "# Floquet-BdG 近 miss 空间分布与次近对诊断",
        "",
        "> 日期：2026-11-11。只使用已冻结且经过独立复核的 N=400／600 剖面；两个近 miss 与一个参考对照，最近对和次近对各 6 条记录。不新增种子、不新增类别、不补算体 winding，未计算 N=640。",
        "",
        "## 一、两套窗口严格分开",
        "",
        "原类别使用既有每端10%窗口：N=400 为40格，N=600 为60格；A10%=|右外10%−左外10%|/edge10%。这些量用于逐项复现冻结比较，不能换成别的窗口。",
        "",
        "补充空间诊断为固定40窗口：左外40=[0,40)、左内40=[40,80)、中央40=[N/2−20,N/2+20)、右内40=[N−80,N−40)、右外40=[N−40,N)。signedA40=(右外40−左外40)/edge40，与原类别的绝对不对称度不同。",
        "",
        "初稿曾把固定40误作原10%端点，交叉校验据此失败；现已在接受结果前纠正。固定40用于观察空间细节，不回溯修改类别或阈值。所有尺寸差均为 N=600 减 N=400，固定 seed、强度和 pair_index。",
        "",
        "## 二、最近对：近 miss 的左右端来源",
        "",
        *delta_table(data, 0),
        "",
        f"seed=5、r=0.05：Δ左外10%={fmt(low['left10pct'])}，Δ右外10%={fmt(low['right10pct'])}，所以 Δedge10%={fmt(low['edge10pct'])} 仍为正。左端增量超过右端减量，直接解释了为何右端减弱却没有总端点减弱。",
        "",
        f"seed=5、r=0.1：Δ左外10%={fmt(high['left10pct'])}，Δ右外10%={fmt(high['right10pct'])}，Δedge10%={fmt(high['edge10pct'])}。总端点虽下降，左外质量却增加，ΔA10%={fmt(high['asymmetry10pct'])}；这就是‘右端减弱但更对称’的空间含义。",
        "",
        f"参考 seed=2、r=0.1 的 Δ左外10%={fmt(reference['left10pct'])}、Δ右外10%={fmt(reference['right10pct'])}、ΔA10%={fmt(reference['asymmetry10pct'])}。它同样左增右减，但绝对不对称度上升，与高强度近 miss 不同。",
        "",
        f"窗口定义敏感性也可量化：低强度近 miss 的固定 Δedge40={fmt(low['edge40'])}，与原 Δedge10%={fmt(low['edge10pct'])} 符号不同，因为 N=600 的原端点包含第40至59格而固定40不包含。二者各自真实，但不能混用或借此改类。",
        "",
        "图 1 插入位置：最近对空间分解之后、次近对表格之前。",
        "",
        "![图 1：近 miss 固定窗口与次近对](near-miss-spatial.png)",
        "",
        "**图 1**　左列是最近对，右列是次近对；柱上 Δ 为 N=600−N=400。图中只画固定40窗口及 signedA40，原10%类别指标见表，避免两种定义混淆。",
        "",
        "## 三、次近对：平行的描述性对照",
        "",
        *delta_table(data, 1),
        "",
        f"三例次近对的 ΔL50 分别为 {second_l50[0]:+d}、{second_l50[1]:+d}、{second_l50[2]:+d}，均与最近对的尾长变化分开记录。次近对的端部符号并不与最近对一一同步，因此不能假定最近对的变化会自动传给全部近零谱子空间。",
        "",
        "次近对与最近对不相加来挽救某个类别，也不根据次近对重新命名最近对。谱隔离比一并保留；有限谱排序不构成体不变量证明。",
        "",
        "## 四、结论与边界",
        "",
        "两个近 miss 的原10%端点分解都显示左外质量增加：低强度时它抵消并超过右端减量，高强度时它与右端减量共同降低总外端质量、同时降低绝对不对称度。由此，未复现不能简单归结为‘右端没有减弱’，也不能归结为‘端点消失’。",
        "",
        "本轮只说明这三个对照、两种尺寸和既有剖面中的空间关系。没有计算新本征对，没有统计总体，没有改变原类别或阈值，也没有证明因果机制、体 winding、材料实现或热力学极限。",
        "",
        "复现：`python research/floquet-bdg-tbc/analyze_near_miss_spatial.py`。固定协议、逐窗口值、原10%指标、尺寸差、原类别和来源哈希保存在 `near_miss_spatial_analysis.json`。",
        "",
    ]
    (ROOT / "NEAR_MISS_SPATIAL.md").write_text("\n".join(lines), encoding="utf-8")


def main():
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    unclassified = json.loads(UNCLASSIFIED.read_text(encoding="utf-8"))
    if not json.loads(OLD_INDEPENDENT.read_text(encoding="utf-8")).get("all_passed"):
        raise ValueError("Original independent profile verification has not passed")
    if not json.loads(NEW_INDEPENDENT.read_text(encoding="utf-8")).get("all_passed"):
        raise ValueError("New-cell independent profile verification has not passed")
    if source["category_counts"] != unclassified["original_category_counts"]:
        raise ValueError("Original category counts differ between frozen sources")
    records, cases = [], []
    for selected in protocol["selected_cases"]:
        label, seed, strength = selected["label"], selected["seed"], selected["strength"]
        original = next(row for row in source["cases"] if (row["seed"], row["strength"]) == (seed, strength))
        cases.append({"label": label, "seed": seed, "strength": strength, "original_category": original["category"]})
        for n in protocol["n_values"]:
            source_case = cell(source, n, strength, seed)
            for pair_index in protocol["pair_indices"]:
                metrics = spatial_metrics(source_case["pairs"][pair_index], n)
                records.append({"label": label, "seed": seed, "strength": strength, "n": n, **metrics})
    deltas = []
    for case in cases:
        for pair_index in protocol["pair_indices"]:
            first = next(row for row in records if row["label"] == case["label"] and row["n"] == 400 and row["pair_index"] == pair_index)
            second = next(row for row in records if row["label"] == case["label"] and row["n"] == 600 and row["pair_index"] == pair_index)
            row = {"label": case["label"], "pair_index": pair_index}
            for name in DELTA_METRICS:
                first_value = first["windows"][name] if name in WINDOWS else first[name]
                second_value = second["windows"][name] if name in WINDOWS else second[name]
                row[name] = second_value - first_value
            if pair_index == 0:
                original = next(item for item in source["cases"] if (item["seed"], item["strength"]) == (case["seed"], case["strength"]))["comparison"]
                expected = {
                    "left10pct": original["left_delta"], "right10pct": original["right_delta"],
                    "edge10pct": original["edge_delta"], "asymmetry10pct": original["asymmetry_delta"],
                    "L50": original["delta_L50"],
                }
                if any(abs(row[name] - value) > 1e-12 for name, value in expected.items()):
                    raise ValueError(f"Original endpoint definition mismatch: {case['label']}")
            deltas.append(row)
    data = {
        "schema": "floquet-bdg-near-miss-spatial-analysis-v1",
        "analysis_date": protocol["analysis_date"],
        "protocol_sha256": sha(PROTOCOL), "source_sha256": sha(SOURCE),
        "unclassified_source_sha256": sha(UNCLASSIFIED),
        "original_independent_source_sha256": sha(OLD_INDEPENDENT),
        "new_independent_source_sha256": sha(NEW_INDEPENDENT),
        "window_definitions": protocol["window_definitions"],
        "original_endpoint_definitions": protocol["original_endpoint_definitions"],
        "new_seed_count": 0, "new_eigenpairs_computed": False,
        "new_winding_computed": False, "n640_computed": False,
        "new_taxonomy_claim": False, "categories_changed": False,
        "second_pair_topological_claim": False, "universal_mechanism_claim": False,
        "original_category_counts": source["category_counts"],
        "cases": cases, "records": records, "size_deltas": deltas,
        "max_original_metric_recompute_error": max(row["original_metric_recompute_error"] for row in records),
    }
    (ROOT / "near_miss_spatial_analysis.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    figure(data)
    markdown(data)
    print(json.dumps({"cases": cases, "size_deltas": deltas, "max_original_metric_recompute_error": data["max_original_metric_recompute_error"], "new_seed_count": 0, "new_eigenpairs_computed": False, "n640_computed": False}, ensure_ascii=False, indent=2))
    print("generated near_miss_spatial_analysis.json near-miss-spatial.png NEAR_MISS_SPATIAL.md")


if __name__ == "__main__":
    main()
