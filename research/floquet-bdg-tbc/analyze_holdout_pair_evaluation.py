"""Evaluate frozen candidates on every preregistered remaining-seed-related pair."""

import itertools
import json
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

PROTOCOL = ROOT / "remaining_seed_outcome_protocol.json"
CANDIDATES = ROOT / "profile_stat_candidates_analysis.json"
SEED01 = ROOT / "seed01_matrix_midpoint_analysis.json"
SEED6 = ROOT / "seed6_matrix_midpoint_analysis.json"
OUT = ROOT / "holdout_pair_evaluation_analysis.json"
REPORT_DATE = "2026-11-12"
plt.rcParams.update({
    "font.sans-serif": ["Microsoft YaHei", "SimHei", "Noto Sans CJK SC", "DejaVu Sans"],
    "axes.unicode_minus": False, "font.size": 9, "figure.dpi": 160,
})


def sign(value):
    return 1 if value > 0 else -1 if value < 0 else 0


def load_sources():
    sources = {"seed01_matrix_midpoint_analysis.json": SEED01, "seed6_matrix_midpoint_analysis.json": SEED6}
    sources.update({f"remaining_seed{seed}_path_outcome_analysis.json": ROOT / f"remaining_seed{seed}_path_outcome_analysis.json" for seed in (2, 3, 4, 5, 7)})
    if any(not path.is_file() for path in sources.values()):
        raise FileNotFoundError("All five remaining path outcomes must exist before candidate evaluation")
    seed01 = json.loads(SEED01.read_text(encoding="utf-8"))
    seed6 = json.loads(SEED6.read_text(encoding="utf-8"))
    jumps = {str(row["seed"]): row["jump_change_count"] for row in seed01["summary_by_seed"]}
    jumps["6"] = seed6["summary"]["jump_change_count"]
    for seed in (2, 3, 4, 5, 7):
        data = json.loads(sources[f"remaining_seed{seed}_path_outcome_analysis.json"].read_text(encoding="utf-8"))
        jumps[str(seed)] = data["summary"]["jump_change_count"]
    return sources, jumps


def evaluate():
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    candidate_data = json.loads(CANDIDATES.read_text(encoding="utf-8"))
    sources, jumps = load_sources()
    comparison = set(protocol["comparison_seed_values"])
    pairs = [(a, b) for a, b in itertools.combinations(range(8), 2) if not (a in comparison and b in comparison)]
    records = []
    summaries = []
    for candidate in candidate_data["candidate_metrics"]:
        metric = candidate["metric"]
        direction = candidate["direction"]
        candidate_records = []
        for pair_index, (a, b) in enumerate(pairs, start=1):
            jump_delta = jumps[str(b)] - jumps[str(a)]
            value_a = candidate["values"][str(a)]
            value_b = candidate["values"][str(b)]
            candidate_delta = value_b - value_a
            informative = jump_delta != 0
            expected_sign = sign(jump_delta) if direction == "same_as_jump_changes" else -sign(jump_delta)
            actual_sign = sign(candidate_delta)
            consistent = (actual_sign == expected_sign and actual_sign != 0) if informative else None
            reason = "uninformative_jump_tie" if not informative else "direction_consistent" if consistent else "candidate_tie_not_strict" if actual_sign == 0 else "direction_inconsistent"
            row = {
                "evaluation_index": len(records) + 1, "pair_index": pair_index,
                "metric": metric, "level": candidate["level"], "direction": direction,
                "seed_a": a, "seed_b": b, "jump_a": jumps[str(a)], "jump_b": jumps[str(b)],
                "jump_delta": jump_delta, "value_a": value_a, "value_b": value_b,
                "candidate_delta": candidate_delta, "informative": informative,
                "expected_sign": expected_sign if informative else 0, "actual_sign": actual_sign,
                "consistent": consistent, "reason": reason,
            }
            records.append(row)
            candidate_records.append(row)
        informative_rows = [row for row in candidate_records if row["informative"]]
        consistent_count = sum(row["consistent"] is True for row in informative_rows)
        inconsistent_count = sum(row["consistent"] is False for row in informative_rows)
        all_consistent = bool(informative_rows) and inconsistent_count == 0
        summaries.append({
            "metric": metric, "level": candidate["level"], "direction": direction,
            "consistent_pair_count": consistent_count,
            "inconsistent_pair_count": inconsistent_count,
            "uninformative_pair_count": sum(not row["informative"] for row in candidate_records),
            "candidate_tie_count": sum(row["actual_sign"] == 0 for row in informative_rows),
            "all_informative_pairs_consistent": all_consistent,
            "assessment": "all_informative_pairs_consistent" if all_consistent else "not_all_informative_pairs_consistent",
        })
    return protocol, candidate_data, sources, jumps, pairs, records, summaries


