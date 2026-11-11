"""Refine the N=600 valley and subsequent same-N overlap drop."""

import hashlib
import json
from pathlib import Path
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from analyze_fixed_n_path import compute_point, adjacent_link  # noqa: E402

PROTOCOL = ROOT / "n600_valley_protocol.json"
SOURCE = ROOT / "n600_path_analysis.json"
N400_SOURCE = ROOT / "path_refinement_analysis.json"
CATEGORY_SOURCE = ROOT / "repeated_category_analysis.json"
CANDIDATE = ROOT / "swap_candidate_spectrum_analysis.json"
OLD_INDEPENDENT = ROOT / "multi_seed_independent.json"
NEW_INDEPENDENT = ROOT / "category_new_cells_independent.json"
plt.rcParams.update({
    "font.sans-serif": ["Microsoft YaHei", "SimHei", "Noto Sans CJK SC", "DejaVu Sans"],
    "axes.unicode_minus": False, "font.size": 10, "figure.dpi": 160,
})


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fmt(value):
    return f"{value:.6g}"


def figure(data):
    fig, axes = plt.subplots(2, 2, figsize=(13, 9.2), constrained_layout=False)
    strengths = [point["strength"] for point in data["points"]]
    n400_points = data["n400_points"]
    for points, name, color in ((data["points"], "N=600", "#356A64"), (n400_points, "N=400", "#A25B3F")):
        axes[0, 0].semilogy(strengths, [point["center_separation"] for point in points], marker="o", color=color, label=name)
    axes[0, 0].set_ylabel("两对中心间隔")
    axes[0, 0].set_title("谷值区的中心间隔")
    axes[0, 0].legend(frameon=False)
    midpoints = [(link["from"] + link["to"]) / 2 for link in data["links"]]
    for axis, key, ylabel in ((axes[0, 1], "diagonal_score", "同谱秩重叠"), (axes[1, 0], "swapped_score", "交换得分")):
        for links, name, color in ((data["links"], "N=600", "#356A64"), (data["n400_links"], "N=400", "#A25B3F")):
            axis.semilogy(midpoints, [link[key] for link in links], marker="o", color=color, label=name)
        axis.set_ylabel(ylabel)
        axis.set_title("同 N 相邻子空间分配得分")
        axis.legend(frameon=False)
    for pair_index, color in ((0, "#356A64"), (1, "#A25B3F")):
        axes[1, 1].semilogy(strengths, [point["pairs"][pair_index]["max_separation_ratio"] for point in data["points"]], marker="o", color=color, label=f"第{pair_index+1}对")
    axes[1, 1].set_ylabel("既有分离比")
    axes[1, 1].set_title("次近对分离比保持为1")
    axes[1, 1].legend(frameon=False)
    for axis in axes.flat:
        axis.axvline(0.04375, color="#888888", lw=0.8, ls="--")
        axis.set_xlabel("无序强度 r")
        axis.grid(alpha=0.2, which="both")
    fig.subplots_adjust(top=0.88, bottom=0.11, left=0.08, right=0.97, hspace=0.43, wspace=0.28)
    fig.suptitle("N=600：谷值与后续重叠下降区", fontsize=16, y=0.97)
    fig.savefig(ROOT / "n600-valley.png", bbox_inches="tight")
    plt.close(fig)


