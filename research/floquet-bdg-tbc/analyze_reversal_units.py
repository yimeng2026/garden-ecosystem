"""Decompose selected sign-reversal cells without new physics input or promotion."""

import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "multi_seed_profile_control.json"
INDEPENDENT = ROOT / "multi_seed_independent.json"
REGISTRY = [(0, 0.05), (1, 0.05), (0, 0.1), (2, 0.1)]
LABELS = {
    (0, 0.05): "tail_growth_without_endpoint_recovery",
    (1, 0.05): "right_end_driven_symmetrization",
    (0, 0.1): "left_end_driven_threshold",
    (2, 0.1): "right_end_weakening_with_broadening",
}
plt.rcParams.update({
    "font.sans-serif": ["Microsoft YaHei", "SimHei", "Noto Sans CJK SC", "DejaVu Sans"],
    "axes.unicode_minus": False, "font.size": 10, "figure.dpi": 160,
})


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def recompute(pair, n):
    profile = np.asarray(pair["profile"], dtype=float)
    edge_sites = pair["edge_sites_per_end"]
    cumulative = np.cumsum(profile + profile[::-1])
    lengths = {f"L{threshold}": int(np.searchsorted(cumulative, threshold / 100, side="left") + 1) for threshold in (50, 90, 99)}
    left = float(profile[:edge_sites].sum())
    right = float(profile[-edge_sites:].sum())
    errors = [abs(left - pair["left_edge_weight"]), abs(right - pair["right_edge_weight"])]
    errors.extend(abs(lengths[key] - pair[key]) for key in ("L50", "L90", "L99"))
    return {
        "left_edge_weight": left, "right_edge_weight": right, **lengths,
        "asymmetry": abs(left - right) / pair["edge_weight"],
        "max_recompute_error": float(max(errors)),
    }


def analyze_case(source, seed, strength):
    n400 = next(row for row in source["cases"] if (row["n"], row["strength"], row["seed"]) == (400, strength, seed))
    n600 = next(row for row in source["cases"] if (row["n"], row["strength"], row["seed"]) == (600, strength, seed))
    first400, first600 = n400["pairs"][0], n600["pairs"][0]
    calc400, calc600 = recompute(first400, 400), recompute(first600, 600)
    left_delta = calc600["left_edge_weight"] - calc400["left_edge_weight"]
    right_delta = calc600["right_edge_weight"] - calc400["right_edge_weight"]
    asymmetry_delta = calc600["asymmetry"] - calc400["asymmetry"]
    comparison = {
        "n400_first": {key: value for key, value in first400.items() if key != "profile"},
        "n600_first": {key: value for key, value in first600.items() if key != "profile"},
        "n400_second": {key: value for key, value in n400["pairs"][1].items() if key != "profile"},
        "n600_second": {key: value for key, value in n600["pairs"][1].items() if key != "profile"},
        "n400_asymmetry": calc400["asymmetry"], "n600_asymmetry": calc600["asymmetry"],
        "asymmetry_delta": asymmetry_delta,
        "left_delta": left_delta, "right_delta": right_delta,
        "edge_delta": first600["edge_weight"] - first400["edge_weight"],
        "delta_L50": first600["L50"] - first400["L50"],
        "delta_L90": first600["L90"] - first400["L90"],
        "dominant_end": "right" if abs(right_delta) >= abs(left_delta) else "left",
        "mechanism": LABELS[(seed, strength)],
        "both_sizes_joint_pass": bool(first400["diagnostic_joint_pass"] and first600["diagnostic_joint_pass"]),
        "endpoint_loss": False if first400["diagnostic_joint_pass"] and first600["diagnostic_joint_pass"] else None,
        "isolation_explains_everything": False,
        "profile_metrics_recomputed": True,
        "max_recompute_error": max(calc400["max_recompute_error"], calc600["max_recompute_error"]),
    }
    return {"seed": seed, "strength": strength, "comparison": comparison}


def figure(cases):
    fig, axes = plt.subplots(2, 2, figsize=(13, 8.8), constrained_layout=False)
    names = [f"s{case['seed']},r{case['strength']}" for case in cases]
    x = np.arange(len(cases))
    width = 0.34
    for case_index, case in enumerate(cases):
        comparison = case["comparison"]
        for offset, n, color in ((-0.3, "n400_first", "#356A64"), (0.1, "n600_first", "#A25B3F")):
            axes[0, 0].bar(case_index + offset, comparison[n]["left_edge_weight"], 0.18, color=color)
            axes[0, 0].bar(case_index + offset + 0.2, comparison[n]["right_edge_weight"], 0.18, color=color, hatch="//")
        axes[0, 1].bar(case_index - width / 2, comparison["n400_asymmetry"], width, color="#356A64")
        axes[0, 1].bar(case_index + width / 2, comparison["n600_asymmetry"], width, color="#A25B3F")
        axes[1, 0].bar(case_index - width / 2, comparison["left_delta"], width, color="#356A64")
        axes[1, 0].bar(case_index + width / 2, comparison["right_delta"], width, color="#A25B3F")
        axes[1, 1].bar(case_index - width / 2, comparison["n400_first"]["L50"], width, color="#356A64")
        axes[1, 1].bar(case_index + width / 2, comparison["n600_first"]["L50"], width, color="#A25B3F")
    axes[0, 0].set_title("最近对：左右端权重（绿 N=400／棕 N=600，斜线右端）")
    axes[0, 0].set_ylabel("端部权重")
    axes[0, 1].set_title("左右不对称度（N=400 绿／N=600 棕）")
    axes[0, 1].set_ylabel("|左−右|／总端点权重")
    axes[1, 0].set_title("尺寸差分解：左端（绿）与右端（棕）")
    axes[1, 0].set_ylabel("N=600 − N=400")
    axes[1, 0].axhline(0, color="#666666", lw=0.8, ls="--")
    axes[1, 1].set_title("L50（N=400 绿／N=600 棕）")
    axes[1, 1].set_ylabel("格点数")
    for axis in axes.flat:
        axis.set_xticks(x)
        axis.set_xticklabels(names)
        axis.grid(axis="y", alpha=0.2)
    fig.subplots_adjust(top=0.88, bottom=0.1, left=0.08, right=0.98, hspace=0.38, wspace=0.28)
    fig.suptitle("反转单元：端部分解、对称性与覆盖尾长", fontsize=16, y=0.975)
    fig.savefig(ROOT / "reversal-units.png", bbox_inches="tight")
    plt.close(fig)