def figure(data):
    jumps = data["jump_counts"]
    summaries = data["candidate_summaries"]
    records = data["pair_evaluations"]
    seeds = list(range(8))
    fig, axes = plt.subplots(2, 2, figsize=(14, 10.2))
    colors = ["#6F7F92" if seed in (0, 1, 6) else "#356A64" for seed in seeds]
    axes[0, 0].bar(seeds, [jumps[str(seed)] for seed in seeds], color=colors, width=0.68)
    axes[0, 0].set_xticks(seeds, [f"s{seed}" for seed in seeds])
    axes[0, 0].set_ylim(0, 7)
    axes[0, 0].set_ylabel("跳变改变数")
    axes[0, 0].set_title("八个实现的原始路径结局")
    axes[0, 0].grid(alpha=0.2, axis="y")
    axes[0, 1].bar([0, 1, 2], [20, 5, 3], color=["#356A64", "#C39A52", "#8A9299"], width=0.58)
    axes[0, 1].set_xticks([0, 1, 2], ["有效剩余对", "跳变平局", "训练内排除"])
    axes[0, 1].set_ylim(0, 24)
    axes[0, 1].set_ylabel("无序对数量")
    axes[0, 1].set_title("25 个检验对与 3 个排除对")
    axes[0, 1].grid(alpha=0.2, axis="y")
    metrics = [row["metric"] for row in summaries]
    y = np.arange(len(metrics))
    consistent = np.array([row["consistent_pair_count"] for row in summaries])
    inconsistent = np.array([row["inconsistent_pair_count"] for row in summaries])
    axes[1, 0].barh(y, consistent, color="#356A64", label="方向一致")
    axes[1, 0].barh(y, inconsistent, left=consistent, color="#A25B3F", label="方向不一致")
    axes[1, 0].set_yticks(y, metrics, fontsize=7)
    axes[1, 0].invert_yaxis()
    axes[1, 0].set_xlim(0, 20)
    axes[1, 0].set_xlabel("无序对数量（总计 20；非准确率）")
    axes[1, 0].set_title("16 个冻结候选的逐对结果")
    axes[1, 0].legend(frameon=False, fontsize=8)
    axes[1, 0].grid(alpha=0.2, axis="x")
    informative_pairs = [(row["seed_a"], row["seed_b"]) for row in records[:25] if row["informative"]]
    matrix = np.array([[1 if row["consistent"] else 0 for row in records if row["metric"] == metric and row["informative"]] for metric in metrics])
    axes[1, 1].imshow(matrix, aspect="auto", cmap=ListedColormap(["#A25B3F", "#356A64"]), vmin=0, vmax=1)
    axes[1, 1].set_yticks(np.arange(len(metrics)), metrics, fontsize=7)
    axes[1, 1].set_xticks(np.arange(len(informative_pairs)), [f"{a}-{b}" for a, b in informative_pairs], rotation=55, ha="right", fontsize=7)
    axes[1, 1].set_xlabel("seed 对")
    axes[1, 1].set_title("有效对方向：绿=一致，红=不一致")
    for spine in axes[1, 1].spines.values():
        spine.set_visible(False)
    fig.subplots_adjust(top=0.89, bottom=0.14, left=0.12, right=0.98, hspace=0.48, wspace=0.30)
    fig.suptitle("冻结候选的逐对方向检验（不是预测）", fontsize=16, y=0.97)
    fig.savefig(ROOT / "holdout-pair-evaluation.png", bbox_inches="tight")
    plt.close(fig)


def markdown(data):
    lines = [
        "# Floquet-BdG 剩余种子候选逐对方向检验",
        "",
        f"> 日期：{REPORT_DATE}。16 个冻结候选各检验25个剩余种子相关对，共400条记录；20对跳变计数不同，5对为跳变平局。训练种子内部3对排除。只执行预登记方向检验，不是预测，不计算相关性、回归、p 值或预测准确率。不补算体 winding，未计算 N=640。",
        "",
        "## 一、路径结局与检验对",
        "",
        "| seed | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
        "| 跳变改变数 | " + " | ".join(str(data["jump_counts"][str(seed)]) for seed in range(8)) + " |",
        "",
        "25 对由全部8个种子的28对中排除 seed=0、1、6 内部的3对得到。跳变计数相同的5对不提供方向信息：`(1,3)`、`(1,4)`、`(2,7)`、`(3,4)`、`(5,6)`。其余20对逐候选检查严格同向或反向。",
        "",
        "图 1 插入位置：检验对说明之后、候选汇总之前。",
        "",
        "![图 1：剩余种子候选逐对方向检验](holdout-pair-evaluation.png)",
        "",
        "**图 1**　路径结局、检验对类型、16个候选的一致与不一致计数，以及20个有效对的逐格结果。一致对数不是预测准确率。",
        "",
        "## 二、全部候选汇总",
        "",
        "| 指标 | 方向 | 一致对 | 不一致对 | 跳变平局 | 候选零差分 | 规则结论 |",
        "|:---|:---|---:|---:|---:|---:|:---|",
    ]
    for row in data["candidate_summaries"]:
        lines.append(f"| {row['metric']} | {row['direction']} | {row['consistent_pair_count']} | {row['inconsistent_pair_count']} | {row['uninformative_pair_count']} | {row['candidate_tie_count']} | {row['assessment']} |")
    full_count = sum(row["all_informative_pairs_consistent"] for row in data["candidate_summaries"])
    lines += [
        "",
        f"按全部20个有效对都必须一致的严格规则，共有 {full_count} 个候选满足；其余 {16 - full_count} 个不满足。该结论只描述冻结规则的结果，不是预测验证、统计显著性或因果归因。所有失败和平局均保留，没有选择性筛选。",
        "",
        "## 三、独立复核与证据边界",
        "",
        "候选值此前已用于描述统计，因此这不是完全未触碰的外部验证集；只有路径跳变结局是新生成的。当前工作至多是结局盲的逐对方向检验，不是外部实验重复。",
        "",
        "不删除不一致对，不删除跳变平局，不计算方向一致比例作为预测准确率，不拟合预测模型，不计算相关性、回归或 p 值。候选全对一致也不构成统计显著性；不一致也不等于证伪物理理论。",
        "",
        "本报告不新增 Floquet 单元，不外推真实态交换、谱交叉、连续路径、普遍尺寸律、因果机制、热力学极限或新类别。",
        "",
        "复现：`python research/floquet-bdg-tbc/analyze_holdout_pair_evaluation.py`；独立复核：`python research/floquet-bdg-tbc/verify_holdout_pair_evaluation.py`。全部400条逐对记录保存在 `holdout_pair_evaluation_analysis.json`。",
        "",
    ]
    (ROOT / "HOLDOUT_PAIR_EVALUATION.md").write_text("\n".join(lines), encoding="utf-8")


