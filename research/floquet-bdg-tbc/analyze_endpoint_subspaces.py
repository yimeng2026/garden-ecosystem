"""Compare the first two zero-target pairs without changing the endpoint verdict."""

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
sys.path.insert(0, str(ROOT.parent / "floquet-bdg-localization-scale"))
from convention_model import quasienergy_spectrum  # noqa: E402
from disorder_model import disordered_floquet  # noqa: E402
from scale_analysis import center_mass, coverage_lengths  # noqa: E402

SOURCE = ROOT / "scale_diagnostic.json"
DATA = json.loads(SOURCE.read_text(encoding="utf-8"))
plt.rcParams.update({
    "font.sans-serif": ["Microsoft YaHei", "SimHei", "Noto Sans CJK SC", "DejaVu Sans"],
    "axes.unicode_minus": False, "font.size": 10, "figure.dpi": 160,
})


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pair_metrics(spectrum, n, indices, pair_index):
    vectors = spectrum["eigenvectors"][:, indices]
    q, _ = np.linalg.qr(vectors)
    diagonal = np.einsum("ij,ij->i", q, q.conj()).real
    profile = diagonal.reshape((n, 2)).sum(axis=1) / 2
    edge_sites = max(1, int(np.ceil(0.1 * n)))
    distances = np.abs(spectrum["eigenvalues"] - 1.0)
    bulk_distance = float(np.sort(distances)[2])
    ratios = distances[indices] / bulk_distance
    edge_weight = float(profile[:edge_sites].sum() + profile[-edge_sites:].sum())
    lengths = coverage_lengths(profile)
    return {
        "pair_index": pair_index,
        "spectrum_indices": [int(index) for index in indices],
        "distances": [float(distances[index]) for index in indices],
        "separation_ratios": [float(value) for value in ratios],
        "max_separation_ratio": float(max(ratios)),
        "edge_sites_per_end": edge_sites,
        "left_edge_weight": float(profile[:edge_sites].sum()),
        "right_edge_weight": float(profile[-edge_sites:].sum()),
        "edge_weight": edge_weight,
        **lengths,
        "mass20": float(profile[:20].sum() + profile[-20:].sum()),
        "mass40": float(profile[:40].sum() + profile[-40:].sum()),
        "center20_mass": center_mass(profile, fraction=0.2),
        "subspace_ipr": float(diagonal @ diagonal),
        "n_profile_ipr": float(n * np.sum(profile**2)),
        "diagnostic_joint_pass": bool(max(ratios) < 0.1 and edge_weight > 0.5),
        "profile_sha256": hashlib.sha256(profile.tobytes()).hexdigest(),
        "profile": [float(value) for value in profile],
    }


def compute_case(n):
    row = next(row for row in DATA["rows"] if row["n"] == n)
    strength, seed = row["strength"], row["seed"]
    beta = np.random.default_rng(20261111 + seed).random(n)
    u, period = disordered_floquet(n, 2.5, beta, strength, 7.0, 1.0, 1.0)
    spectrum = quasienergy_spectrum(u, period)
    distances = np.abs(spectrum["eigenvalues"] - 1.0)
    order = np.argsort(distances)
    pairs = [pair_metrics(spectrum, n, order[2 * index:2 * index + 2], index) for index in range(2)]
    old = json.loads((ROOT / f"n{n}_scale.json").read_text(encoding="utf-8"))
    first = pairs[0]
    if first["profile_sha256"] != old["profile_sha256"] or first["edge_weight"] != old["edge_weight"]:
        raise ValueError(f"N={n} first pair does not reproduce the frozen profile")
    if first["diagnostic_joint_pass"] != row["endpoint"]["zero"]["joint_pass"]:
        raise ValueError(f"N={n} first pair does not reproduce the original endpoint verdict")
    return {
        "n": n, "strength": strength, "seed": seed,
        "original_winding_integer": row["zero"]["nearest_integer"],
        "original_winding_raw": row["zero"]["value"],
        "original_min_bulk_gap": row["zero"]["min_bulk_gap"],
        "original_joint_pass": row["endpoint"]["zero"]["joint_pass"],
        "reported_joint_pass": row["endpoint"]["zero"]["joint_pass"],
        "pairs": pairs,
        "selection_caveat": "第二对按同一第三近体距离计算；不回溯替换原最近邻端点判据。",
        "reference_sha256": sha(ROOT / f"n{n}_scale.json"),
    }


