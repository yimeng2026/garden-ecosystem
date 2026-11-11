"""Fixed-seed refined path for cross-size matrix entries and native adjacent links."""

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
from analyze_matched_beta_control import compute_cell, native_rank, embedded_rank, sha  # noqa: E402
from analyze_subspace_overlap import embedded_orthonormal_basis, overlap_entry  # noqa: E402
from analyze_embedding_robustness import embedded_cell_average_basis  # noqa: E402
from analyze_overlap_confounding import cross_size_result  # noqa: E402
from analyze_fixed_n_path import adjacent_link  # noqa: E402

PROTOCOL = ROOT / "seed6_matrix_path_protocol.json"
BATCH_B = ROOT / "matched_beta_batch_b_analysis.json"
BATCH_C = ROOT / "matched_beta_batch_c_analysis.json"
REPORT_DATE = "2026-11-12"
ENTRIES = ((0, 0), (0, 1), (1, 0), (1, 1))
plt.rcParams.update({
    "font.sans-serif": ["Microsoft YaHei", "SimHei", "Noto Sans CJK SC", "DejaVu Sans"],
    "axes.unicode_minus": False, "font.size": 9, "figure.dpi": 160,
})


def ratio(after, before):
    return after / before if before else None


def evaluate_path(protocol):
    master = np.random.default_rng(20261111 + protocol["seed"]).random(protocol["master_grid"])
    cells, bases_by_key = [], {}
    rank_controls = []
    for strength in protocol["strengths"]:
        for n in protocol["n_values"]:
            beta = master.reshape(n, protocol["master_grid"] // n).mean(axis=1)
            cell, bases = compute_cell(n, beta, strength)
            cell.update({
                "strength": strength, "new_for_path": strength in protocol["interior_strengths"],
                "evidence_role": "new_interior" if strength in protocol["interior_strengths"] else "endpoint_path_control",
            })
            cells.append(cell)
            bases_by_key[(strength, n)] = bases
            rank_controls.append(native_rank(bases, n))
    path_matrices, representation_fidelity = [], []
    max_direction = 0.0
    embeddings = {"linear_point": embedded_orthonormal_basis, "cell_average": embedded_cell_average_basis}
    for strength in protocol["strengths"]:
        for m in protocol["common_grids"]:
            bases = {
                n: {method: [embedding(subspace, m) for subspace in bases_by_key[(strength, n)]] for method, embedding in embeddings.items()}
                for n in protocol["n_values"]
            }
            for method in embeddings:
                grid = cross_size_result(bases[400][method], bases[600][method], m)
                path_matrices.append({"strength": strength, "method": method, **grid})
                for i in range(2):
                    for j in range(2):
                        reverse = overlap_entry(bases[600][method][j], bases[400][method][i])["overlap"]
                        max_direction = max(max_direction, abs(grid["overlap_matrix"][i][j]["overlap"] - reverse))
            for n in protocol["n_values"]:
                for method in embeddings:
                    rank_controls.append(embedded_rank(bases[n][method], n, method, m))
                for pair_index in (0, 1):
                    forward = overlap_entry(bases[n]["linear_point"][pair_index], bases[n]["cell_average"][pair_index])
                    reverse = overlap_entry(bases[n]["cell_average"][pair_index], bases[n]["linear_point"][pair_index])
                    representation_fidelity.append({
                        "strength": strength, "n": n, "pair_index": pair_index, "m": m,
                        "forward": forward["overlap"], "reverse": reverse["overlap"],
                        "direction_absolute_error": abs(forward["overlap"] - reverse["overlap"]),
                        "singular_values": forward["singular_values"], "principal_angles_deg": forward["principal_angles_deg"],
                    })
    return cells, bases_by_key, path_matrices, representation_fidelity, rank_controls, max_direction


def build_links(protocol, cells, bases_by_key, path_matrices):
    links = []
    for n in protocol["n_values"]:
        for first, second in zip(protocol["strengths"][:-1], protocol["strengths"][1:]):
            first_cell = next(cell for cell in cells if cell["strength"] == first and cell["n"] == n)
            second_cell = next(cell for cell in cells if cell["strength"] == second and cell["n"] == n)
            first_bases = [subspace.reshape((2 * n, 2)) for subspace in bases_by_key[(first, n)]]
            second_bases = [subspace.reshape((2 * n, 2)) for subspace in bases_by_key[(second, n)]]
            link = adjacent_link(first_cell, second_cell, first_bases, second_bases)
            link["n"] = n
            link["center_separation_delta"] = second_cell["center_separation"] - first_cell["center_separation"]
            links.append(link)
    method_grid_links, entry_links = [], []
    for first, second in zip(protocol["strengths"][:-1], protocol["strengths"][1:]):
        for method in protocol["methods"]:
            for m in protocol["common_grids"]:
                before = next(row for row in path_matrices if row["strength"] == first and row["method"] == method and row["m"] == m)
                after = next(row for row in path_matrices if row["strength"] == second and row["method"] == method and row["m"] == m)
                entries = {}
                for i, j in ENTRIES:
                    old, new = before["overlap_matrix"][i][j], after["overlap_matrix"][i][j]
                    delta = new["overlap"] - old["overlap"]
                    channels = []
                    for k in range(2):
                        delta_s_squared = new["singular_values"][k] ** 2 - old["singular_values"][k] ** 2
                        channels.append({
                            "channel_index": k, "before_s": old["singular_values"][k], "after_s": new["singular_values"][k],
                            "delta_s_squared": delta_s_squared, "score_contribution": delta_s_squared / 2,
                        })
                    entry = {
                        "from": first, "to": second, "method": method, "m": m,
                        "i": i, "j": j, "entry": f"O{i}{j}",
                        "before_overlap": old["overlap"], "after_overlap": new["overlap"],
                        "delta_overlap": delta, "ratio": ratio(new["overlap"], old["overlap"]),
                        "score_group": "diagonal" if i == j else "swapped", "score_contribution": delta / 2,
                        "singular_channels": channels,
                        "dominant_singular_channel_index": max((0, 1), key=lambda k: abs(channels[k]["score_contribution"])),
                    }
                    entry_links.append(entry)
                    entries[(i, j)] = entry
                diagonal_driver = max(((0, 0), (1, 1)), key=lambda ij: abs(entries[ij]["score_contribution"]))
                swapped_driver = max(((0, 1), (1, 0)), key=lambda ij: abs(entries[ij]["score_contribution"]))
                method_grid_links.append({
                    "from": first, "to": second, "method": method, "m": m,
                    "before_dominant_assignment": before["dominant_assignment"], "after_dominant_assignment": after["dominant_assignment"],
                    "delta_diagonal_score": after["diagonal_score"] - before["diagonal_score"],
                    "delta_swapped_score": after["swapped_score"] - before["swapped_score"],
                    "diagonal_score_ratio": ratio(after["diagonal_score"], before["diagonal_score"]),
                    "swapped_score_ratio": ratio(after["swapped_score"], before["swapped_score"]),
                    "dominant_diagonal_entry": f"O{diagonal_driver[0]}{diagonal_driver[1]}",
                    "dominant_swapped_entry": f"O{swapped_driver[0]}{swapped_driver[1]}",
                })
    return links, method_grid_links, entry_links


def entry_extrema(path_matrices, entry_links):
    extrema = []
    for method in ("linear_point", "cell_average"):
        for i, j in ENTRIES:
            entry_name = f"O{i}{j}"
            points = [row for row in path_matrices if row["method"] == method and row["m"] == 4800]
            values = [(row["strength"], row["overlap_matrix"][i][j]["overlap"]) for row in points]
            minimum = min(values, key=lambda row: row[1])
            maximum = max(values, key=lambda row: row[1])
            links = [row for row in entry_links if row["method"] == method and row["m"] == 4800 and row["entry"] == entry_name]
            jump = max(links, key=lambda row: abs(row["delta_overlap"]))
            extrema.append({
                "method": method, "m": 4800, "entry": entry_name,
                "min": minimum[1], "min_strength": minimum[0], "max": maximum[1], "max_strength": maximum[0],
                "endpoint_delta": values[-1][1] - values[0][1],
                "max_adjacent_absolute_jump": abs(jump["delta_overlap"]),
                "max_jump_from": jump["from"], "max_jump_to": jump["to"],
                "dominant_singular_channel_counts": dict(Counter(row["dominant_singular_channel_index"] for row in links)),
            })
    return extrema


def driver_summary(method_grid_links):
    rows = []
    for method in ("linear_point", "cell_average"):
        for group, entries in (("diagonal", ("O00", "O11")), ("swapped", ("O01", "O10"))):
            links = [row for row in method_grid_links if row["method"] == method and row["m"] == 4800]
            ratios = [row[f"{group}_score_ratio"] for row in links if row[f"{group}_score_ratio"] is not None]
            rows.append({
                "method": method, "m": 4800, "score_group": group,
                "dominant_entry_counts": {entry: sum(row[f"dominant_{group}_entry"] == entry for row in links) for entry in entries},
                "score_ratio_range": [min(ratios), max(ratios)],
            })
    return rows


def link_summary(links):
    summaries = []
    for n in (400, 600):
        rows = [row for row in links if row["n"] == n]
        min_link = min(rows, key=lambda row: row["diagonal_score"])
        max_swap = max(rows, key=lambda row: row["swapped_score"])
        max_center = max(rows, key=lambda row: abs(row["center_separation_delta"]))
        summaries.append({
            "n": n, "link_count": len(rows),
            "assignment_counts": dict(Counter(row["dominant_assignment"] for row in rows)),
            "min_diagonal_score": min_link["diagonal_score"], "min_diagonal_from": min_link["from"], "min_diagonal_to": min_link["to"],
            "max_swapped_score": max_swap["swapped_score"], "max_swapped_from": max_swap["from"], "max_swapped_to": max_swap["to"],
            "max_absolute_center_separation_delta": abs(max_center["center_separation_delta"]),
            "max_center_change_from": max_center["from"], "max_center_change_to": max_center["to"],
        })
    return summaries


def endpoint_binding(cells, path_matrices, batch_b, batch_c):
    max_matrix = 0.0
    max_singular = 0.0
    max_spectrum = 0.0
    for strength, source in ((0.1, batch_b), (0.2, batch_c)):
        source_row = next(row for row in source["realizations"] if row["seed"] == 6 and row["strength"] == strength)
        for method in ("linear_point", "cell_average"):
            for m in (1200, 2400, 4800):
                actual = next(row for row in path_matrices if row["strength"] == strength and row["method"] == method and row["m"] == m)
                expected = next(row for row in source_row["methods"][method]["grids"] if row["m"] == m)
                for i, j in ENTRIES:
                    a = actual["overlap_matrix"][i][j]
                    e = expected["overlap_matrix"][i][j]
                    max_matrix = max(max_matrix, abs(a["overlap"] - e["overlap"]))
                    max_singular = max(max_singular, max(abs(x - y) for x, y in zip(a["singular_values"], e["singular_values"])))
        for n in (400, 600):
            actual_cell = next(cell for cell in cells if cell["strength"] == strength and cell["n"] == n)
            expected_cell = next(cell for cell in source_row["cells"] if cell["n"] == n)
            max_spectrum = max(max_spectrum, max(abs(x - y) for x, y in zip(actual_cell["spectrum_first_six"], expected_cell["spectrum_first_six"])))
    return {
        "max_matrix_absolute_error": max_matrix,
        "max_singular_absolute_error": max_singular,
        "max_spectrum_absolute_error": max_spectrum,
        "endpoint_recomputation_is_not_new_realization": True,
    }


def figure(data):
    strengths = [row["strength"] for row in data["cells"] if row["n"] == 400]
    midpoints = [(first + second) / 2 for first, second in zip(strengths[:-1], strengths[1:])]
    fig, axes = plt.subplots(2, 2, figsize=(14, 9.6))
    for method, color, marker in (("linear_point", "#356A64", "o"), ("cell_average", "#A25B3F", "s")):
        values = [next(row for row in data["path_matrices"] if row["strength"] == strength and row["method"] == method and row["m"] == 4800)["overlap_matrix"][0][0]["overlap"] for strength in strengths]
        axes[0, 0].plot(strengths, values, color=color, marker=marker, label=method)
    axes[0, 0].set_yscale("log")
    axes[0, 0].set_title("O00：同谱秩核心项的路径响应")
    axes[0, 0].set_ylabel("O00（对数）")
    axes[0, 0].legend(frameon=False)
    for (i, j), label, color in (((0, 1), "O01", "#356A64"), ((1, 0), "O10", "#A25B3F")):
        for method, linestyle in (("linear_point", "-"), ("cell_average", "--")):
            values = [next(row for row in data["path_matrices"] if row["strength"] == strength and row["method"] == method and row["m"] == 4800)["overlap_matrix"][i][j]["overlap"] for strength in strengths]
            axes[0, 1].plot(strengths, values, color=color, ls=linestyle, marker="o", ms=4, label=f"{label} {method}")
    axes[0, 1].set_yscale("log")
    axes[0, 1].set_title("O01／O10：交换项具有种子内路径分化")
    axes[0, 1].set_ylabel("重叠（对数）")
    axes[0, 1].legend(frameon=False, fontsize=7)
    for (i, j), entry_label, color in (((0, 0), "O00", "#356A64"), ((0, 1), "O01", "#A25B3F")):
        for k, linestyle in ((0, "-"), (1, "--")):
            values = [next(row for row in data["path_matrices"] if row["strength"] == strength and row["method"] == "linear_point" and row["m"] == 4800)["overlap_matrix"][i][j]["singular_values"][k] ** 2 for strength in strengths]
            axes[1, 0].plot(strengths, values, color=color, ls=linestyle, marker="o", ms=4, label=f"{entry_label} s{k + 1}²")
    axes[1, 0].set_yscale("log")
    axes[1, 0].set_title("线性点值：O00／O01 主奇异通道")
    axes[1, 0].set_ylabel("s_k^2（对数）")
    axes[1, 0].legend(frameon=False, fontsize=8)
    for n, color in ((400, "#356A64"), (600, "#A25B3F")):
        rows = [row for row in data["links"] if row["n"] == n]
        axes[1, 1].plot(midpoints, [row["diagonal_score"] for row in rows], color=color, marker="o", label=f"N={n}同谱秩")
        axes[1, 1].plot(midpoints, [row["swapped_score"] for row in rows], color=color, ls="--", marker="s", ms=4, label=f"N={n}交换")
    axes[1, 1].set_yscale("log")
    axes[1, 1].set_title("同尺寸相邻强度的原生子空间重叠")
    axes[1, 1].set_ylabel("重叠得分（对数）")
    axes[1, 1].legend(frameon=False, fontsize=8)
    for axis in axes.flat:
        axis.set_xlabel("无序强度 r")
        axis.grid(alpha=0.2, which="both")
    fig.subplots_adjust(top=0.89, bottom=0.12, left=0.08, right=0.98, hspace=0.42, wspace=0.25)
    fig.suptitle("seed=6：细化强度路径与主奇异通道", fontsize=16, y=0.97)
    fig.savefig(ROOT / "seed6-matrix-path.png", bbox_inches="tight")
    plt.close(fig)


def fmt(value):
    return f"{value:.6g}"


def markdown(data):
    summary = data["summary"]
    lines = [
        "# Floquet-BdG 固定 seed=6 矩阵路径",
        "",
        f"> 日期：{REPORT_DATE}。固定 seed=6，r=0.1–0.2 共9个等距点、8条相邻链接；14个内部新尺寸单元，4个端点单元仅作路径一致性重算。不新增类别，不补算体 winding，未计算 N=640。",
        "",
        "## 一、两类路径证据必须分开",
        "",
        "跨尺寸 Oij 只在同一强度点的 N=400 与 N=600 子空间之间定义，不是同尺寸态追踪。相邻强度的同尺寸原生二维子空间重叠才是本报告的路径控制。两者都使用同一主无序剖面，离散网格不归一化，不筛选有利路径段。",
        "",
        f"端点矩阵最大误差为 {fmt(data['endpoint_binding']['max_matrix_absolute_error'])}，端点主奇异值最大误差为 {fmt(data['endpoint_binding']['max_singular_absolute_error'])}，端点前六谱距离最大误差为 {fmt(data['endpoint_binding']['max_spectrum_absolute_error'])}。端点重算不并入此前批次计数。",
        "",
        "## 二、跨尺寸矩阵项的逐点响应",
        "",
        "| 方法 | 矩阵项 | 最小值及强度 | 最大值及强度 | 最大相邻绝对跳变 | 主导奇异通道计数 |",
        "|:---|:---:|---:|---:|---:|:---:|",
    ]
    for row in data["entry_extrema"]:
        counts = row["dominant_singular_channel_counts"]
        channel = f"s₁:{counts.get('0', counts.get(0, 0))}／s₂:{counts.get('1', counts.get(1, 0))}"
        lines.append(f"| {row['method']} | {row['entry']} | {fmt(row['min'])} @ {row['min_strength']} | {fmt(row['max'])} @ {row['max_strength']} | {fmt(row['max_adjacent_absolute_jump'])}（{row['max_jump_from']}→{row['max_jump_to']}） | {channel} |")
    lines += [
        "",
        "图 1 插入位置：矩阵项表之后、原生相邻链接与边界之前。",
        "",
        "![图 1：固定种子矩阵路径](seed6-matrix-path.png)",
        "",
        "**图 1**　O00、O01、O10 及其主奇异通道随强度的变化，以及同尺寸相邻子空间重叠。数值贡献只用于分解，不直接命名物理机制。",
        "",
        "## 三、得分主导项与同尺寸原生链接",
        "",
        "| 方法 | 得分组 | 主导项计数（8条链接） | 得分比范围 |",
        "|:---|:---|:---|---:|",
    ]
    for row in data["driver_summary"]:
        lines.append(f"| {row['method']} | {row['score_group']} | {row['dominant_entry_counts']} | {fmt(row['score_ratio_range'][0])}–{fmt(row['score_ratio_range'][1])} |")
    lines += [
        "",
        "| N | 链接数 | 同谱秩最小值及链接 | 交换最大值及链接 | 最大中心间隔变化 |",
        "|---:|---:|---:|---:|---:|",
    ]
    for row in data["link_summary"]:
        lines.append(f"| {row['n']} | {row['link_count']} | {fmt(row['min_diagonal_score'])}（{row['min_diagonal_from']}→{row['min_diagonal_to']}） | {fmt(row['max_swapped_score'])}（{row['max_swapped_from']}→{row['max_swapped_to']}） | {fmt(row['max_absolute_center_separation_delta'])} |")
    lines += [
        "",
        f"跨表示自一致性范围为 {fmt(summary['min_representation_fidelity'])}–{fmt(summary['max_representation_fidelity'])}；线性点值秩间重叠最大为 {fmt(summary['max_linear_point_off_diagonal'])}，单元平均最大为 {fmt(summary['max_cell_average_off_diagonal'])}。这些控制不与路径得分混用。",
        "",
        "## 四、结论与边界",
        "",
        "细化路径可以检验横断面矩阵项关系的持续性，并定位相邻强度的最大数值贡献跳变；但8条离散链接仍不是连续路径证明。任何跳变、极小值或分配变化都不能直接命名为谱交叉、避免交叉或真实态交换。",
        "",
        "本轮不能外推为其他种子、普遍尺寸律、统计显著性、次近对拓扑性或热力学极限结论。旧交换候选属于不同无序实现，不能与路径差分直接相减。",
        "",
        "复现：`python research/floquet-bdg-tbc/analyze_seed6_matrix_path.py`。18个路径单元、54组矩阵、16条原生链接、192条矩阵项差分及控制保存在 `seed6_matrix_path_analysis.json`。",
        "",
    ]
    (ROOT / "SEED6_MATRIX_PATH.md").write_text("\n".join(lines), encoding="utf-8")


def check_only():
    stored = json.loads((ROOT / "seed6_matrix_path_analysis.json").read_text(encoding="utf-8"))
    if stored.get("protocol_sha256") != sha(PROTOCOL) or stored.get("batch_b_analysis_sha256") != sha(BATCH_B) or stored.get("batch_c_analysis_sha256") != sha(BATCH_C):
        raise ValueError("Seed-6 path evidence is stale")
    if len(stored.get("cells", [])) != 18 or len(stored.get("path_matrices", [])) != 54 or len(stored.get("links", [])) != 16:
        raise ValueError("Seed-6 path evidence is incomplete")
    if stored.get("new_interior_control_cells") != 14 or not stored.get("all_preregistered_results_retained"):
        raise ValueError("Seed-6 path scope changed")
    print(json.dumps({"check_only": True, "cells": 18, "path_matrices": 54, "native_links": 16, "entry_links": 192, "all_passed": True}, ensure_ascii=False))
    return 0


def main():
    if "--check-only" in sys.argv:
        return check_only()
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    cells, bases_by_key, path_matrices, representation_fidelity, rank_controls, max_direction = evaluate_path(protocol)
    links, method_grid_links, entry_links = build_links(protocol, cells, bases_by_key, path_matrices)
    batch_b = json.loads(BATCH_B.read_text(encoding="utf-8"))
    batch_c = json.loads(BATCH_C.read_text(encoding="utf-8"))
    summary = {
        "cross_size_assignment_counts": {
            method: dict(Counter(row["dominant_assignment"] for row in path_matrices if row["method"] == method))
            for method in protocol["methods"]
        },
        "max_direction_absolute_error": max_direction,
        "max_representation_direction_absolute_error": max(row["direction_absolute_error"] for row in representation_fidelity),
        "min_representation_fidelity": min(row["forward"] for row in representation_fidelity),
        "max_representation_fidelity": max(row["forward"] for row in representation_fidelity),
        "max_native_off_diagonal": max(row["off01"] for row in rank_controls if row["method"] == "native_qr"),
        "max_linear_point_off_diagonal": max(row["off01"] for row in rank_controls if row["method"] == "linear_point"),
        "max_cell_average_off_diagonal": max(row["off01"] for row in rank_controls if row["method"] == "cell_average"),
        "method_grid_assignment_change_count": sum(row["before_dominant_assignment"] != row["after_dominant_assignment"] for row in method_grid_links),
    }
    data = {
        "schema": "floquet-bdg-seed6-matrix-path-analysis-v1",
        "analysis_date": protocol["analysis_date"], "report_date": REPORT_DATE,
        "protocol_sha256": sha(PROTOCOL), "batch_b_analysis_sha256": sha(BATCH_B), "batch_c_analysis_sha256": sha(BATCH_C),
        "cells": cells, "path_matrices": path_matrices, "links": links,
        "method_grid_links": method_grid_links, "entry_links": entry_links,
        "entry_extrema": entry_extrema(path_matrices, entry_links),
        "driver_summary": driver_summary(method_grid_links), "link_summary": link_summary(links),
        "representation_fidelity": representation_fidelity, "rank_controls": rank_controls,
        "summary": summary, "endpoint_binding": endpoint_binding(cells, path_matrices, batch_b, batch_c),
        "new_interior_control_cells": 14, "endpoint_control_cells_recomputed": 4,
        "evaluated_control_cells": 18, "not_merged_into_batch_counts": True,
        "new_seed_count": 0, "new_winding_computed": False, "n640_computed": False,
        "all_preregistered_results_retained": True,
        "normalization_correction_applied": False, "representation_invariant_claim": False,
        "statistical_significance_claim": False, "continuous_path_proof": False,
        "spectral_crossing_proven": False, "avoided_crossing_claim": False,
        "state_exchange_proven": False, "causal_mechanism_proven": False,
        "thermodynamic_limit_proof": False, "new_taxonomy_claim": False,
        "old_candidate_is_different_realization": True,
        "difference_from_original_is_not_size_effect": True,
        "categories_changed": False,
    }
    (ROOT / "seed6_matrix_path_analysis.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    figure(data)
    markdown(data)
    print(json.dumps({"summary": summary, "driver_summary": data["driver_summary"], "link_summary": data["link_summary"], "endpoint_binding": data["endpoint_binding"], "cells": 18, "native_links": 16, "entry_links": 192}, ensure_ascii=False, indent=2))
    print("generated seed6_matrix_path_analysis.json seed6-matrix-path.png SEED6_MATRIX_PATH.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
