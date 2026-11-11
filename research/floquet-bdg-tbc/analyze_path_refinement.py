"""Refine only the two regions identified by the preregistered coarse fixed-N path."""

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

PROTOCOL = ROOT / "path_refinement_protocol.json"
SOURCE = ROOT / "fixed_n_path_analysis.json"
CANDIDATE = ROOT / "swap_candidate_spectrum_analysis.json"
CATEGORY_SOURCE = ROOT / "repeated_category_analysis.json"
OLD_INDEPENDENT = ROOT / "multi_seed_independent.json"
NEW_INDEPENDENT = ROOT / "category_new_cells_independent.json"
TITLES = {"max_change": "最大变化链接细化", "minimum_region": "最小间隔邻域细化"}
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
    }


def fmt(value):
    return f"{value:.6g}"


def figure(data):
    fig, axes = plt.subplots(2, 2, figsize=(13, 9.2), constrained_layout=False)
    for row_index, region in enumerate(data["regions"]):
        points, links = region["points"], region["links"]
        strengths = [point["strength"] for point in points]
        axes[row_index, 0].semilogy(strengths, [point["center_separation"] for point in points], marker="o", color="#6F7F92")
        minimum = min(points, key=lambda row: row["center_separation"])
        axes[row_index, 0].annotate(f"最小 {minimum['center_separation']:.3e}", (minimum["strength"], minimum["center_separation"]), xytext=(6, 7), textcoords="offset points", fontsize=8)
        axes[row_index, 0].set_ylabel("两对中心间隔")
        axes[row_index, 0].set_title(TITLES[region["label"]] + "：中心间隔")
        midpoints = [(link["from"] + link["to"]) / 2 for link in links]
        for key, label, color in (("diagonal_score", "同谱秩", "#356A64"), ("swapped_score", "交换", "#A25B3F")):
            axes[row_index, 1].semilogy(midpoints, [link[key] for link in links], marker="o", color=color, label=label)
        axes[row_index, 1].set_ylabel("相邻子空间平均重叠")
        axes[row_index, 1].set_title(TITLES[region["label"]] + "：分配得分")
        axes[row_index, 1].legend(frameon=False)
        for column in (0, 1):
            axis = axes[row_index, column]
            axis.axvline(0.05 if region["label"] == "max_change" else 0.0425, color="#888888", lw=0.8, ls="--")
            axis.set_xlabel("无序强度 r")
            axis.grid(alpha=0.2, which="both")
    fig.subplots_adjust(top=0.88, bottom=0.11, left=0.08, right=0.97, hspace=0.43, wspace=0.28)
    fig.suptitle("N=400，seed=6：只细化粗路径识别的两个邻域", fontsize=16, y=0.97)
    fig.savefig(ROOT / "path-refinement.png", bbox_inches="tight")
    plt.close(fig)