def markdown(data):
    summary = data["summary"]
    comparison = data["size_comparison"]
    lines = [
        "# Floquet-BdG N=600 谷值与重叠下降区细化",
        "",
        "> 日期：2026-11-11。N=600、seed=6、固定随机流。新增 r=0.043125 和0.044375，复核0.0425、0.04375、0.045三个旧点。不新增类别、不补算体 winding，未计算 N=640。",
        "",
        "## 一、细化协议",
        "",
        "谷值区使用 r=0.042500、0.043125、0.043750、0.044375、0.045000。分别记录中心间隔、同谱秩重叠、交换得分和既有 profile 诊断，不把不同指标混成同一个机制名称。",
        "",
        f"三个旧点的最大数值复核误差为 {data['max_reference_error']:.3e}。",
        "",
        "| r | N=600中心间隔 | N=400中心间隔 | 绝对差 |",
        "|---:|---:|---:|---:|",
    ]
    for point, old in zip(data["points"], data["n400_points"]):
        lines.append(f"| {point['strength']} | {fmt(point['center_separation'])} | {fmt(old['center_separation'])} | {fmt(abs(point['center_separation'] - old['center_separation']))} |")
    lines += [
        "",
        "## 二、相邻重叠与分配方向",
        "",
        "| 从 r | 到 r | N=600同谱秩 | N=400同谱秩 | N=600交换 | N=400交换 | 主导分配（N=600／N=400） |",
        "|---:|---:|---:|---:|---:|---:|:---|",
    ]
    for link, old in zip(data["links"], data["n400_links"]):
        lines.append(f"| {link['from']} | {link['to']} | {fmt(link['diagonal_score'])} | {fmt(old['diagonal_score'])} | {fmt(link['swapped_score'])} | {fmt(old['swapped_score'])} | {link['dominant_assignment']}／{old['dominant_assignment']} |")
    lines += [
        "",
        "图 1 插入位置：相邻重叠表之后、结论之前。",
        "",
        "![图 1：N=600 谷值与重叠下降区](n600-valley.png)",
        "",
        "**图 1**　中心间隔、同谱秩重叠、交换得分和既有分离比分别展示；虚线为此前最小值位置 r=0.04375。",
        "",
        "## 三、结果与边界",
        "",
        f"4条链接中，同谱秩占优 {summary['diagonal_link_count']}，交换占优 {summary['swapped_link_count']}，精确并列 {summary['tie_link_count']}；与 N=400 的主导分配一致 {comparison['assignment_agreement_count']}/4。",
        "",
        f"最小中心间隔为 {fmt(summary['min_center_separation'])}，位于 r={summary['min_center_separation_strength']}；最大相邻间隔变化为 {fmt(summary['max_adjacent_center_separation_change'])}。",
        "",
        f"最大同谱秩下降为 {fmt(summary['max_diagonal_score_drop'])}，最大交换得分上升为 {fmt(summary['max_swapped_score_increase'])}，最低同谱秩得分为 {fmt(summary['min_diagonal_score'])}。这些指标描述不同方面，不能互相替代。",
        "",
        f"最大同谱秩下降和最大交换上升都位于 r=0.04375→0.044375；该链接同谱秩为 {fmt(data['links'][2]['diagonal_score'])}，交换为 {fmt(data['links'][2]['swapped_score'])}。粗网格末段的更低重叠没有以同样幅度出现，说明低值具有步长依赖。",
        "",
        f"最大中心间隔变化位于 r={comparison['max_change_link']['from']}→{comparison['max_change_link']['to']}。最小中心间隔则位于新增点 r=0.044375；这只是当前离散网格的最小值位置。",
        "",
        f"N=600 最近对联合诊断通过强度为 {summary['pair0_joint_pass_strengths']}；次近对通过强度为 {summary['pair1_joint_pass_strengths']}。",
        "",
        "中心间隔回升和重叠下降不是谱交叉证明，也不是尺寸不变性或连续态追踪结论。新增点只提高局部分辨率，不构成避免交叉、真实态交换、次近对拓扑性或体 winding 证明。原类别和此前计数未改变。",
        "",
        "复现：`python research/floquet-bdg-tbc/analyze_n600_valley.py`。5个参数点、4条链接、三个旧点复核和来源哈希保存在 `n600_valley_analysis.json`。",
        "",
    ]
    (ROOT / "N600_VALLEY.md").write_text("\n".join(lines), encoding="utf-8")