def figure(cases):
    fig, axes = plt.subplots(2, 2, figsize=(12, 8.4), constrained_layout=False)
    colors = ["#356A64", "#A25B3F"]
    for row_index, case in enumerate(cases):
        n = case["n"]
        cumulative_axis, profile_axis = axes[row_index]
        for pair, color in zip(case["pairs"], colors):
            profile = np.asarray(pair["profile"])
            cumulative = np.cumsum(profile + profile[::-1])
            x = (np.arange(n) + 1) / n
            cumulative_axis.plot(x, cumulative, color=color, lw=1.5, label=f"第 {pair['pair_index'] + 1} 对")
            profile_axis.semilogy(np.arange(n), np.maximum(profile, 1e-16), color=color, lw=1.0, label=f"第 {pair['pair_index'] + 1} 对")
        cumulative_axis.set_xlim(0, 0.5)
        cumulative_axis.set_ylim(0, 1.02)
        cumulative_axis.axhline(0.5, color="#888888", lw=0.7, ls="--")
        cumulative_axis.axhline(0.9, color="#BBBBBB", lw=0.7, ls="--")
        cumulative_axis.set_title(f"N={n}：两端累积覆盖")
        cumulative_axis.set_xlabel("每端覆盖宽度 / N")
        cumulative_axis.set_ylabel("累计质量")
        cumulative_axis.grid(alpha=0.2)
        cumulative_axis.legend(frameon=False)
        profile_axis.set_title(f"N={n}：最近对与次近对剖面")
        profile_axis.set_xlabel("格点 j")
        profile_axis.set_ylabel("投影子空间权重（对数轴）")
        profile_axis.grid(alpha=0.2)
        profile_axis.legend(frameon=False)
    fig.subplots_adjust(top=0.89, bottom=0.09, left=0.08, right=0.98, hspace=0.42, wspace=0.25)
    fig.suptitle("零能候选子空间：最近对与次近对只作诊断，不回溯恢复端点", fontsize=15, y=0.975)
    fig.savefig(ROOT / "endpoint-subspaces.png", bbox_inches="tight")
    plt.close(fig)


def fmt(value):
    return f"{value:.6g}"


