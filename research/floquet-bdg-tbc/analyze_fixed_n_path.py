"""Track same-N Floquet subspaces along a preregistered discrete strength path."""

import hashlib
import json
from pathlib import Path
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / "floquet-bdg-convention"))
sys.path.insert(0, str(ROOT.parent / "floquet-bdg-disorder"))
from convention_model import quasienergy_spectrum  # noqa: E402
from disorder_model import disordered_floquet  # noqa: E402
sys.path.insert(0, str(ROOT))
from analyze_endpoint_subspaces import pair_metrics  # noqa: E402
from analyze_subspace_overlap import overlap_entry, source_cell  # noqa: E402

PROTOCOL = ROOT / "fixed_n_path_protocol.json"
SOURCE = ROOT / "repeated_category_analysis.json"
CANDIDATE = ROOT / "swap_candidate_spectrum_analysis.json"
OLD_INDEPENDENT = ROOT / "multi_seed_independent.json"
NEW_INDEPENDENT = ROOT / "category_new_cells_independent.json"
plt.rcParams.update({
    "font.sans-serif": ["Microsoft YaHei", "SimHei", "Noto Sans CJK SC", "DejaVu Sans"],
    "axes.unicode_minus": False, "font.size": 10, "figure.dpi": 160,
})


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compute_point(n, strength, seed):
    beta = np.random.default_rng(20261111 + seed).random(n)
    u, period = disordered_floquet(n, 2.5, beta, strength, 7.0, 1.0, 1.0)
    spectrum = quasienergy_spectrum(u, period)
    distances = np.abs(spectrum["eigenvalues"] - 1.0)
    order = np.argsort(distances)
    pairs, bases = [], []
    for pair_index in (0, 1):
        indices = order[2 * pair_index:2 * pair_index + 2]
        metrics = pair_metrics(spectrum, n, indices, pair_index)
        pair_distances = metrics["distances"]
        pairs.append({
            "pair_index": pair_index, "distances": pair_distances,
            "center": float(np.mean(pair_distances)), "within_distance_difference": abs(pair_distances[1] - pair_distances[0]),
            "max_separation_ratio": metrics["max_separation_ratio"], "edge_weight": metrics["edge_weight"],
            "L50": metrics["L50"], "diagnostic_joint_pass": metrics["diagnostic_joint_pass"],
            "profile_sha256": metrics["profile_sha256"], "profile": metrics["profile"],
        })
        bases.append(spectrum["eigenvectors"][:, indices])
    center_separation = abs(pairs[1]["center"] - pairs[0]["center"])
    point = {
        "strength": strength, "pairs": [{key: value for key, value in pair.items() if key != "profile"} for pair in pairs],
        "spectrum_first_six": [float(distances[index]) for index in order[:6]],
        "center_separation": center_separation,
        "center_separation_ratio": center_separation / max(pair["center"] for pair in pairs),
    }
    return point, pairs, bases


def adjacent_link(first, second, bases_first, bases_second):
    q_first = [np.linalg.qr(basis, mode="reduced")[0] for basis in bases_first]
    q_second = [np.linalg.qr(basis, mode="reduced")[0] for basis in bases_second]
    matrix = [[overlap_entry(q_first[i], q_second[j]) for j in range(2)] for i in range(2)]
    diagonal = (matrix[0][0]["overlap"] + matrix[1][1]["overlap"]) / 2
    swapped = (matrix[0][1]["overlap"] + matrix[1][0]["overlap"]) / 2
    return {
        "from": first["strength"], "to": second["strength"],
        "overlap_matrix": matrix, "diagonal_score": diagonal, "swapped_score": swapped,
        "dominant_assignment": "diagonal" if diagonal > swapped else "swapped" if swapped > diagonal else "tie_exact",
        "center_separation_before": first["center_separation"], "center_separation_after": second["center_separation"],
    }


def fmt(value):
    return f"{value:.6g}"