def fmt(value):
    return f"{value:.6g}"


def markdown(data):
    lines = [
        "# Floquet-BdG 反转单元机制诊断",
        "",
        "> 日期：2026-11-11。只使用已独立验证的 16 组 profile，定向分解 seed=0、1、2 的四个代表性对照。不追加种子，不补算体 winding，未计算 N=640。",
        "",
        "## 一、左右端差值与不对称性",
        "",
        "| seed | r | Δ左端 | Δ右端 | Δ总端点 | ΔL50 | Δ不对称度 | 机制标签（描述性） |",
        "|---:|---:|---:|---:|---:|---:|---:|:---|",
    ]
    for case in data["cases"]:
        row = case["comparison"]
        lines.append(f"| {case['seed']} | {case['strength']} | {fmt(row['left_delta'])} | {fmt(row['right_delta'])} | {fmt(row['edge_delta'])} | {row['delta_L50']} | {fmt(row['asymmetry_delta'])} | {row['mechanism']} |")
    lines += [
        "",
        "图 1 插入位置：左右端分解表之后、个案解释之前。",
        "",
        "![图 1：反转单元的端部与覆盖分解](reversal-units.png)",
        "",
        "**图 1**　上排为端点权重和不对称度，下排为左右端差值与 L50；绿色为 N=400，棕色为 N=600。",
        "",
        "## 二、两类不同反转机制",
        "",
        "### seed=1、r=0.05：右端驱动并趋于对称",
        "",
        "N=400→600 的左端权重增加约 0.0879，右端增加约 0.2475，右端驱动更显著。L50 从 66 缩短到 35，不对称度下降。谱隔离比没有同步大幅改善，因此不能把变化完全归因于谱隔离；它更像端部空间重新分配与两端趋于对称。",
        "",
        "### seed=2、r=0.1：右端减弱并伴随尾部变宽",
        "",
        "N=400→600 的左端权重增加约 0.0397，右端减少约 0.0759，总端点权重下降约 0.0362；L50 从 15 增至 27，不对称度上升。这是尾部变宽和右端减弱的组合。",
        "",
        "两种尺寸的端点权重分别约为 0.8217 和 0.7856，联合判据均通过，因此**不是端点消失**。N=600 的分离比更小，却出现端点权重下降，再次说明谱隔离与端部局域是不同指标。",
        "",
        "## 三、seed=0 参照不能省略",
        "",
        "r=0.05、seed=0 保持尾长增长且端点未恢复；r=0.1、seed=0 的正向端点差主要来自左端增强，右端基本持平。不同随机实现的‘尺寸效应’在方向、主导端和对称性上并不相同。",
        "",
        "## 四、解释边界与下一步",
        "",
        "本轮是定向解释性分解，不是普适机制命名或因果证明。数据来自已有 16 单元，原始独立后端验证未改变；本轮只重算左右端、覆盖与不对称指标。",
        "",
        "下一步应把‘右端驱动—对称化’与‘右端减弱—尾部变宽’作为可检验的结构描述，结合更多预登记种子的同类分解，检验它们是否形成可重复的类别，而不是把单次反转当作相变。",
        "",
        "复现：`python research/floquet-bdg-tbc/analyze_reversal_units.py`。原始对照、次近对摘要、重算误差和来源哈希保存在 `reversal_unit_analysis.json`。",
        "",
    ]
    (ROOT / "REVERSAL_UNITS.md").write_text("\n".join(lines), encoding="utf-8")


def main():
    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    independent = json.loads(INDEPENDENT.read_text(encoding="utf-8"))
    if not independent.get("all_passed"):
        raise ValueError("The original multi-seed independent verification did not pass")
    cases = [analyze_case(source, seed, strength) for seed, strength in REGISTRY]
    data = {
        "schema": "floquet-bdg-reversal-unit-analysis-v1",
        "analysis_date": "2026-11-11",
        "source_sha256": sha(SOURCE),
        "independent_source_sha256": sha(INDEPENDENT),
        "new_seed_count": 0,
        "new_winding_computed": False,
        "n640_computed": False,
        "analysis_role": "exploratory_decomposition_not_universal_law",
        "cases": cases,
    }
    (ROOT / "reversal_unit_analysis.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    figure(cases)
    markdown(data)
    print(json.dumps(data, ensure_ascii=False, indent=2))
    print("generated reversal_unit_analysis.json reversal-units.png REVERSAL_UNITS.md")


if __name__ == "__main__":
    main()
