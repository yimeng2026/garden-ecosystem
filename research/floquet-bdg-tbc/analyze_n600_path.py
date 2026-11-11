"""Replicate the two refined path regions at N=600 and compare metrics with N=400."""

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
from analyze_fixed_n_path import compute_point, adjacent_link  # noqa: E402
from analyze_subspace_overlap import source_cell  # noqa: E402

PROTOCOL = ROOT / "n600_path_protocol.json"
SOURCE = ROOT / "repeated_category_analysis.json"
N400_SOURCE = ROOT / "path_refinement_analysis.json"
COARSE = ROOT / "fixed_n_path_analysis.json"
CANDIDATE = ROOT / "swap_candidate_spectrum_analysis.json"
OLD_INDEPENDENT = ROOT / "multi_seed_independent.json"
NEW_INDEPENDENT = ROOT / "category_new_cells_independent.json"
TITLES = {"max_change": "最大变化链接", "minimum_region": "最小间隔邻域"}
plt.rcParams.update({
    "font.sans-serif": ["Microsoft YaHei", "SimHei", "Noto Sans CJK SC", "DejaVu Sans"],
    "axes.unicode_minus": False, "font.size": 10, "figure.dpi": 160,
})


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def summarize(points, links):
    assignments = [link["dominant_assignment"] for link in links]
    minimum = min(points, key=lambda row: row["center_separation"])
    changes = [abs(link["center_separation_after"] - link["center_separation_before"]) for link in links]
    return {
        "diagonal_link_count": assignments.count("diagonal"), "swapped_link_count": assignments.count("swapped"),
        "tie_link_count": assignments.count("tie_exact"),
        "min_center_separation": minimum["center_separation"], "min_center_separation_strength": minimum["strength"],
        "max_adjacent_center_separation_change": max(changes),
        "pair0_joint_pass_strengths": [point["strength"] for point in points if point["pairs"][0]["diagnostic_joint_pass"]],
        "pair1_joint_pass_strengths": [point["strength"] for point in points if point["pairs"][1]["diagnostic_joint_pass"]],
    }


def fmt(value):
    return f"{value:.6g}"


def figure(data):
    fig, axes = plt.subplots(2, 2, figsize=(13, 9.2), constrained_layout=False)
    n400_regions = {region["label"]: region for region in data["n400_regions"]}
    for row_index, region in enumerate(data["regions"]):
        label = region["label"]
        n400 = n400_regions[label]
        strengths = [point["strength"] for point in region["points"]]
        for source_region, name, color in ((region, "N=600", "#356A64"), (n400, "N=400", "#A25B3F")):
            axes[row_index, 0].semilogy(strengths, [point["center_separation"] for point in source_region["points"]], marker="o", color=color, label=name)
            axes[row_index, 1].semilogy([(link["from"] + link["to"]) / 2 for link in source_region["links"]], [link["diagonal_score"] for link in source_region["links"]], marker="o", color=color, label=name)
        axes[row_index, 0].set_ylabel("两对中心间隔")
        axes[row_index, 0].set_title(TITLES[label] + "：中心间隔")
        axes[row_index, 0].legend(frameon=False)
        axes[row_index, 1].set_ylabel("同谱秩平均重叠")
        axes[row_index, 1].set_title(TITLES[label] + "：同 N 分配得分")
        axes[row_index, 1].legend(frameon=False)
        for column in (0, 1):
            axis = axes[row_index, column]
            axis.axvline(0.05 if label == "max_change" else 0.0425, color="#888888", lw=0.8, ls="--")
            axis.set_xlabel("无序强度 r")
            axis.grid(alpha=0.2, which="both")
    fig.subplots_adjust(top=0.88, bottom=0.11, left=0.08, right=0.97, hspace=0.43, wspace=0.28)
    fig.suptitle("N=600 与 N=400：各自同 N 的路径指标比较", fontsize=16, y=0.97)
    fig.savefig(ROOT / "n600-path.png", bbox_inches="tight")
    plt.close(fig)