def figure(data):
    fig, axes = plt.subplots(2, 2, figsize=(13, 9.2), constrained_layout=False)
    strengths = [row["strength"] for row in data["path"]]
    for pair_index, color in ((0, "#356A64"), (1, "#A25B3F")):
        axes[0, 0].plot(strengths, [row["pairs"][pair_index]["center"] for row in data["path"]], marker="o", color=color, label=f"第{pair_index+1}对中心")
        axes[1, 0].semilogy(strengths, [row["pairs"][pair_index]["max_separation_ratio"] for row in data["path"]], marker="o", color=color, label=f"第{pair_index+1}对")
    axes[0, 0].set_yscale("log")
    axes[0, 0].set_ylabel("谱距离中心")
    axes[0, 0].set_title("两对中心随强度变化")
    axes[0, 0].legend(frameon=False)
    axes[1, 0].set_ylabel("既有分离比")
    axes[1, 0].set_title("次近对分离比保持为1")
    axes[1, 0].legend(frameon=False)
    axes[0, 1].semilogy(strengths, [row["center_separation"] for row in data["path"]], marker="o", color="#6F7F92")
    minimum = min(data["path"], key=lambda row: row["center_separation"])
    axes[0, 1].annotate(f"最小 {minimum['center_separation']:.3e}", (minimum["strength"], minimum["center_separation"]), xytext=(8, 8), textcoords="offset points", fontsize=8)
    axes[0, 1].set_ylabel("两对中心间隔")
    axes[0, 1].set_title("中心间隔非零，但离散步长有限")
    midpoints = [(link["from"] + link["to"]) / 2 for link in data["links"]]
    for key, label, color in (("diagonal_score", "同谱秩分配", "#356A64"), ("swapped_score", "交换分配", "#A25B3F")):
        axes[1, 1].semilogy(midpoints, [link[key] for link in data["links"]], marker="o", color=color, label=label)
    axes[1, 1].set_ylabel("相邻子空间平均重叠")
    axes[1, 1].set_title("相邻链接的分配得分")
    axes[1, 1].legend(frameon=False)
    for axis in axes.flat:
        axis.axvline(0.05, color="#888888", lw=0.8, ls="--")
        axis.set_xlabel("无序强度 r")
        axis.grid(alpha=0.2, which="both")
    fig.subplots_adjust(top=0.88, bottom=0.11, left=0.08, right=0.97, hspace=0.42, wspace=0.28)
    fig.suptitle("N=400，seed=6：固定随机流的离散参数路径", fontsize=16, y=0.97)
    fig.savefig(ROOT / "fixed-n-path.png", bbox_inches="tight")
    plt.close(fig)


