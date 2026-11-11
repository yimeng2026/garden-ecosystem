"""Audit why unclassified and near-miss contrasts do not match the reference signature."""

import hashlib
import json
from collections import Counter
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "repeated_category_analysis.json"
INDEPENDENT = ROOT / "category_new_cells_independent.json"
ORIGINAL_INDEPENDENT = ROOT / "multi_seed_independent.json"
SIGNATURES = [
    "positive_edge_tail_shorter_or_asymmetry_up",
    "mixed_nonmatching_sign_combinations",
    "right_weakening_with_symmetrization",
]
COLORS = {
    "positive_edge_tail_shorter_or_asymmetry_up": "#6F7F92",
    "mixed_nonmatching_sign_combinations": "#999999",
    "right_weakening_with_symmetrization": "#356A64",
}
plt.rcParams.update({
    "font.sans-serif": ["Microsoft YaHei", "SimHei", "Noto Sans CJK SC", "DejaVu Sans"],
    "axes.unicode_minus": False, "font.size": 10, "figure.dpi": 160,
})


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def signature(comparison):
    if comparison["edge_delta"] > 0 and comparison["delta_L50"] < 0 and comparison["asymmetry_delta"] > 0:
        return SIGNATURES[0]
    if comparison["right_delta"] < 0 and comparison["edge_delta"] < 0 and comparison["delta_L50"] > 0 and comparison["asymmetry_delta"] < 0:
        return SIGNATURES[2]
    return SIGNATURES[1]


def blocking_conditions(comparison):
    conditions = []
    if comparison["right_delta"] >= 0:
        conditions.append("right_delta_not_negative")
    if comparison["edge_delta"] >= 0:
        conditions.append("edge_delta_not_negative")
    if comparison["delta_L50"] <= 0:
        conditions.append("L50_not_positive")
    if comparison["asymmetry_delta"] <= 0:
        conditions.append("asymmetry_delta_not_positive")
    return conditions


def figure(data):
    fig, axes = plt.subplots(2, 2, figsize=(12.5, 8.5), constrained_layout=False)
    for row in data["unclassified_cases"]:
        comparison = row["comparison"]
        signature_name = row["signature"]
        axes[0, 0].scatter(comparison["right_delta"], comparison["asymmetry_delta"], s=55, color=COLORS[signature_name], marker="o" if comparison["edge_delta"] > 0 else "x")
        axes[0, 0].annotate(f"s{row['seed']},r{row['strength']}", (comparison["right_delta"], comparison["asymmetry_delta"]), textcoords="offset points", xytext=(4, 4), fontsize=8)
    axes[0, 0].axhline(0, color="#777777", lw=0.8, ls="--")
    axes[0, 0].axvline(0, color="#777777", lw=0.8, ls="--")
    axes[0, 0].set_title("未归类的七种符号组合（圆圈总端点为正，叉为负）")
    axes[0, 0].set_xlabel("右端权重差")
    axes[0, 0].set_ylabel("不对称度差")
    axes[0, 0].grid(alpha=0.2)

    near = [case for case in data["cases"] if (case["seed"], case["strength"]) in ((5, 0.05), (5, 0.1), (2, 0.1))]
    names = [f"s{case['seed']},r{case['strength']}" for case in near]
    x = np.arange(3)
    width = 0.25
    for index, metric in enumerate(("right_delta", "edge_delta", "asymmetry_delta")):
        axes[0, 1].bar(x + (index - 1) * width, [case["comparison"][metric] for case in near], width, label=metric)
    axes[0, 1].set_xticks(x)
    axes[0, 1].set_xticklabels(names)
    axes[0, 1].axhline(0, color="#777777", lw=0.8, ls="--")
    axes[0, 1].set_title("近 miss 与参考 seed=2 的条件差异")
    axes[0, 1].legend(frameon=False, fontsize=8)
    axes[0, 1].grid(axis="y", alpha=0.2)

    counts = data["signature_counts"]
    axes[1, 0].bar(["正向—尾短", "混合组合", "右弱—对称"], [counts[name] for name in SIGNATURES], color=[COLORS[name] for name in SIGNATURES], width=0.55)
    axes[1, 0].set_title("未归类的三种描述性组合")
    axes[1, 0].set_ylabel("对照数")
    axes[1, 0].tick_params(axis="x", labelsize=8)
    axes[1, 0].grid(axis="y", alpha=0.2)

    axes[1, 1].bar(names, [case["comparison"]["delta_L50"] for case in near], color=["#6F7F92", "#356A64", "#A25B3F"], width=0.5)
    axes[1, 1].set_title("近 miss 与参考的 L50 均增加，但其他条件不同")
    axes[1, 1].set_ylabel("ΔL50")
    axes[1, 1].grid(axis="y", alpha=0.2)
    fig.subplots_adjust(top=0.88, bottom=0.13, left=0.08, right=0.98, hspace=0.45, wspace=0.32)
    fig.suptitle("未归类不是单一机制：逐条件审计，不新增类别", fontsize=16, y=0.975)
    fig.savefig(ROOT / "unclassified-signatures.png", bbox_inches="tight")
    plt.close(fig)


def fmt(value):
    return f"{value:.5g}"