def markdown(data):
    lines = [
        "# Floquet-BdG 最近／次近零能子空间诊断",
        "",
        "> 日期：2026-11-11。保留 N=400、r=0.1、seed=0 与 N=600、r=0.05、seed=0 的原有输入。仅比较最近两对候选模，未计算 N=640。",
        "",
        "## 一、为什么检查次近对",
        "",
        "W₀=1 而端点联合判据失败，可能来自候选子空间选择，也可能来自真实的端点非局域化。先检查次近对是否提供不同信息；第二对不回溯恢复，也不替换已经登记的最近邻判据。",
        "",
        "| N | 子空间 | 端点权重 | 最大分离比 | L50 | L90 | 原判据 |",
        "|---:|:---|---:|---:|---:|---:|:---|",
    ]
    for case in data["cases"]:
        for pair in case["pairs"]:
            label = "最近对" if pair["pair_index"] == 0 else "次近对"
            verdict = "通过" if case["original_joint_pass"] and pair["pair_index"] == 0 else "不通过／不提升"
            lines.append(f"| {case['n']} | {label} | {fmt(pair['edge_weight'])} | {fmt(pair['max_separation_ratio'])} | {pair['L50']} | {pair['L90']} | {verdict} |")
    lines += [
        "",
        "图 1 插入位置：子空间指标之后、个案解释之前。",
        "",
        "![图 1：最近对与次近对的覆盖和剖面](endpoint-subspaces.png)",
        "",
        "**图 1**　上排为 N=400，下排为 N=600；左列是两端累积覆盖，右列是投影子空间剖面。对数轴下界仅用于显示，原始权重保存在 JSON。",
        "",
        "## 二、个案读数与选择边界",
        "",
    ]
    for case in data["cases"]:
        first, second = case["pairs"]
        lines.append(f"### N={case['n']}")
        lines.append("")
        lines.append(f"最近对端点权重为 {fmt(first['edge_weight'])}，次近对为 {fmt(second['edge_weight'])}；次近对最大分离比为 {fmt(second['max_separation_ratio'])}。")
        lines.append("")
        lines.append(f"最近对左／右端权重分别为 {fmt(first['left_edge_weight'])}／{fmt(first['right_edge_weight'])}；次近对分别为 {fmt(second['left_edge_weight'])}／{fmt(second['right_edge_weight'])}。")
        lines.append("")
        if case["n"] == 400:
            lines.append("最近对的通过由右端主导，而不是两端同时达到 0.5。单端权重不等于拓扑证明；次近对也主要压在右端，但其最大分离比为 1，与第三近体距离重合，不能作为另一个隔离端点候选。")
            lines.append("")
        elif case["n"] == 600:
            lines.append(f"次近对的中心 20% 质量增至 {fmt(second['center20_mass'])}，L50 增至 {second['L50']}，且最大分离比为 1。它更接近体谱且更离域，因此不能把最近对未通过简单解释为选错备用端点。")
            lines.append("")
        if second["edge_weight"] > first["edge_weight"]:
            lines.append("次近对端部权重更高，但这只是候选子空间差异的诊断信号，不能据此回溯恢复原端点判据，更不能替代体边对应证明。")
        else:
            lines.append("次近对没有显示更高的端部权重。本例不支持‘仅因最近邻选错子空间就造成端点未通过’这一充分解释。")
        lines.append("")
    lines += [
        "## 三、解释边界与下一步",
        "",
        "N=400 的局部阈值穿越与 N=600 的尾长增长仍是两类不同边界现象。两个案例具有不同无序强度，不能把观测差异单独归因于链长 N。W₀=1 只保留其原有体不变量含义，不自动等于端点恢复或热力学体边对应。",
        "",
        "本次没有计算 N=640。下一步应在同一无序强度、同一嵌套随机流下比较 profile 与候选子空间，区分无序强度效应和尺寸效应；在新对照完成前，不提出普适恢复标度。",
        "",
        "复现：`python research/floquet-bdg-tbc/analyze_endpoint_subspaces.py`。原始数组、首对 SHA-256 和既有 winding／端点状态保存在 `endpoint_subspace_analysis.json`。",
        "",
    ]
    (ROOT / "ENDPOINT_SUBSPACES.md").write_text("\n".join(lines), encoding="utf-8")


def main():
    cases = [compute_case(n) for n in (400, 600)]
    data = {
        "schema": "floquet-bdg-endpoint-subspace-diagnostic-v1",
        "analysis_date": "2026-11-11",
        "source_sha256": sha(SOURCE),
        "method": "rank-two QR projector site weights; nearest two pairs ordered by distance to +1; same third-nearest bulk-distance denominator",
        "second_pair_role": "diagnostic_only_no_retroactive_recovery",
        "n640_computed": False,
        "thermodynamic_limit_proof": False,
        "cases": cases,
    }
    (ROOT / "endpoint_subspace_analysis.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    figure(cases)
    markdown(data)
    print(json.dumps({
        "cases": [{"n": case["n"], "pairs": [{key: value for key, value in pair.items() if key != "profile"} for pair in case["pairs"]]} for case in cases],
        "n640_computed": False,
        "second_pair_role": data["second_pair_role"],
    }, ensure_ascii=False, indent=2))
    print("generated endpoint_subspace_analysis.json endpoint-subspaces.png ENDPOINT_SUBSPACES.md")


if __name__ == "__main__":
    main()
