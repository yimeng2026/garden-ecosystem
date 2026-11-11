"""Apply the frozen descriptive category rules to all seed=0..7 contrasts."""

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
from analyze_reversal_units import recompute  # noqa: E402

PROTOCOL = ROOT / "repeated_category_protocol.json"
OLD = ROOT / "multi_seed_profile_control.json"
NEW = ROOT / "category_new_cells.json"
REVERSAL = ROOT / "reversal_unit_analysis.json"
INDEPENDENT = ROOT / "category_new_cells_independent.json"
CATEGORY_ORDER = json.loads(PROTOCOL.read_text(encoding="utf-8"))["category_order"]
COLORS = {
    "tail_growth_without_endpoint_recovery": "#8B3A3A",
    "right_end_weakening_with_broadening": "#A25B3F",
    "right_end_driven_symmetrization": "#356A64",
    "left_end_driven_threshold": "#6F7F92",
    "other_unclassified": "#999999",
}
plt.rcParams.update({
    "font.sans-serif": ["Microsoft YaHei", "SimHei", "Noto Sans CJK SC", "DejaVu Sans"],
    "axes.unicode_minus": False, "font.size": 10, "figure.dpi": 160,
})


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def comparison(n400, n600):
    first400, first600 = n400["pairs"][0], n600["pairs"][0]
    calc400, calc600 = recompute(first400, 400), recompute(first600, 600)
    left_delta = calc600["left_edge_weight"] - calc400["left_edge_weight"]
    right_delta = calc600["right_edge_weight"] - calc400["right_edge_weight"]
    asymmetry_delta = calc600["asymmetry"] - calc400["asymmetry"]
    edge_delta = first600["edge_weight"] - first400["edge_weight"]
    delta_l50 = first600["L50"] - first400["L50"]
    both_pass = bool(first400["diagnostic_joint_pass"] and first600["diagnostic_joint_pass"])
    if edge_delta < 0 and delta_l50 > 0 and not both_pass:
        category = "tail_growth_without_endpoint_recovery"
    elif right_delta < 0 and edge_delta < 0 and delta_l50 > 0 and asymmetry_delta > 0:
        category = "right_end_weakening_with_broadening"
    elif left_delta > 0 and right_delta > left_delta and asymmetry_delta < 0:
        category = "right_end_driven_symmetrization"
    elif left_delta > right_delta and edge_delta > 0 and delta_l50 > 0 and asymmetry_delta < 0:
        category = "left_end_driven_threshold"
    else:
        category = "other_unclassified"
    result = {
        "n400_first": {key: value for key, value in first400.items() if key != "profile"},
        "n600_first": {key: value for key, value in first600.items() if key != "profile"},
        "n400_second": {key: value for key, value in n400["pairs"][1].items() if key != "profile"},
        "n600_second": {key: value for key, value in n600["pairs"][1].items() if key != "profile"},
        "n400_asymmetry": calc400["asymmetry"], "n600_asymmetry": calc600["asymmetry"],
        "asymmetry_delta": asymmetry_delta,
        "left_delta": left_delta, "right_delta": right_delta, "edge_delta": edge_delta,
        "delta_L50": delta_l50, "delta_L90": first600["L90"] - first400["L90"],
        "both_sizes_joint_pass": both_pass,
        "dominant_end": "right" if abs(right_delta) >= abs(left_delta) else "left",
        "profile_metrics_recomputed": True,
        "max_recompute_error": max(calc400["max_recompute_error"], calc600["max_recompute_error"]),
    }
    return category, result


def figure(data):
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.5), constrained_layout=False)
    bottom = np.zeros(2)
    for category in CATEGORY_ORDER:
        values = [data["by_strength"][str(strength)][category] for strength in (0.05, 0.1)]
        axes[0].bar(["r=0.05", "r=0.1"], values, bottom=bottom, label=category, color=COLORS[category], width=0.55)
        bottom += np.asarray(values)
    axes[0].set_title("八种子的描述性类别计数")
    axes[0].set_ylabel("对照数")
    axes[0].set_ylim(0, 8.8)
    axes[0].legend(frameon=False, fontsize=8, loc="upper left", bbox_to_anchor=(0, -0.12), ncol=1)
    for row in data["cases"]:
        comparison = row["comparison"]
        category = row["category"]
        axes[1].scatter(comparison["right_delta"], comparison["asymmetry_delta"], s=52, color=COLORS[category], alpha=0.9)
        axes[1].annotate(f"s{row['seed']},r{row['strength']}", (comparison["right_delta"], comparison["asymmetry_delta"]), textcoords="offset points", xytext=(4, 4), fontsize=8)
    axes[1].axhline(0, color="#777777", lw=0.8, ls="--")
    axes[1].axvline(0, color="#777777", lw=0.8, ls="--")
    axes[1].set_xlabel("右端权重差（N=600 − N=400）")
    axes[1].set_ylabel("不对称度差")
    axes[1].set_title("类别只描述结构，不替代因果证明")
    axes[1].grid(alpha=0.2)
    fig.subplots_adjust(top=0.82, bottom=0.3, left=0.08, right=0.98, wspace=0.26)
    fig.suptitle("类别可重复性：参考结构在新种子中是否出现", fontsize=16, y=0.97)
    fig.savefig(ROOT / "repeated-categories.png", bbox_inches="tight")
    plt.close(fig)


def fmt(value):
    return f"{value:.5g}"


