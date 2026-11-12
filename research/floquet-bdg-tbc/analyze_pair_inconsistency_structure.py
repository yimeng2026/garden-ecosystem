"""Describe shared and metric-specific failures without changing the frozen rule."""

import itertools
import json
from pathlib import Path
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from analyze_matched_beta_batch_a import sha  # noqa: E402

PROTOCOL = ROOT / "pair_inconsistency_structure_protocol.json"
SOURCE = ROOT / "holdout_pair_evaluation_analysis.json"
OUT = ROOT / "pair_inconsistency_structure_analysis.json"
REPORT_DATE = "2026-11-12"
plt.rcParams.update({
    "font.sans-serif": ["Microsoft YaHei", "SimHei", "Noto Sans CJK SC", "DejaVu Sans"],
    "axes.unicode_minus": False, "font.size": 9, "figure.dpi": 160,
})


def build_structure(source):
    records = source["pair_evaluations"]
    metrics = [row["metric"] for row in source["candidate_summaries"]]
    first = records[:25]
    informative_pairs = [(row["seed_a"], row["seed_b"]) for row in first if row["informative"]]
    pair_summaries = []
    for a, b in informative_pairs:
        local = [row for row in records if row["seed_a"] == a and row["seed_b"] == b]
        consistent_names = [row["metric"] for row in local if row["consistent"] is True]
        inconsistent_names = [row["metric"] for row in local if row["consistent"] is False]
        zero_names = [row["metric"] for row in local if row["actual_sign"] == 0]
        pair_summaries.append({
            "seed_a": a, "seed_b": b, "jump_a": local[0]["jump_a"], "jump_b": local[0]["jump_b"],
            "consistent_count": len(consistent_names), "inconsistent_count": len(inconsistent_names),
            "zero_diff_count": len(zero_names), "consistent_metric_names": consistent_names,
            "inconsistent_metric_names": inconsistent_names, "candidate_zero_diff_names": zero_names,
            "all_candidates_inconsistent": len(inconsistent_names) == 16,
            "all_candidates_consistent": len(inconsistent_names) == 0,
        })
    failure_sets = []
    failure_lookup = {}
    for metric in metrics:
        local = [row for row in records if row["metric"] == metric and row["informative"]]
        failing = [[row["seed_a"], row["seed_b"]] for row in local if row["consistent"] is False]
        zero = [[row["seed_a"], row["seed_b"]] for row in local if row["actual_sign"] == 0]
        failure_sets.append({"metric": metric, "failing_pairs": failing, "zero_diff_pairs": zero})
        failure_lookup[metric] = {tuple(pair) for pair in failing}
    spectrum = []
    for k in range(17):
        pairs = [[row["seed_a"], row["seed_b"]] for row in pair_summaries if row["inconsistent_count"] == k]
        spectrum.append({"inconsistent_candidate_count": k, "pair_count": len(pairs), "pairs": pairs})
    overlap = []
    for a, b in itertools.combinations(metrics, 2):
        set_a, set_b = failure_lookup[a], failure_lookup[b]
        shared = set_a & set_b
        union = set_a | set_b
        overlap.append({
            "metric_a": a, "metric_b": b,
            "intersection_count": len(shared), "union_count": len(union),
            "only_a_count": len(set_a - set_b), "only_b_count": len(set_b - set_a),
            "shared_pairs": [list(pair) for pair in sorted(shared)],
            "only_a_pairs": [list(pair) for pair in sorted(set_a - set_b)],
            "only_b_pairs": [list(pair) for pair in sorted(set_b - set_a)],
            "jaccard": len(shared) / len(union) if union else None,
        })
    closest = next(row for row in overlap if row["metric_a"] == "q99" and row["metric_b"] == "block_std_max")
    return pair_summaries, failure_sets, spectrum, overlap, closest