def markdown(data):
    summary = data["summary"]
    lines = [
        "# Floquet-BdG 固定尺寸离散参数路径",
        "",
        "> 日期：2026-11-11。N=400、seed=6、固定随机流；r=0.040–0.060 共9个预登记点、8条相邻链接。不新增类别、不补算体 winding，未计算 N=640。",
        "",
        "## 一、路径与复核协议",
        "",
        "所有强度点使用同一个 beta 随机流，因此变化只来自模型中的无序强度。相同 N 的二维子空间直接 QR 后比较，不再需要跨尺寸插值。",
        "",
        "r=0.050 必须复现原冻结剖面、端点权重、谱距离和分离比，容差1e-10只用于复现，不是近简并或交叉阈值。",
        "",
        f"参考点最大剖面误差 {data['max_reference_profile_absolute_error']:.3e}，最大谱距离误差 {data['max_reference_distance_absolute_error']:.3e}。",
        "",
        "## 二、逐点谱结构",
        "",
        "| r | 最近对中心 | 次近对中心 | 中心间隔 | 最近对分离比 | 次近对分离比 | 最近对诊断 | 次近对诊断 |",
        "|---:|---:|---:|---:|---:|---:|:---:|:---:|",
    ]
    for point in data["path"]:
        lines.append(f"| {point['strength']} | {fmt(point['pairs'][0]['center'])} | {fmt(point['pairs'][1]['center'])} | {fmt(point['center_separation'])} | {fmt(point['pairs'][0]['max_separation_ratio'])} | {fmt(point['pairs'][1]['max_separation_ratio'])} | {point['pairs'][0]['diagnostic_joint_pass']} | {point['pairs'][1]['diagnostic_joint_pass']} |")
    lines += [
        "",
        "## 三、相邻子空间重叠",
        "",
        "| 从 r | 到 r | 同谱秩得分 | 交换得分 | 主导分配 | 中心间隔变化 |",
        "|---:|---:|---:|---:|:---|---:|",
    ]
    for link in data["links"]:
        lines.append(f"| {link['from']} | {link['to']} | {fmt(link['diagonal_score'])} | {fmt(link['swapped_score'])} | {link['dominant_assignment']} | {fmt(link['center_separation_after'] - link['center_separation_before'])} |")
    lines += [
        "",
        "图 1 插入位置：相邻链接表之后、结论之前。",
        "",
        "![图 1：固定尺寸离散参数路径](fixed-n-path.png)",
        "",
        "**图 1**　固定随机流下，谱中心、中心间隔、既有分离比和相邻重叠随强度的变化。虚线为原参考点 r=0.050。",
        "",
        "## 四、结论与边界",
        "",
        f"8条链接中，同谱秩分配占优 {summary['diagonal_link_count']}，交换分配占优 {summary['swapped_link_count']}，精确并列 {summary['tie_link_count']}。本网格没有交换分配链接。",
        "",
        f"同尺寸相邻重叠的范围为 {fmt(min(link['diagonal_score'] for link in data['links']))}–{fmt(max(link['diagonal_score'] for link in data['links']))}，高于此前跨尺寸弱重叠，说明同 N 的态对应更可辨识；但8个离散链接仍不等于连续态追踪。",
        "",
        f"最小中心间隔为 {fmt(summary['min_center_separation'])}，出现在 r={summary['min_center_separation_strength']}；相邻中心间隔最大绝对变化为 {fmt(summary['max_adjacent_center_separation_change'])}。",
        "",
        f"最近对 profile 联合诊断通过的强度为 {summary['pair0_joint_pass_strengths']}；次近对通过强度为 {summary['pair1_joint_pass_strengths']}。这些既有诊断不构成体 winding 证明。",
        "",
        "离散路径上的交换分配链接只能作为细化候选，不能直接称为真实态交换或避免交叉。即使所有链接同谱秩，也不能把有限步长外推为连续路径不变性。",
        "",
        "本轮没有证明连续路径、谱交叉、避免交叉、真实态追踪、次近对拓扑性或体 winding。原类别和此前计数未改变。",
        "",
        "复现：`python research/floquet-bdg-tbc/analyze_fixed_n_path.py`。9个参数点、8条重叠链接和来源哈希保存在 `fixed_n_path_analysis.json`。",
        "",
    ]
    (ROOT / "FIXED_N_PATH.md").write_text("\n".join(lines), encoding="utf-8")


