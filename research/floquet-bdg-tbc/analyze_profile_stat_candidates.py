"""Preregistered disorder-profile statistics with non-predictive candidate labels."""

import hashlib
import json
from pathlib import Path
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from analyze_matched_beta_batch_a import fmt, sha  # noqa: E402

PROTOCOL = ROOT / "profile_stat_candidates_protocol.json"
BATCH_A = ROOT / "matched_beta_batch_a_analysis.json"
BATCH_B = ROOT / "matched_beta_batch_b_analysis.json"
SEED01 = ROOT / "seed01_matrix_midpoint_analysis.json"
SEED6 = ROOT / "seed6_matrix_midpoint_analysis.json"
REPORT_DATE = "2026-11-12"
plt.rcParams.update({
    "font.sans-serif": ["Microsoft YaHei", "SimHei", "Noto Sans CJK SC", "DejaVu Sans"],
    "axes.unicode_minus": False, "font.size": 9, "figure.dpi": 160,
})


def direction(values):
    ordered = {int(seed): float(value) for seed, value in values.items()}
    if ordered[1] < ordered[0] < ordered[6]:
        return "same_as_jump_changes"
    if ordered[1] > ordered[0] > ordered[6]:
        return "opposite_to_jump_changes"
    return "unordered"


def unique_count(values):
    return len({round(float(value), 15) for value in values.values()})


def compute_metrics(x):
    differences = np.diff(x)
    return {
        "mean": float(np.mean(x)), "std": float(np.std(x, ddof=0)),
        "min": float(np.min(x)), "q01": float(np.quantile(x, 0.01)),
        "q02": float(np.quantile(x, 0.02)),
        "q05": float(np.quantile(x, 0.05)), "q10": float(np.quantile(x, 0.10)),
        "q25": float(np.quantile(x, 0.25)), "q50": float(np.quantile(x, 0.50)),
        "q75": float(np.quantile(x, 0.75)), "q90": float(np.quantile(x, 0.90)),
        "q95": float(np.quantile(x, 0.95)), "q98": float(np.quantile(x, 0.98)),
        "q99": float(np.quantile(x, 0.99)),
        "max": float(np.max(x)), "mad": float(np.median(np.abs(x - np.median(x)))),
        "iqr": float(np.quantile(x, 0.75) - np.quantile(x, 0.25)),
        "low_frac_0p05": float(np.mean(x < 0.05)),
        "low_frac_0p1": float(np.mean(x < 0.1)), "low_frac_0p2": float(np.mean(x < 0.2)),
        "high_frac_0p8": float(np.mean(x > 0.8)),
        "high_frac_0p85": float(np.mean(x > 0.85)),
        "high_frac_0p9": float(np.mean(x > 0.9)),
        "high_frac_0p95": float(np.mean(x > 0.95)),
        "lag1": float(np.corrcoef(x[:-1], x[1:])[0, 1]),
        "lag2": float(np.corrcoef(x[:-2], x[2:])[0, 1]),
        "lag3": float(np.corrcoef(x[:-3], x[3:])[0, 1]),
        "lag4": float(np.corrcoef(x[:-4], x[4:])[0, 1]),
        "roughness_rms": float(np.sqrt(np.mean(differences ** 2))),
        "total_variation": float(np.mean(np.abs(differences))),
        "sign_changes": int(np.sum(np.signbit(differences[1:]) != np.signbit(differences[:-1]))),
    }