def figure(data):
    pairs = data["pair_summaries"]
    spectrum = data["shared_failure_spectrum"]
    metrics = data["candidate_names"]
    overlap = data["overlap_records"]
    closest = data["closest_candidate_comparison"]
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    x = np.arange(len(pairs))
    counts = [row["inconsistent_count"] for row in pairs]
    axes[0, 0].bar(x, counts, color=["#A25B3F" if count == 16 else "#C39A52" if count else "#356A64" for count in counts], width=0.72)
    axes[0, 0].set_xticks(x, [f"{row['seed_a']}-{row['seed_b']}" for row in pairs], rotation=55, ha="right", fontsize=7)
    axes[0, 0].set_ylim(0, 16.8)
    axes[0, 0].set_ylabel("不一致候选数")
    axes[0, 0].set_title("每个有效无序对的候选失败数")
    axes[0, 0].grid(alpha=0.2, axis="y")
    axes[0, 1].bar(range(17), [row["pair_count"] for row in spectrum], color="#6F7F92", width=0.72)
    axes[0, 1].set_xticks(range(17))
    axes[0, 1].set_xlabel("恰好失败的候选数 k")
    axes[0, 1].set_ylabel("无序对数量")
    axes[0, 1].set_title("共同失败的完整 k 谱（不合并类别）")
    axes[0, 1].grid(alpha=0.2, axis="y")
    lookup = {(row["metric_a"], row["metric_b"]): row["jaccard"] for row in overlap}
    matrix = np.full((16, 16), np.nan)
    for i, a in enumerate(metrics):
        for j, b in enumerate(metrics):
            if i == j:
                continue
            key = (a, b) if i < j else (b, a)
            matrix[i, j] = lookup[key]
    cmap = plt.get_cmap("YlGnBu").copy()
    cmap.set_bad("#F2F2F2")
    image = axes[1, 0].imshow(matrix, cmap=cmap, vmin=0, vmax=1, aspect="auto")
    axes[1, 0].set_xticks(range(16), metrics, rotation=55, ha="right", fontsize=7)
    axes[1, 0].set_yticks(range(16), metrics, fontsize=7)
    axes[1, 0].set_title("失败集合 Jaccard 重叠（描述性）")
    fig.colorbar(image, ax=axes[1, 0], fraction=0.046, pad=0.03)
    labels = ["共同失败", "仅 q99", "仅 block_std_max"]
    values = [closest["intersection_count"], closest["only_a_count"], closest["only_b_count"]]
    axes[1, 1].bar(labels, values, color=["#356A64", "#C39A52", "#6F7F92"], width=0.58)
    axes[1, 1].set_ylim(0, 3.2)
    axes[1, 1].set_ylabel("无序对数量")
    axes[1, 1].set_title("两个最接近候选的失败集合关系")
    axes[1, 1].grid(alpha=0.2, axis="y")
    shared_text = "、".join(f"{a}-{b}" for a, b in closest["shared_pairs"]) or "无"
    axes[1, 1].text(0.5, -0.23, f"共同失败对：{shared_text}", transform=axes[1, 1].transAxes, ha="center", fontsize=9)
    fig.subplots_adjust(top=0.89, bottom=0.17, left=0.10, right=0.96, hspace=0.52, wspace=0.34)
    fig.suptitle("候选不一致对的结构：共同失败与指标特异失败", fontsize=16, y=0.97)
    fig.savefig(ROOT / "pair-inconsistency-structure.png", bbox_inches="tight")
    plt.close(fig)


def markdown(data):
    closest = data["closest_candidate_comparison"]
    lines = [
        "# Floquet-BdG 候选不一致对结构分析",
        "",
        f"> 日期：{REPORT_DATE}。只分析既有20个有效无序对、16个失败集合及其120组重叠；共有104条方向不一致赋值。原400条记录与5个跳变平局不变。不是因果归因，不是预测，不修改严格规则，不提出集成或新指标。不补算体 winding，未计算 N=640。",
        "",
        "## 一、每个有效对的失败候选数",
        "",
        "| seed 对 | 跳变计数 | 一致候选 | 不一致候选 | 候选零差分 | 不一致指标 |",
        "|:---|:---|---:|---:|---:|:---|",
    ]
    for row in data["pair_summaries"]:
        lines.append(f"| {row['seed_a']}—{row['seed_b']} | {row['jump_a']}→{row['jump_b']} | {row['consistent_count']} | {row['inconsistent_count']} | {row['zero_diff_count']} | {'、'.join(row['inconsistent_metric_names']) or '无'} |")
    lines += [
        "",
        "完整 k 谱记录每个失败候选数对应的无序对，不把多个 k 合并成新类别。共同失败仅表示多个指标在同一无序对上不一致，不是因果归因。",
        "",
        "| 失败候选数 k | 无序对数量 | seed 对 |",
        "|---:|---:|:---|",
    ]
    for row in data["shared_failure_spectrum"]:
        if row["pair_count"]:
            lines.append(f"| {row['inconsistent_candidate_count']} | {row['pair_count']} | {'、'.join(f'{a}-{b}' for a, b in row['pairs'])} |")
    lines += [
        "",
        "图 1 插入位置：k 谱之后、失败集合重叠之前。",
        "",
        "![图 1：候选不一致对结构](pair-inconsistency-structure.png)",
        "",
        "**图 1**　每个有效对的失败候选数、完整 k 谱、失败集合 Jaccard 重叠及两个最接近候选的集合关系。Jaccard 只描述集合重叠，不是相关性或预测能力。",
        "",
        "## 二、120 组失败集合重叠",
        "",
        "对16个候选的120组两两组合，计算失败集合的交集、并集、共享对、单侧对和 Jaccard。空并集记为 null，不记为1。所有计算均保留在分析 JSON。",
        "",
        f"q99 与 block_std_max 的交集为 {closest['intersection_count']} 对，并集为 {closest['union_count']} 对，Jaccard={closest['jaccard']:.6g}。共同失败对为 {closest['shared_pairs']}；仅 q99 失败为 {closest['only_a_pairs']}，仅 block_std_max 失败为 {closest['only_b_pairs']}。这不构成联合使用或放宽规则的建议。",
        "",
        "| 指标 | 失败对数 | 失败 seed 对 | 候选零差分对 |",
        "|:---|---:|:---|:---|",
    ]
    for row in data["candidate_failure_sets"]:
        lines.append(f"| {row['metric']} | {len(row['failing_pairs'])} | {'、'.join(f'{a}-{b}' for a, b in row['failing_pairs']) or '无'} | {'、'.join(f'{a}-{b}' for a, b in row['zero_diff_pairs']) or '无'} |")
    lines += [
        "",
        "## 三、证据边界",
        "",
        "共同失败位置可能来自同一无序实现对多个统计量的共同影响，也可能只是离散跳变计数造成的集合重合；本分析不能区分这些解释，因此不是因果归因。指标特异失败也不能自动解释为指标缺陷或物理机制。",
        "",
        "本分析不是预测验证、统计显著性检验或完全未触碰的外部验证；不提出新指标、集成规则或修正版接受阈值。严格规则下0／16全对一致的原结论不变。",
        "",
        "复现：`python research/floquet-bdg-tbc/analyze_pair_inconsistency_structure.py`；独立复核：`python research/floquet-bdg-tbc/verify_pair_inconsistency_structure.py`。",
        "",
    ]
    (ROOT / "PAIR_INCONSISTENCY_STRUCTURE.md").write_text("\n".join(lines), encoding="utf-8")