def main():
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    candidate = json.loads(CANDIDATE.read_text(encoding="utf-8"))
    if not json.loads(OLD_INDEPENDENT.read_text(encoding="utf-8")).get("all_passed"):
        raise ValueError("Original independent profile verification has not passed")
    if not json.loads(NEW_INDEPENDENT.read_text(encoding="utf-8")).get("all_passed"):
        raise ValueError("New-cell independent profile verification has not passed")
    n, seed = protocol["n"], protocol["seed"]
    stored = source_cell(source, n, protocol["reference_strength"], seed)
    path, bases, reference_errors = [], [], {}
    for strength in protocol["strengths"]:
        point, full_pairs, pair_bases = compute_point(n, strength, seed)
        if strength == protocol["reference_strength"]:
            for pair in full_pairs:
                old = stored["pairs"][pair["pair_index"]]
                profile_error = float(np.max(np.abs(np.asarray(pair["profile"]) - np.asarray(old["profile"]))))
                edge_error = abs(pair["edge_weight"] - old["edge_weight"])
                distance_error = max(abs(pair["distances"][i] - old["distances"][i]) for i in range(2))
                ratio_error = abs(pair["max_separation_ratio"] - old["max_separation_ratio"])
                if max(profile_error, edge_error, distance_error, ratio_error) > 1e-10:
                    raise ValueError("Reference fixed-N cell does not reproduce frozen evidence")
                reference_errors[str(pair["pair_index"])] = {
                    "stored_profile_sha256": old["profile_sha256"], "max_profile_absolute_error": profile_error,
                    "edge_weight_absolute_error": edge_error, "stored_distance_max_absolute_error": distance_error,
                    "separation_ratio_absolute_error": ratio_error,
                }
        path.append(point)
        bases.append(pair_bases)
        print(json.dumps({"completed_strength": strength, "center_separation": point["center_separation"], "pair_centers": [pair["center"] for pair in point["pairs"]]}, ensure_ascii=False), flush=True)
    if set(reference_errors) != {"0", "1"}:
        raise ValueError("Reference errors were not registered")
    links = [adjacent_link(path[index], path[index + 1], bases[index], bases[index + 1]) for index in range(len(path) - 1)]
    assignments = [link["dominant_assignment"] for link in links]
    minimum = min(path, key=lambda row: row["center_separation"])
    changes = [abs(link["center_separation_after"] - link["center_separation_before"]) for link in links]
    summary = {
        "diagonal_link_count": assignments.count("diagonal"), "swapped_link_count": assignments.count("swapped"),
        "tie_link_count": assignments.count("tie_exact"),
        "assignment_sequence": [{"from": link["from"], "to": link["to"], "dominant_assignment": link["dominant_assignment"]} for link in links],
        "min_center_separation": minimum["center_separation"], "min_center_separation_strength": minimum["strength"],
        "max_adjacent_center_separation_change": max(changes),
        "pair0_joint_pass_strengths": [row["strength"] for row in path if row["pairs"][0]["diagnostic_joint_pass"]],
        "pair1_joint_pass_strengths": [row["strength"] for row in path if row["pairs"][1]["diagnostic_joint_pass"]],
    }
    data = {
        "schema": "floquet-bdg-fixed-n-path-analysis-v1", "analysis_date": protocol["analysis_date"],
        "protocol_sha256": sha(PROTOCOL), "source_sha256": sha(SOURCE), "candidate_source_sha256": sha(CANDIDATE),
        "original_independent_source_sha256": sha(OLD_INDEPENDENT), "new_independent_source_sha256": sha(NEW_INDEPENDENT),
        "new_parameter_points": len(path), "new_seed_count": 0, "new_winding_computed": False, "n640_computed": False,
        "fixed_random_stream": True, "discrete_path": True, "continuous_path_proof": False,
        "near_degeneracy_threshold_added": False, "spectral_crossing_proven": False,
        "avoided_crossing_claim": False, "state_exchange_proven": False, "second_pair_topological_claim": False,
        "new_taxonomy_claim": False, "categories_changed": False, "universal_mechanism_claim": False,
        "original_category_counts": source["category_counts"], "path": path, "links": links,
        "summary": summary, "reference_errors": reference_errors,
        "max_reference_profile_absolute_error": max(row["max_profile_absolute_error"] for row in reference_errors.values()),
        "max_reference_distance_absolute_error": max(row["stored_distance_max_absolute_error"] for row in reference_errors.values()),
        "previous_candidate_center_separations": [cell["center_separation"] for cell in candidate["cells"]],
    }
    (ROOT / "fixed_n_path_analysis.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    figure(data)
    markdown(data)
    print(json.dumps({"summary": summary, "max_reference_profile_absolute_error": data["max_reference_profile_absolute_error"], "max_reference_distance_absolute_error": data["max_reference_distance_absolute_error"]}, ensure_ascii=False, indent=2))
    print("generated fixed_n_path_analysis.json fixed-n-path.png FIXED_N_PATH.md")


if __name__ == "__main__":
    main()