def markdown(data):
    lines = [
        "# Floquet-BdG 未归类与未复现诊断",
        "",
        "> 日期：2026-11-11。仅审计已有 8 种子、16 个对照的符号条件，不新增类别，不追加种子，不补算体 winding，未计算 N=640。",
        "",
        "## 一、未归类不是单一机制",
        "",
        "三个描述性组合仅用于解释现有条件，不构成新分类学：两个端点增加但尾部缩短或不对称上升、四个混合符号组合、一个右端减弱但更对称。",
        "",
        "| seed | r | Δ右端 | Δ总端点 | ΔL50 | Δ不对称度 | 描述性组合 | 未满足参考条件 |",
        "|---:|---:|---:|---:|---:|---:|:---|:---|",
    ]
    for row in data["unclassified_cases"]:
        comparison = row["comparison"]
        lines.append(f"| {row['seed']} | {row['strength']} | {fmt(comparison['right_delta'])} | {fmt(comparison['edge_delta'])} | {comparison['delta_L50']} | {fmt(comparison['asymmetry_delta'])} | {row['signature']} | {', '.join(row['blocking_conditions'])} |")
    lines += [
        "",
        "图 1 插入位置：未归类条件表之后、近 miss 解释之前。",
        "",
        "![图 1：未归类的符号组合与近 miss](unclassified-signatures.png)",
        "",
        "**图 1**　未归类内部存在不同结构，不能用单一机制解释，也不能通过追加阈值把它们强行归类。",
        "",
        "## 二、右端减弱为何未复现",
        "",
        "参考的右端减弱—尾部变宽要求同时满足：右端差为负、总端点差为负、L50 为正、不对称度差为正。seed=4–7 中没有单元同时满足，故复现数为 0。",
        "",
        "seed=5、r=0.05 是近 miss：右端减弱且不对称度增加，但总端点仍增加，因此缺少 `edge_delta_not_negative` 条件。",
        "",
        "seed=5、r=0.1 是另一个近 miss：右端和总端点均下降、L50 增加，但不对称度下降，形成**右端减弱但更对称**，缺少 `asymmetry_delta_not_positive` 条件。两种尺寸的联合判据仍通过，不能称端点消失。",
        "",
        "这两个近 miss 说明，未复现不是简单的‘没有右端减弱’，而是其他条件没有共同出现。它们可指导后续结构分析，但不能用来修改参考定义以制造复现。",
        "",
        "## 三、解释边界与下一步",
        "",
        "本轮是条件审计，不是新的机制命名或统计因果证明。原类别及原始计数完全保留，独立后端验证文件未改变。",
        "",
        "下一步应先检查近 miss 的左右端空间分布和次近对角色，再判断它们是否属于其他可重复结构；不要为了复现参考类别而移动阈值。",
        "",
        "复现：`python research/floquet-bdg-tbc/analyze_unclassified_signatures.py`。全部阻断条件、原始类别、签名组合和来源哈希保存在 `unclassified_signature_analysis.json`。",
        "",
    ]
    (ROOT / "UNCLASSIFIED_SIGNATURES.md").write_text("\n".join(lines), encoding="utf-8")


def main():
    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    independent = json.loads(INDEPENDENT.read_text(encoding="utf-8"))
    original_independent = json.loads(ORIGINAL_INDEPENDENT.read_text(encoding="utf-8"))
    if not independent.get("all_passed") or not original_independent.get("all_passed"):
        raise ValueError("Source independent verification has not passed")
    unclassified = []
    for row in source["cases"]:
        if row["category"] != "other_unclassified":
            continue
        comparison = row["comparison"]
        unclassified.append({
            "seed": row["seed"], "strength": row["strength"], "original_category": row["category"],
            "signature": signature(comparison), "blocking_conditions": blocking_conditions(comparison),
            "comparison": comparison,
        })
    counts = Counter(row["signature"] for row in unclassified)
    data = {
        "schema": "floquet-bdg-unclassified-signature-analysis-v1",
        "analysis_date": "2026-11-11",
        "source_sha256": sha(SOURCE),
        "new_independent_source_sha256": sha(INDEPENDENT),
        "original_independent_source_sha256": sha(ORIGINAL_INDEPENDENT),
        "analysis_role": "condition_audit_not_new_taxonomy",
        "new_seed_count": 0,
        "new_winding_computed": False,
        "n640_computed": False,
        "new_taxonomy_claim": False,
        "unclassified_not_homogeneous": len(counts) > 1,
        "original_category_counts": source["category_counts"],
        "reference_weakening_new_seed_recurrences": source["new_seed_category_counts"]["right_end_weakening_with_broadening"],
        "cases": source["cases"],
        "unclassified_cases": unclassified,
        "signature_counts": {name: counts.get(name, 0) for name in SIGNATURES},
    }
    (ROOT / "unclassified_signature_analysis.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    figure(data)
    markdown(data)
    print(json.dumps({key: value for key, value in data.items() if key not in ("cases", "unclassified_cases")}, ensure_ascii=False, indent=2))
    print("generated unclassified_signature_analysis.json unclassified-signatures.png UNCLASSIFIED_SIGNATURES.md")


if __name__ == "__main__":
    main()