def markdown(data):
    summary = data["summary"]
    lines = [
        "# Floquet-BdG 参数路径定向细化",
        "",
        "> 日期：2026-11-11。N=400、seed=6、固定随机流。只细化粗路径已识别的最大变化链接与最小间隔邻域，不新增类别、不补算体 winding，未计算 N=640。",
        "",
        "## 一、细化协议与粗点复核",
        "",
        "最大变化区使用 r=0.050000、0.050625、0.051250、0.051875、0.052500；最小间隔区使用 r=0.040000、0.041250、0.042500、0.043750、0.045000。新增唯一点共5个，8条细分链接。",
        "",
        f"五个粗网格旧点的中心、距离、分离比、端点权重和诊断标志均复核，最大数值误差为 {data['max_reference_error']:.3e}。",
        "",
    ]
    for region in data["regions"]:
        lines += [
            f"## 二、{TITLES[region['label']]}",
            "",
            "| r | 最近对中心 | 次近对中心 | 中心间隔 |",
            "|---:|---:|---:|---:|",
        ]
        for point in region["points"]:
            lines.append(f"| {point['strength']} | {fmt(point['pairs'][0]['center'])} | {fmt(point['pairs'][1]['center'])} | {fmt(point['center_separation'])} |")
        lines += [
            "",
            "| 从 r | 到 r | 同谱秩得分 | 交换得分 | 主导分配 |",
            "|---:|---:|---:|---:|:---|",
        ]
        for link in region["links"]:
            lines.append(f"| {link['from']} | {link['to']} | {fmt(link['diagonal_score'])} | {fmt(link['swapped_score'])} | {link['dominant_assignment']} |")
        region_summary = region["summary"]
        lines += [
            "",
            f"本区域最小中心间隔为 {fmt(region_summary['min_center_separation'])}，位于 r={region_summary['min_center_separation_strength']}；最大相邻间隔变化为 {fmt(region_summary['max_adjacent_center_separation_change'])}。",
            "",
        ]
    lines += [
        "图 1 插入位置：两个区域的数值表之后、汇总结论之前。",
        "",
        "![图 1：参数路径定向细化](path-refinement.png)",
        "",
        "**图 1**　上排为最大变化链接，下排为最小间隔邻域；左侧为中心间隔，右侧为相邻分配得分。",
        "",
        "## 三、细化后的结论与边界",
        "",
        f"8条细分链接中，同谱秩占优 {summary['diagonal_link_count']}，交换占优 {summary['swapped_link_count']}，精确并列 {summary['tie_link_count']}。",
        "",
        f"全部细化点的最小中心间隔为 {fmt(summary['min_center_separation'])}，位于 r={summary['min_center_separation_strength']}；最大相邻间隔变化为 {fmt(summary['max_adjacent_center_separation_change'])}。",
        "",
        f"最大变化区的同谱秩得分范围为 {fmt(min(link['diagonal_score'] for link in data['regions'][0]['links']))}–{fmt(max(link['diagonal_score'] for link in data['regions'][0]['links']))}，最小间隔邻域为 {fmt(min(link['diagonal_score'] for link in data['regions'][1]['links']))}–{fmt(max(link['diagonal_score'] for link in data['regions'][1]['links']))}。细步长提高了同 N 对应的可辨识性。",
        "",
        "粗网格上的较大跳变在细化后分解为较小变化，且没有交换占优，因此粗步长跳变不是谱交叉证明。离散网格的最小值也不是连续极值；最小间隔位置从0.0425移动到新增点0.04125，只说明当前离散网格的实测最小值位置。",
        "",
        "细化只提高这两个邻域的分辨率，不把有限步长外推为连续路径不变性。若出现交换分配链接，它只是进一步细化候选；若没有，也不构成避免交叉证明。",
        "",
        "本轮没有证明连续路径、谱交叉、避免交叉、真实态追踪、次近对拓扑性或体 winding。原类别和此前计数未改变。",
        "",
        "复现：`python research/floquet-bdg-tbc/analyze_path_refinement.py`。两个区域、10个细化点、8条链接和粗点复核保存在 `path_refinement_analysis.json`。",
        "",
    ]
    (ROOT / "PATH_REFINEMENT.md").write_text("\n".join(lines), encoding="utf-8")