def check_only():
    data = json.loads(OUT.read_text(encoding="utf-8"))
    if data.get("protocol_sha256") != sha(PROTOCOL) or data.get("candidate_source_analysis_sha256") != sha(CANDIDATES):
        raise ValueError("Holdout pair evaluation is stale")
    if data.get("unfiltered_pair_record_count") != 400 or len(data.get("pair_evaluations", [])) != 400 or len(data.get("candidate_summaries", [])) != 16:
        raise ValueError("Holdout pair evaluation is incomplete")
    if data.get("informative_pair_count") != 20 or data.get("uninformative_pair_count") != 5 or not data.get("directional_screen_completed"):
        raise ValueError("Holdout pair evaluation scope changed")
    print(json.dumps({"check_only": True, "candidates": 16, "pair_records": 400, "informative_pairs": 20, "tie_pairs": 5, "all_passed": True}, ensure_ascii=False))
    return 0


def main():
    if "--check-only" in sys.argv:
        return check_only()
    protocol, candidate_data, sources, jumps, pairs, records, summaries = evaluate()
    informative_count = sum(row["informative"] for row in records[:25])
    data = {
        "schema": "floquet-bdg-holdout-pair-evaluation-v1",
        "analysis_date": protocol["analysis_date"], "report_date": REPORT_DATE,
        "protocol_sha256": sha(PROTOCOL), "candidate_source_analysis_sha256": sha(CANDIDATES),
        "path_outcome_sources": {name: sha(path) for name, path in sources.items()},
        "comparison_seed_values": protocol["comparison_seed_values"],
        "remaining_seed_values": protocol["seed_values"], "jump_counts": jumps,
        "all_remaining_path_outcomes_exist": True,
        "candidate_count": 16, "pair_count_per_candidate": len(pairs),
        "unfiltered_pair_record_count": len(records),
        "informative_pair_count": informative_count,
        "uninformative_pair_count": len(pairs) - informative_count,
        "training_only_pair_count_excluded": 3,
        "pair_evaluations": records, "candidate_summaries": summaries,
        "all_preregistered_results_retained": True,
        "failed_pairs_removed": False, "tie_pairs_removed": False,
        "directional_screen_completed": True, "candidate_evaluation_completed": True,
        "predictive_validation_completed": False, "pair_evaluation_is_not_prediction": True,
        "pristine_external_holdout_claim": False, "predictive_model_fitted": False,
        "correlation_claim": False, "predictive_accuracy_computed": False,
        "statistical_significance_claim": False, "causal_mechanism_proven": False,
        "continuous_path_proof": False, "spectral_crossing_proven": False,
        "state_exchange_proven": False, "thermodynamic_limit_proof": False,
        "new_floquet_cells_computed": 0, "new_floquet_spectra_recomputed": False,
        "new_winding_computed": False, "n640_computed": False,
        "new_taxonomy_claim": False, "categories_changed": False,
    }
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    figure(data)
    markdown(data)
    print(json.dumps({
        "candidates": 16, "pair_records": len(records), "informative_pairs": informative_count,
        "tie_pairs": len(pairs) - informative_count,
        "all_informative_pairs_consistent_count": sum(row["all_informative_pairs_consistent"] for row in summaries),
        "all_informative_pairs_consistent_names": [row["metric"] for row in summaries if row["all_informative_pairs_consistent"]],
        "candidate_consistency": {row["metric"]: [row["consistent_pair_count"], row["inconsistent_pair_count"]] for row in summaries},
        "new_floquet_cells": 0,
    }, ensure_ascii=False, indent=2))
    print("generated holdout_pair_evaluation_analysis.json holdout-pair-evaluation.png HOLDOUT_PAIR_EVALUATION.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