def compute_block_metrics(block):
    means = block.mean(axis=1)
    stds = block.std(axis=1, ddof=0)
    n = len(means)
    return {
        "block_mean_min": float(np.min(means)), "block_mean_max": float(np.max(means)),
        "block_mean_std": float(np.std(means, ddof=0)),
        "block_std_max": float(np.max(stds)), "block_std_mean": float(np.mean(stds)),
        "low_block_frac_0p1": float(np.mean(means < 0.1)),
        "high_block_frac_0p8": float(np.mean(means > 0.8)),
        "left_right_delta": float(np.mean(means[:n // 2]) - np.mean(means[n // 2:])),
        "endpoint_delta": float(means[0] - means[-1]),
    }


def load_profiles():
    a = json.loads(BATCH_A.read_text(encoding="utf-8"))
    b = json.loads(BATCH_B.read_text(encoding="utf-8"))
    rows = {}
    for source in (a, b):
        for row in source["realizations"]:
            rows[row["seed"]] = row["master_profile"]
    profiles = []
    for seed in range(8):
        master = np.asarray(rows[seed], dtype=float)
        profiles.append({
            "seed": seed, "master_profile": [float(value) for value in master],
            "master_profile_sha256": hashlib.sha256(master.tobytes()).hexdigest(),
            "beta400": [float(value) for value in master.reshape(400, 12).mean(axis=1)],
            "beta600": [float(value) for value in master.reshape(600, 8).mean(axis=1)],
            "master_metrics": compute_metrics(master),
            "block_metrics": {
                "n400": compute_block_metrics(master.reshape(400, 12)),
                "n600": compute_block_metrics(master.reshape(600, 8)),
            },
        })
    return profiles


def build_metric_records(profiles, protocol):
    records = []
    for metric in protocol["master_metrics"]:
        values = {str(row["seed"]): row["master_metrics"][metric] for row in profiles}
        records.append({
            "metric": metric, "level": "master", "values": values,
            "unique_count": unique_count(values), "direction": direction(values),
            "coarsening_direction": "not_applicable",
        })
    for metric in protocol["block_metrics"]:
        values_by_n = {
            f"n{n}": {str(row["seed"]): row["block_metrics"][f"n{n}"][metric] for row in profiles}
            for n in (400, 600)
        }
        directions = {level: direction(values) for level, values in values_by_n.items()}
        coarsening = "both_same" if directions["n400"] == directions["n600"] and directions["n400"] != "unordered" else "different" if directions["n400"] != directions["n600"] else "unordered"
        values = values_by_n["n400"]
        records.append({
            "metric": metric, "level": "block", "values": values, "values_by_n": values_by_n,
            "unique_count": unique_count(values), "direction": directions["n400"],
            "direction_by_n": directions, "coarsening_direction": coarsening,
        })
    for row in records:
        row["candidate"] = row["unique_count"] >= 6 and row["direction"] != "unordered"
    return records


def figure(data):
    profiles = data["profiles"]
    seeds = np.arange(8)
    colors = {0: "#356A64", 1: "#A25B3F", 6: "#6F7F92"}
    fig, axes = plt.subplots(2, 2, figsize=(14, 9.6))
    for metric, label in (("mean", "均值"), ("std", "标准差"), ("q05", "5%分位"), ("min", "最小值")):
        values = [row["master_metrics"][metric] for row in profiles]
        axes[0, 0].plot(seeds, values, marker="o", label=label)
        for seed in (0, 1, 6):
            axes[0, 0].scatter(seed, values[seed], color=colors[seed], s=70, zorder=5)
    axes[0, 0].set_xticks(seeds)
    axes[0, 0].set_xlabel("seed")
    axes[0, 0].set_ylabel("统计值")
    axes[0, 0].set_title("主剖面位置与低端统计")
    axes[0, 0].legend(frameon=False, fontsize=8)
    axes[0, 0].grid(alpha=0.2)
    for n, linestyle in ((400, "-"), (600, "--")):
        values = [row["master_metrics"]["roughness_rms"] for row in profiles]
        axes[0, 1].plot(seeds, values, marker="o", label="粗糙度RMS")
        values2 = [row["master_metrics"]["total_variation"] for row in profiles]
        axes[0, 1].plot(seeds, values2, marker="s", ls="--", label="平均绝对差")
        for seed in (0, 1, 6):
            axes[0, 1].scatter(seed, values[seed], color=colors[seed], s=65, zorder=5)
        break
    axes[0, 1].set_xticks(seeds)
    axes[0, 1].set_xlabel("seed")
    axes[0, 1].set_ylabel("相邻差分统计")
    axes[0, 1].set_title("局部粗糙度随无序实现变化")
    axes[0, 1].legend(frameon=False, fontsize=8)
    axes[0, 1].grid(alpha=0.2)
    for metric, label, color in (("low_frac_0p1", "x<0.1", "#356A64"), ("low_frac_0p2", "x<0.2", "#6F7F92"), ("high_frac_0p8", "x>0.8", "#A25B3F")):
        axes[1, 0].plot(seeds, [row["master_metrics"][metric] for row in profiles], marker="o", color=color, label=label)
    axes[1, 0].set_xticks(seeds)
    axes[1, 0].set_xlabel("seed")
    axes[1, 0].set_ylabel("尾部分数")
    axes[1, 0].set_title("低值与高值尾部分数")
    axes[1, 0].legend(frameon=False, fontsize=8)
    axes[1, 0].grid(alpha=0.2)
    candidates = data["candidate_metrics"][:12]
    if not candidates:
        axes[1, 1].text(0.5, 0.5, "无符合预登记规则的候选", ha="center", va="center", transform=axes[1, 1].transAxes)
    else:
        x = np.arange(len(candidates))
        for seed, color in ((1, "#A25B3F"), (0, "#356A64"), (6, "#6F7F92")):
            ranks = []
            for row in candidates:
                ordered = sorted(row["values"], key=lambda key: row["values"][key])
                rank = {key: index + 1 for index, key in enumerate(ordered)}
                ranks.append(rank[str(seed)])
            axes[1, 1].plot(x, ranks, marker="o", color=color, label=f"seed={seed}")
        axes[1, 1].set_xticks(x, [row["metric"] for row in candidates], rotation=55, ha="right", fontsize=7)
        axes[1, 1].set_ylim(0.5, 8.5)
        axes[1, 1].set_ylabel("8个种子中的秩次")
        axes[1, 1].set_title("前12个探索性候选的秩次（非预测）")
        axes[1, 1].legend(frameon=False, fontsize=8)
        axes[1, 1].grid(alpha=0.2)
    fig.subplots_adjust(top=0.89, bottom=0.16, left=0.08, right=0.98, hspace=0.46, wspace=0.25)
    fig.suptitle("无序主剖面的候选统计指标与实现差异", fontsize=16, y=0.97)
    fig.savefig(ROOT / "profile-stat-candidates.png", bbox_inches="tight")
    plt.close(fig)


def markdown(data):
    lines = [
        "# Floquet-BdG 无序主剖面候选统计指标",
        "",
        f"> 日期：{REPORT_DATE}。全部8个主剖面、40组指标记录；只计算描述统计与预登记方向标签，不新增 Floquet 单元，不拟合预测模型，不计算 p 值。不补算体 winding，未计算 N=640。",
        "",
        "## 一、主剖面统计与实现差异",
        "",
        "统一计算位置、尾部、局部 block、粗糙度、总变差、符号变化和滞后相关。block 使用 N=400 的12值平均与 N=600 的8值平均，局部标准差采用 ddof=0。所有结果不归一化，不筛选有利剖面。",
        "",
        "| seed | 均值 | 标准差 | 最小值 | 5%分位 | 95%分位 | 最大值 | 粗糙度RMS | x<0.1 | x>0.8 | lag1 |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in data["profiles"]:
        stats = row["master_metrics"]
        lines.append(f"| {row['seed']} | {fmt(stats['mean'])} | {fmt(stats['std'])} | {fmt(stats['min'])} | {fmt(stats['q05'])} | {fmt(stats['q95'])} | {fmt(stats['max'])} | {fmt(stats['roughness_rms'])} | {fmt(stats['low_frac_0p1'])} | {fmt(stats['high_frac_0p8'])} | {fmt(stats['lag1'])} |")
    lines += [
        "",
        "图 1 插入位置：主剖面汇总表之后、候选规则之前。",
        "",
        "![图 1：无序主剖面候选统计指标](profile-stat-candidates.png)",
        "",
        "**图 1**　主剖面位置、粗糙度、尾部分数及前12个探索性候选的秩次。秩次只用于描述，不是预测准确率。",
        "",
        "## 二、预登记候选规则",
        "",
        "指标在8个种子中至少有6个不同取值，并在 seed=1、0、6 上严格同向或反向于跳变计数 0、4、6，才标为探索性候选。block 指标另记录 N=400 与 N=600 是否同向。全部40组记录均保存在 JSON，报告只按协议顺序展示前12个候选。",
        "",
        "| 指标 | 层级 | 方向 | block同向性 | 不同取值数 | seed=1值 | seed=0值 | seed=6值 |",
        "|:---|:---|:---|:---:|---:|---:|---:|---:|",
    ]
    for row in data["candidate_metrics"][:12]:
        lines.append(f"| {row['metric']} | {row['level']} | {row['direction']} | {row['coarsening_direction']} | {row['unique_count']} | {fmt(row['values']['1'])} | {fmt(row['values']['0'])} | {fmt(row['values']['6'])} |")
    lines += [
        "",
        f"共有 {len(data['candidate_metrics'])} 个探索性候选。它们只满足预设排序规则，不是统计显著性、因果归因或预测证据。",
        "",
        "## 三、为什么仍不能直接建模",
        "",
        f"三个对照种子的跳变计数为 {data['path_jump_counts']}，而主导项计数均为 {data['path_driver_counts']}。主导项计数没有排序差异，不能为任何统计指标提供监督标签。跨种子最大跳变链接也完全一致的条目数为0，进一步说明实现依赖不能被单一统计量替代。",
        "",
        "下一步若使用这些候选，必须先在剩余种子上预注册验证指标与结局定义，再评估其是否仍有一致方向；不能把本报告的方向匹配当作可推广的预测能力。",
        "",
        "本报告不能外推为普遍尺寸律、真实态交换、谱交叉、统计显著性或热力学极限结论。旧交换候选属于不同无序实现，不能与统计差分直接相减。",
        "",
        "复现：`python research/floquet-bdg-tbc/analyze_profile_stat_candidates.py`。完整40组指标、方向、候选规则和来源哈希保存在 `profile_stat_candidates_analysis.json`。",
        "",
    ]
    (ROOT / "PROFILE_STAT_CANDIDATES.md").write_text("\n".join(lines), encoding="utf-8")


def check_only():
    stored = json.loads((ROOT / "profile_stat_candidates_analysis.json").read_text(encoding="utf-8"))
    if stored.get("protocol_sha256") != sha(PROTOCOL) or stored.get("seed01_analysis_sha256") != sha(SEED01) or stored.get("seed6_analysis_sha256") != sha(SEED6):
        raise ValueError("Profile-statistic candidate evidence is stale")
    if len(stored.get("profiles", [])) != 8 or len(stored.get("metric_records", [])) != 40:
        raise ValueError("Profile-statistic candidate evidence is incomplete")
    if not stored.get("all_preregistered_results_retained") or stored.get("predictive_model_fitted"):
        raise ValueError("Profile-statistic scope changed")
    print(json.dumps({"check_only": True, "profiles": 8, "metric_records": 40, "candidates": len(stored["candidate_metrics"]), "all_passed": True}, ensure_ascii=False))
    return 0


def main():
    if "--check-only" in sys.argv:
        return check_only()
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    profiles = load_profiles()
    records = build_metric_records(profiles, protocol)
    data = {
        "schema": "floquet-bdg-profile-stat-candidates-analysis-v1",
        "analysis_date": protocol["analysis_date"], "report_date": REPORT_DATE,
        "protocol_sha256": sha(PROTOCOL),
        "batch_a_analysis_sha256": sha(BATCH_A), "batch_b_analysis_sha256": sha(BATCH_B),
        "seed01_analysis_sha256": sha(SEED01), "seed6_analysis_sha256": sha(SEED6),
        "profiles": profiles, "metric_records": records,
        "candidate_metrics": [row for row in records if row["candidate"]],
        "path_jump_counts": {"0": 4, "1": 0, "6": 6},
        "path_driver_counts": {"0": 4, "1": 4, "6": 4},
        "new_floquet_cells_computed": 0, "new_seed_count": 0,
        "new_winding_computed": False, "n640_computed": False,
        "all_preregistered_results_retained": True,
        "predictive_model_fitted": False, "correlation_claim": False,
        "statistical_significance_claim": False, "causal_mechanism_proven": False,
        "universal_size_law_claim": False, "thermodynamic_limit_proof": False,
        "new_taxonomy_claim": False, "categories_changed": False,
    }
    (ROOT / "profile_stat_candidates_analysis.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    figure(data)
    markdown(data)
    print(json.dumps({"profiles": 8, "metric_records": 40, "candidate_count": len(data["candidate_metrics"]), "candidate_names": [row["metric"] for row in data["candidate_metrics"]], "new_floquet_cells": 0}, ensure_ascii=False, indent=2))
    print("generated profile_stat_candidates_analysis.json profile-stat-candidates.png PROFILE_STAT_CANDIDATES.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