def markdown(data):
    lines = [
        "# Floquet-BdG 端部机制类别可重复性检验",
        "",
        "> 日期：2026-11-11。既有 seed=0–3 与新增预登记 seed=4–7，共 8 个种子、16 个 N=400→600 对照。不追加阈值，不补算体 winding，未计算 N=640。",
        "",
        "## 一、类别计数",
        "",
        "| 类别 | r=0.05 | r=0.1 | 合计 |",
        "|:---|---:|---:|---:|",
    ]
    for category in CATEGORY_ORDER:
        low, high = data["by_strength"]["0.05"][category], data["by_strength"]["0.1"][category]
        lines.append(f"| {category} | {low} | {high} | {low + high} |")
    lines += [
        "",
        "未归类（`other_unclassified`）单元不会被强行命名。参考类别在新种子中出现，只能称为可重复候选，不能据此宣称普遍机制。",
        "",
        "图 1 插入位置：类别计数之后、逐种子数据之前。",
        "",
        "![图 1：机制类别的可重复性](repeated-categories.png)",
        "",
        "**图 1**　左图为类别计数，右图为右端差与不对称度差；类别由冻结的符号条件给出。",
        "",
        "## 二、逐种子分类结果",
        "",
        "| seed | r | Δ左端 | Δ右端 | ΔL50 | Δ不对称度 | 类别 |",
        "|---:|---:|---:|---:|---:|---:|:---|",
    ]
    for row in data["cases"]:
        comparison = row["comparison"]
        lines.append(f"| {row['seed']} | {row['strength']} | {fmt(comparison['left_delta'])} | {fmt(comparison['right_delta'])} | {comparison['delta_L50']} | {fmt(comparison['asymmetry_delta'])} | {row['category']} |")
    new_counts = data["new_seed_category_counts"]
    lines += [
        "",
        "## 三、是否形成可重复类别",
        "",
        f"参考的右端驱动—对称化在 seed=4–7 中出现 {new_counts['right_end_driven_symmetrization']} 例；右端减弱—尾部变宽出现 {new_counts['right_end_weakening_with_broadening']} 例。seed=1 与 seed=2 的原始参照类别未改变。",
        "",
    ]
    if new_counts["right_end_driven_symmetrization"] + new_counts["right_end_weakening_with_broadening"] > 0:
        lines.append("新种子中出现了至少一个参考结构，因此可保留‘可重复候选’这一弱表述；但不同强度、不同种子仍不等价，不能升级为普适类别。")
    else:
        lines.append("新种子没有复现两个参考类别，因此目前不能宣称它们已经形成可重复类别。未复现也是有效结果，不用更多后验筛选掩盖。")
    lines += [
        "",
        "类别由符号条件而非拓扑相变判据定义。它们用于组织后续谱隔离和端部不对称分析，不补算体 winding，也不提供统计因果或热力学结论。",
        "",
        "复现：`python research/floquet-bdg-tbc/build_category_cells.py`、`python research/floquet-bdg-tbc/verify_category_cells.py`、`python research/floquet-bdg-tbc/analyze_repeated_categories.py`。",
        "",
    ]
    (ROOT / "REPEATED_CATEGORIES.md").write_text("\n".join(lines), encoding="utf-8")


def main():
    old = json.loads(OLD.read_text(encoding="utf-8"))
    new = json.loads(NEW.read_text(encoding="utf-8"))
    independent = json.loads(INDEPENDENT.read_text(encoding="utf-8"))
    if not independent.get("all_passed"):
        raise ValueError("New-cell independent verification has not passed")
    all_cells = old["cases"] + new["cases"]
    cases = []
    for strength in (0.05, 0.1):
        for seed in range(8):
            n400 = next(row for row in all_cells if (row["n"], row["strength"], row["seed"]) == (400, strength, seed))
            n600 = next(row for row in all_cells if (row["n"], row["strength"], row["seed"]) == (600, strength, seed))
            category, metrics = comparison(n400, n600)
            cases.append({"seed": seed, "strength": strength, "category": category, "comparison": metrics})
    counts = Counter(row["category"] for row in cases)
    by_strength = {str(strength): {category: sum(row["category"] == category and row["strength"] == strength for row in cases) for category in CATEGORY_ORDER} for strength in (0.05, 0.1)}
    data = {
        "schema": "floquet-bdg-repeated-category-analysis-v1",
        "analysis_date": "2026-11-11",
        "protocol_sha256": sha(PROTOCOL),
        "source_sha256": sha(OLD),
        "reversal_source_sha256": sha(REVERSAL),
        "new_cells_sha256": sha(NEW),
        "new_independent_sha256": sha(INDEPENDENT),
        "all_cells": all_cells,
        "cases": cases,
        "category_counts": {category: counts.get(category, 0) for category in CATEGORY_ORDER},
        "by_strength": by_strength,
        "new_seed_category_counts": {category: sum(row["category"] == category and row["seed"] >= 4 for row in cases) for category in CATEGORY_ORDER},
        "new_seed_count": 4,
        "new_winding_computed": False,
        "n640_computed": False,
        "causal_or_universal_category_claim": False,
    }
    (ROOT / "repeated_category_analysis.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    figure(data)
    markdown(data)
    print(json.dumps({key: value for key, value in data.items() if key not in ("cases", "all_cells")}, ensure_ascii=False, indent=2))
    print("generated repeated_category_analysis.json repeated-categories.png REPEATED_CATEGORIES.md")


if __name__ == "__main__":
    main()