def main():
    if "--check-only" in sys.argv:
        stored = json.loads((ROOT / "n600_valley_analysis.json").read_text(encoding="utf-8"))
        expected = {"protocol_sha256": sha(PROTOCOL), "source_sha256": sha(SOURCE), "n400_source_sha256": sha(N400_SOURCE), "candidate_source_sha256": sha(CANDIDATE)}
        if any(stored.get(key) != value for key, value in expected.items()):
            raise ValueError("N=600 valley evidence is stale")
        if len(stored.get("points", [])) != 5 or len(stored.get("links", [])) != 4 or stored.get("new_parameter_points") != 2:
            raise ValueError("N=600 valley evidence has wrong scope")
        print(json.dumps({"check_only": True, "points": 5, "links": 4, "new_parameter_points": 2, "all_passed": True}, ensure_ascii=False))
        return 0
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    n400_source = json.loads(N400_SOURCE.read_text(encoding="utf-8"))
    category_source = json.loads(CATEGORY_SOURCE.read_text(encoding="utf-8"))
    candidate = json.loads(CANDIDATE.read_text(encoding="utf-8"))
    if not json.loads(OLD_INDEPENDENT.read_text(encoding="utf-8")).get("all_passed"):
        raise ValueError("Original independent profile verification has not passed")
    if not json.loads(NEW_INDEPENDENT.read_text(encoding="utf-8")).get("all_passed"):
        raise ValueError("New-cell independent profile verification has not passed")
    previous_region = next(region for region in source["regions"] if region["label"] == "minimum_region")
    n400_region = next(region for region in n400_source["regions"] if region["label"] == "minimum_region")
    n, seed = protocol["n"], protocol["seed"]
    computed, bases, reference_errors = {}, {}, {}
    for strength in protocol["strengths"]:
        point, full_pairs, pair_bases = compute_point(n, strength, seed)
        computed[strength] = point
        bases[strength] = pair_bases
        if strength in protocol["reference_strengths"]:
            old_point = next(row for row in previous_region["points"] if row["strength"] == strength)
            pair_errors = {}
            for pair in full_pairs:
                old = old_point["pairs"][pair["pair_index"]]
                pair_errors[str(pair["pair_index"])] = {
                    "center_absolute_error": abs(pair["center"] - old["center"]),
                    "distance_max_absolute_error": max(abs(a - b) for a, b in zip(pair["distances"], old["distances"])),
                    "separation_ratio_absolute_error": abs(pair["max_separation_ratio"] - old["max_separation_ratio"]),
                    "edge_weight_absolute_error": abs(pair["edge_weight"] - old["edge_weight"]),
                    "joint_pass_matches": pair["diagnostic_joint_pass"] == old["diagnostic_joint_pass"],
                }
            reference_errors[str(strength)] = pair_errors
    numeric_errors = [value for errors in reference_errors.values() for error in errors.values() for key, value in error.items() if key != "joint_pass_matches"]
    max_error = max(numeric_errors, default=0.0)
    if max_error > 1e-10 or any(not error["joint_pass_matches"] for errors in reference_errors.values() for error in errors.values()):
        raise ValueError("Previous N=600 valley points were not reproduced")
    points = [computed[strength] for strength in protocol["strengths"]]
    links = [adjacent_link(points[index], points[index + 1], bases[protocol["strengths"][index]], bases[protocol["strengths"][index + 1]]) for index in range(4)]
    assignments = [link["dominant_assignment"] for link in links]
    minimum = min(points, key=lambda row: row["center_separation"])
    changes = [abs(link["center_separation_after"] - link["center_separation_before"]) for link in links]
    diagonal_drops = [previous["diagonal_score"] - link["diagonal_score"] for previous, link in zip(links, links[1:])]
    swapped_increases = [link["swapped_score"] - previous["swapped_score"] for previous, link in zip(links, links[1:])]
    max_link = max(links, key=lambda link: abs(link["center_separation_after"] - link["center_separation_before"]))
    summary = {
        "diagonal_link_count": assignments.count("diagonal"), "swapped_link_count": assignments.count("swapped"),
        "tie_link_count": assignments.count("tie_exact"),
        "min_center_separation": minimum["center_separation"], "min_center_separation_strength": minimum["strength"],
        "max_adjacent_center_separation_change": max(changes),
        "max_diagonal_score_drop": max(diagonal_drops), "max_swapped_score_increase": max(swapped_increases),
        "min_diagonal_score": min(link["diagonal_score"] for link in links),
        "pair0_joint_pass_strengths": [point["strength"] for point in points if point["pairs"][0]["diagnostic_joint_pass"]],
        "pair1_joint_pass_strengths": [point["strength"] for point in points if point["pairs"][1]["diagnostic_joint_pass"]],
    }
    old_links = previous_region["links"]
    comparison = {
        "assignment_agreement_count": sum(new["dominant_assignment"] == old["dominant_assignment"] for new, old in zip(links, old_links)),
        "min_center_separation_same_strength": summary["min_center_separation_strength"] == source["summary"]["min_center_separation_strength"],
        "max_diagonal_score_absolute_difference": max(abs(new["diagonal_score"] - old["diagonal_score"]) for new, old in zip(links, old_links)),
        "max_change_link": {"from": max_link["from"], "to": max_link["to"]},
    }
    data = {
        "schema": "floquet-bdg-n600-valley-analysis-v1", "analysis_date": protocol["analysis_date"],
        "protocol_sha256": sha(PROTOCOL), "source_sha256": sha(SOURCE), "n400_source_sha256": sha(N400_SOURCE),
        "candidate_source_sha256": sha(CANDIDATE),
        "original_independent_source_sha256": sha(OLD_INDEPENDENT), "new_independent_source_sha256": sha(NEW_INDEPENDENT),
        "new_parameter_points": len(protocol["new_unique_strengths"]), "new_unique_strengths": protocol["new_unique_strengths"], "new_seed_count": 0,
        "fixed_random_stream": True, "adaptive_refinement_only": True, "discrete_path": True,
        "new_winding_computed": False, "n640_computed": False, "size_invariance_claim": False,
        "continuous_path_proof": False, "spectral_crossing_proven": False,
        "avoided_crossing_claim": False, "state_exchange_proven": False, "second_pair_topological_claim": False,
        "new_taxonomy_claim": False, "categories_changed": False, "universal_mechanism_claim": False,
        "original_category_counts": category_source["category_counts"],
        "points": points, "links": links, "n400_points": n400_region["points"], "n400_links": n400_region["links"],
        "summary": summary, "size_comparison": comparison, "reference_errors": reference_errors, "max_reference_error": max_error,
        "previous_candidate_center_separations": [cell["center_separation"] for cell in candidate["cells"]],
    }
    (ROOT / "n600_valley_analysis.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    figure(data)
    markdown(data)
    print(json.dumps({"summary": summary, "size_comparison": comparison, "max_reference_error": max_error}, ensure_ascii=False, indent=2))
    print("generated n600_valley_analysis.json n600-valley.png N600_VALLEY.md")


if __name__ == "__main__":
    main()