def main():
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    candidate = json.loads(CANDIDATE.read_text(encoding="utf-8"))
    category_source = json.loads(CATEGORY_SOURCE.read_text(encoding="utf-8"))
    if not json.loads(OLD_INDEPENDENT.read_text(encoding="utf-8")).get("all_passed"):
        raise ValueError("Original independent profile verification has not passed")
    if not json.loads(NEW_INDEPENDENT.read_text(encoding="utf-8")).get("all_passed"):
        raise ValueError("New-cell independent profile verification has not passed")
    n, seed = protocol["n"], protocol["seed"]
    computed, bases, reference_errors = {}, {}, {}
    for label, strengths in protocol["regions"].items():
        for strength in strengths:
            if strength in computed:
                continue
            point, full_pairs, pair_bases = compute_point(n, strength, seed)
            computed[strength] = point
            bases[strength] = pair_bases
            old_point = next((row for row in source["path"] if row["strength"] == strength), None)
            if old_point is not None:
                pair_errors = {}
                for pair in full_pairs:
                    old = old_point["pairs"][pair["pair_index"]]
                    pair_errors[str(pair["pair_index"])] = {
                        "coarse_center": old["center"],
                        "center_absolute_error": abs(pair["center"] - old["center"]),
                        "distance_max_absolute_error": max(abs(a - b) for a, b in zip(pair["distances"], old["distances"])),
                        "separation_ratio_absolute_error": abs(pair["max_separation_ratio"] - old["max_separation_ratio"]),
                        "edge_weight_absolute_error": abs(pair["edge_weight"] - old["edge_weight"]),
                        "joint_pass_matches": pair["diagnostic_joint_pass"] == old["diagnostic_joint_pass"],
                    }
                reference_errors[str(strength)] = pair_errors
    numeric_errors = [value for errors in reference_errors.values() for error in errors.values() for key, value in error.items() if key != "joint_pass_matches" and key != "coarse_center"]
    max_error = max(numeric_errors, default=0.0)
    if max_error > 1e-10 or any(not error["joint_pass_matches"] for errors in reference_errors.values() for error in errors.values()):
        raise ValueError("Coarse reference points were not reproduced")
    regions = []
    for label, strengths in protocol["regions"].items():
        points = [computed[strength] for strength in strengths]
        links = [adjacent_link(points[index], points[index + 1], bases[strengths[index]], bases[strengths[index + 1]]) for index in range(4)]
        regions.append({"label": label, "points": points, "links": links, "summary": summarize(points, links)})
        print(json.dumps({"completed_region": label, "summary": regions[-1]["summary"], "assignments": [link["dominant_assignment"] for link in links]}, ensure_ascii=False), flush=True)
    all_points = [point for region in regions for point in region["points"]]
    all_links = [link for region in regions for link in region["links"]]
    coarse_strengths = {row["strength"] for row in source["path"]}
    new_points = sorted({point["strength"] for point in all_points} - coarse_strengths)
    data = {
        "schema": "floquet-bdg-path-refinement-analysis-v1", "analysis_date": protocol["analysis_date"],
        "protocol_sha256": sha(PROTOCOL), "source_sha256": sha(SOURCE), "candidate_source_sha256": sha(CANDIDATE),
        "original_independent_source_sha256": sha(OLD_INDEPENDENT), "new_independent_source_sha256": sha(NEW_INDEPENDENT),
        "new_parameter_points": len(new_points), "new_unique_strengths": new_points, "new_seed_count": 0,
        "fixed_random_stream": True, "adaptive_refinement_only": True,
        "new_winding_computed": False, "n640_computed": False,
        "continuous_path_proof": False, "spectral_crossing_proven": False,
        "avoided_crossing_claim": False, "state_exchange_proven": False, "second_pair_topological_claim": False,
        "new_taxonomy_claim": False, "categories_changed": False, "universal_mechanism_claim": False,
        "original_category_counts": category_source["category_counts"],
        "regions": regions, "summary": summarize(all_points, all_links),
        "reference_errors": reference_errors, "max_reference_error": max_error,
        "previous_candidate_center_separations": [cell["center_separation"] for cell in candidate["cells"]],
    }
    (ROOT / "path_refinement_analysis.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    figure(data)
    markdown(data)
    print(json.dumps({"summary": data["summary"], "new_unique_strengths": new_points, "max_reference_error": max_error}, ensure_ascii=False, indent=2))
    print("generated path_refinement_analysis.json path-refinement.png PATH_REFINEMENT.md")


if __name__ == "__main__":
    main()