def markdown(data):
    summary = data["summary"]
    comparison = data["size_comparison"]
    lines = [
        "# Floquet-BdG N=600 细化路径复核",
        "",
        "> 日期：2026-11-11。N=600、seed=6、固定随机流。复核 N=400 的两个细化邻域；各自比较同 N 子空间，不做跨尺寸本征矢点积。不新增类别、不补算体 winding，未计算 N=640。",
        "",
        "## 一、参考点与比较规则",
        "",
        "N=600 的 r=0.050 原冻结单元必须复现到1e-10。随后对相同强度点比较谱中心、中心间隔、既有诊断和相邻重叠；尺寸对照仅比较指标，不宣称尺寸不变性。",
        "",
        f"参考点最大数值误差为 {data['max_reference_error']:.3e}。新增 N=600 参数点共9个，两个区域共10点、8条链接。",
        "",
    ]
    for region in data["regions"]:
        lines += [
            f"## 二、{TITLES[region['label']]}",
            "",
            "| r | N=600中心间隔 | N=400中心间隔 | 绝对差 |",
            "|---:|---:|---:|---:|",
        ]
        n400 = next(item for item in data["n400_regions"] if item["label"] == region["label"])
        for point, old in zip(region["points"], n400["points"]):
            lines.append(f"| {point['strength']} | {fmt(point['center_separation'])} | {fmt(old['center_separation'])} | {fmt(abs(point['center_separation'] - old['center_separation']))} |")
        lines += [
            "",
            "| 从 r | 到 r | N=600同谱秩 | N=400同谱秩 | N=600交换 | N=400交换 | 主导分配（N=600／N=400） |",
            "|---:|---:|---:|---:|---:|---:|:---|",
        ]
        for link, old in zip(region["links"], n400["links"]):
            lines.append(f"| {link['from']} | {link['to']} | {fmt(link['diagonal_score'])} | {fmt(old['diagonal_score'])} | {fmt(link['swapped_score'])} | {fmt(old['swapped_score'])} | {link['dominant_assignment']}／{old['dominant_assignment']} |")
        region_summary = region["summary"]
        lines += [
            "",
            f"本区域 N=600 最小中心间隔为 {fmt(region_summary['min_center_separation'])}，位于 r={region_summary['min_center_separation_strength']}；最大相邻间隔变化为 {fmt(region_summary['max_adjacent_center_separation_change'])}。最近对通过强度为 {region_summary['pair0_joint_pass_strengths']}，次近对通过强度为 {region_summary['pair1_joint_pass_strengths']}。",
            "",
        ]
    lines += [
        "图 1 插入位置：两个区域的数值表之后、尺寸对照结论之前。",
        "",
        "![图 1：N=600 与 N=400 的路径指标比较](n600-path.png)",
        "",
        "**图 1**　两个尺寸各自的同 N 谱指标和重叠得分，不使用跨尺寸本征矢点积。",
        "",
        "## 三、尺寸对照结论与边界",
        "",
        f"N=600 的8条链接中，同谱秩占优 {summary['diagonal_link_count']}，交换占优 {summary['swapped_link_count']}，精确并列 {summary['tie_link_count']}。与 N=400 的主导分配一致 {comparison['assignment_agreement_count']}/8。",
        "",
        f"N=600 最小中心间隔为 {fmt(summary['min_center_separation'])}，位于 r={summary['min_center_separation_strength']}；与 N=400 的最小值位置相同：{comparison['min_center_separation_same_strength']}。最大相邻间隔变化为 {fmt(summary['max_adjacent_center_separation_change'])}。",
        "",
        f"同谱秩得分的最大尺寸绝对差为 {fmt(comparison['max_diagonal_score_absolute_difference'])}，中心间隔的最大尺寸绝对差为 {fmt(comparison['max_center_separation_absolute_difference'])}。",
        "",
        f"N=600 最近对联合诊断通过强度为 {summary['pair0_joint_pass_strengths']}；次近对通过强度为 {summary['pair1_joint_pass_strengths']}。这些既有诊断不构成体 winding 证明。",
        "",
        "细化提高各尺寸内部的可辨识性，但方向一致不是尺寸不变性，也不是连续路径、谱交叉、避免交叉、真实态追踪、次近对拓扑性或体 winding 证明。原类别和此前计数未改变。",
        "",
        "复现：`python research/floquet-bdg-tbc/analyze_n600_path.py`。N=600 的10点8链接、参考误差和 N=400 指标对照保存在 `n600_path_analysis.json`。",
        "",
    ]
    (ROOT / "N600_PATH.md").write_text("\n".join(lines), encoding="utf-8")