def check_only():
    data = json.loads(OUT.read_text(encoding="utf-8"))
    if data.get("protocol_sha256") != sha(PROTOCOL) or data.get("source_pair_evaluation_sha256") != sha(SOURCE):
        raise ValueError("Pair-inconsistency structure evidence is stale")
    if len(data.get("pair_summaries", [])) != 20 or len(data.get("overlap_records", [])) != 120 or data.get("total_inconsistent_assignments") != 104:
        raise ValueError("Pair-inconsistency structure evidence is incomplete")
    print(json.dumps({"check_only": True, "pair_summaries": 20, "overlap_records": 120, "total_inconsistent_assignments": 104, "all_passed": True}, ensure_ascii=False))
    return 0


def main():
    if "--check-only" in sys.argv:
        return check_only()
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    pair_summaries, failure_sets, spectrum, overlap, closest = build_structure(source)
    data = {
        "schema": "floquet-bdg-pair-inconsistency-structure-v1",
        "analysis_date": protocol["analysis_date"], "report_date": REPORT_DATE,
        "protocol_sha256": sha(PROTOCOL), "source_pair_evaluation_sha256": sha(SOURCE),
        "candidate_names": [row["metric"] for row in source["candidate_summaries"]],
        "source_pair_record_count": source["unfiltered_pair_record_count"],
        "source_uninformative_pair_count": source["uninformative_pair_count"],
        "source_records_unchanged": True,
        "pair_summaries": pair_summaries, "candidate_failure_sets": failure_sets,
        "shared_failure_spectrum": spectrum, "overlap_records": overlap,
        "closest_candidate_comparison": closest,
        "total_inconsistent_assignments": sum(row["inconsistent_pair_count"] for row in source["candidate_summaries"]),
        "all_preregistered_results_retained": True,
        "strict_rule_changed": False, "failed_pairs_removed": False, "tie_pairs_removed": False,
        "new_metric_proposed": False, "ensemble_rule_proposed": False,
        "structure_is_descriptive_only": True, "causal_attribution_completed": False,
        "predictive_validation_completed": False, "pristine_external_holdout_claim": False,
        "predictive_model_fitted": False, "correlation_claim": False,
        "predictive_accuracy_computed": False, "statistical_significance_claim": False,
        "causal_mechanism_proven": False, "continuous_path_proof": False,
        "spectral_crossing_proven": False, "state_exchange_proven": False,
        "thermodynamic_limit_proof": False, "new_taxonomy_claim": False,
        "new_floquet_cells_computed": 0, "new_floquet_spectra_recomputed": False,
        "new_winding_computed": False, "n640_computed": False,
    }
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    figure(data)
    markdown(data)
    print(json.dumps({
        "pair_summaries": len(pair_summaries), "overlap_records": len(overlap),
        "total_inconsistent_assignments": data["total_inconsistent_assignments"],
        "all_candidates_inconsistent_pairs": [[row["seed_a"], row["seed_b"]] for row in pair_summaries if row["all_candidates_inconsistent"]],
        "all_candidates_consistent_pairs": [[row["seed_a"], row["seed_b"]] for row in pair_summaries if row["all_candidates_consistent"]],
        "closest_candidate_comparison": closest,
    }, ensure_ascii=False, indent=2))
    print("generated pair_inconsistency_structure_analysis.json pair-inconsistency-structure.png PAIR_INCONSISTENCY_STRUCTURE.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