def main():
    if "--check-only" in sys.argv:
        stored = json.loads((ROOT / "n600_path_analysis.json").read_text(encoding="utf-8"))
        expected = {
            "protocol_sha256": sha(PROTOCOL), "source_sha256": sha(SOURCE),
            "n400_source_sha256": sha(N400_SOURCE), "coarse_source_sha256": sha(COARSE),
            "candidate_source_sha256": sha(CANDIDATE),
        }
        if any(stored.get(key) != value for key, value in expected.items()):
            raise ValueError("N=600 path evidence is stale")
        if len(stored.get("regions", [])) != 2 or stored.get("new_parameter_points") != 9:
            raise ValueError("N=600 path evidence has wrong scope")
        print(json.dumps({"check_only": True, "regions": 2, "new_parameter_points": 9, "all_passed": True}, ensure_ascii=False))
        return 0
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    n400_source = json.loads(N400_SOURCE.read_text(encoding="utf-8"))
    coarse = json.loads(COARSE.read_text(encoding="utf-8"))
    candidate = json.loads(CANDIDATE.read_text(encoding="utf-8"))
    if not json.loads(OLD_INDEPENDENT.read_text(encoding="utf-8")).get("all_passed"):
        raise ValueError("Original independent profile verification has not passed")
    if not json.loads(NEW_INDEPENDENT.read_text(encoding="utf-8")).get("all_passed"):
        raise ValueError("New-cell independent profile verification has not passed")
    n, seed = protocol["n"], protocol["seed"]
    stored = source_cell(source, n, protocol["reference_strength"], seed)
    computed, bases, reference_errors = {}, {}, {}
    for strengths in protocol["regions"].values():
        for strength in strengths:
            if strength in computed:
                continue
            point, full_pairs, pair_bases = compute_point(n, strength, seed)
            computed[strength] = point
            bases[strength] = pair_bases
            if strength == protocol["reference_strength"]:
                for pair in full_pairs:
                    old = stored["pairs"][pair["pair_index"]]
                    error = {
                        "stored_profile_sha256": old["profile_sha256"],
                        "max_profile_absolute_error": float(np.max(np.abs(np.asarray(pair["profile"]) - np.asarray(old["profile"])))),
                        "edge_weight_absolute_error": abs(pair["edge_weight"] - old["edge_weight"]),
                        "stored_distance_max_absolute_error": max(abs(a - b) for a, b in zip(pair["distances"], old["distances"])),
                        "separation_ratio_absolute_error": abs(pair["max_separation_ratio"] - old["max_separation_ratio"]),
                        "joint_pass_matches": pair["diagnostic_joint_pass"] == old["diagnostic_joint_pass"],
                    }
                    if max(error["max_profile_absolute_error"], error["edge_weight_absolute_error"], error["stored_distance_max_absolute_error"], error["separation_ratio_absolute_error"]) > 1e-10 or not error["joint_pass_matches"]:
                        raise ValueError("N=600 reference cell does not reproduce frozen evidence")
                    reference_errors[str(pair["pair_index"])] = error
    max_error = max((value for error in reference_errors.values() for key, value in error.items() if key not in ("stored_profile_sha256", "joint_pass_matches")), default=0.0)
    regions = []
    for label, strengths in protocol["regions"].items():
        points = [computed[strength] for strength in strengths]
        links = [adjacent_link(points[index], points[index + 1], bases[strengths[index]], bases[strengths[index + 1]]) for index in range(4)]
        regions.append({"label": label, "points": points, "links": links, "summary": summarize(points, links)})
        print(json.dumps({"completed_region": label, "summary": regions[-1]["summary"], "assignments": [link["dominant_assignment"] for link in links]}, ensure_ascii=False), flush=True)
    all_points = [point for region in regions for point in region["points"]]
    all_links = [link for region in regions for link in region["links"]]
    summary = summarize(all_points, all_links)
    n400_links = [link for region in n400_source["regions"] for link in region["links"]]
    n400_points = [point for region in n400_source["regions"] for point in region["points"]]
    max_link = max(all_links, key=lambda link: abs(link["center_separation_after"] - link["center_separation_before"]))
    old_max_link = max(n400_links, key=lambda link: abs(link["center_separation_after"] - link["center_separation_before"]))
    comparison = {
        "assignment_agreement_count": sum(new["dominant_assignment"] == old["dominant_assignment"] for new, old in zip(all_links, n400_links)),
        "min_center_separation_same_strength": summary["min_center_separation_strength"] == n400_source["summary"]["min_center_separation_strength"],
        "max_change_same_link": (max_link["from"], max_link["to"]) == (old_max_link["from"], old_max_link["to"]),
        "max_diagonal_score_absolute_difference": max(abs(new["diagonal_score"] - old["diagonal_score"]) for new, old in zip(all_links, n400_links)),
        "max_center_separation_absolute_difference": max(abs(new["center_separation"] - old["center_separation"]) for new, old in zip(all_points, n400_points)),
        "max_change_link": {"from": max_link["from"], "to": max_link["to"]},
    }
    new_strengths = sorted({point["strength"] for point in all_points} - {protocol["reference_strength"]})
    data = {
        "schema": "floquet-bdg-n600-path-analysis-v1", "analysis_date": protocol["analysis_date"],
        "protocol_sha256": sha(PROTOCOL), "source_sha256": sha(SOURCE), "n400_source_sha256": sha(N400_SOURCE),
        "coarse_source_sha256": sha(COARSE), "candidate_source_sha256": sha(CANDIDATE),
        "original_independent_source_sha256": sha(OLD_INDEPENDENT), "new_independent_source_sha256": sha(NEW_INDEPENDENT),
        "new_parameter_points": len(new_strengths), "new_unique_strengths": new_strengths, "new_seed_count": 0,
        "fixed_random_stream": True, "adaptive_refinement_only": True, "discrete_path": True,
        "new_winding_computed": False, "n640_computed": False, "size_invariance_claim": False,
        "continuous_path_proof": False, "spectral_crossing_proven": False,
        "avoided_crossing_claim": False, "state_exchange_proven": False, "second_pair_topological_claim": False,
        "new_taxonomy_claim": False, "categories_changed": False, "universal_mechanism_claim": False,
        "original_category_counts": source["category_counts"], "regions": regions, "n400_regions": n400_source["regions"],
        "summary": summary, "size_comparison": comparison, "reference_errors": reference_errors,
        "max_reference_error": max_error,
        "previous_candidate_center_separations": [cell["center_separation"] for cell in candidate["cells"]],
    }
    (ROOT / "n600_path_analysis.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    figure(data)
    markdown(data)
    print(json.dumps({"summary": summary, "size_comparison": comparison, "new_unique_strengths": new_strengths, "max_reference_error": max_error}, ensure_ascii=False, indent=2))
    print("generated n600_path_analysis.json n600-path.png N600_PATH.md")


if __name__ == "__main__":
    main()
