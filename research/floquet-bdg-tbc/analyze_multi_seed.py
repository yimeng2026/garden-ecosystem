"""Evaluate the preregistered four-seed, two-size, two-strength profile pilot."""

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
from analyze_endpoint_subspaces import pair_metrics  # noqa: E402
sys.path.insert(0, str(ROOT.parent / "floquet-bdg-convention"))
sys.path.insert(0, str(ROOT.parent / "floquet-bdg-disorder"))
from convention_model import quasienergy_spectrum  # noqa: E402
from disorder_model import disordered_floquet  # noqa: E402

PROTOCOL = ROOT / "multi_seed_protocol.json"
MATCHED = ROOT / "matched_profile_control.json"
SEEDS = [0, 1, 2, 3]
GRID = [(n, strength, seed) for n in (400, 600) for strength in (0.05, 0.1) for seed in SEEDS]
plt.rcParams.update({
    "font.sans-serif": ["Microsoft YaHei", "SimHei", "Noto Sans CJK SC", "DejaVu Sans"],
    "axes.unicode_minus": False, "font.size": 10, "figure.dpi": 160,
})


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compute_case(n, strength, seed):
    beta = np.random.default_rng(20261111 + seed).random(n)
    u, period = disordered_floquet(n, 2.5, beta, strength, 7.0, 1.0, 1.0)
    spectrum = quasienergy_spectrum(u, period)
    distances = np.abs(spectrum["eigenvalues"] - 1.0)
    order = np.argsort(distances)
    pairs = [pair_metrics(spectrum, n, order[2 * index:2 * index + 2], index) for index in range(2)]
    if seed == 0:
        previous = json.loads(MATCHED.read_text(encoding="utf-8"))
        old = next(row for row in previous["cases"] if (row["n"], row["strength"]) == (n, strength))["pairs"][0]
        if pairs[0]["profile_sha256"] != old["profile_sha256"] or pairs[0]["diagnostic_joint_pass"] != old["diagnostic_joint_pass"]:
            raise ValueError(f"Seed-zero regression failed for N={n}, r={strength}")
    return {"n": n, "strength": strength, "seed": seed, "pairs": pairs, "profile_only": True}


def lookup(cases, n, strength, seed):
    return next(row for row in cases if (row["n"], row["strength"], row["seed"]) == (n, strength, seed))


def difference(first, second):
    a, b = first["pairs"][0], second["pairs"][0]
    return {
        "delta_L50": b["L50"] - a["L50"],
        "delta_L90": b["L90"] - a["L90"],
        "delta_edge_weight": b["edge_weight"] - a["edge_weight"],
        "delta_center20_mass": b["center20_mass"] - a["center20_mass"],
    }


def summarize(values):
    array = np.asarray(values, dtype=float)
    return {
        "positive": int(np.sum(array > 0)), "negative": int(np.sum(array < 0)), "zero": int(np.sum(array == 0)),
        "median": float(np.median(array)), "minimum": float(np.min(array)), "maximum": float(np.max(array)),
    }


def metric_summaries(rows):
    return {metric: summarize([row[metric] for row in rows]) for metric in ("delta_L50", "delta_L90", "delta_edge_weight", "delta_center20_mass")}


def contrasts(cases):
    size_rows = [{"seed": seed, "strength": strength, **difference(lookup(cases, 400, strength, seed), lookup(cases, 600, strength, seed))} for strength in (0.05, 0.1) for seed in SEEDS]
    strength_rows = [{"seed": seed, "n": n, **difference(lookup(cases, n, 0.05, seed), lookup(cases, n, 0.1, seed))} for n in (400, 600) for seed in SEEDS]
    interaction = []
    for seed in SEEDS:
        low = next(row for row in size_rows if row["seed"] == seed and row["strength"] == 0.05)
        high = next(row for row in size_rows if row["seed"] == seed and row["strength"] == 0.1)
        interaction.append({"seed": seed, **{metric: high[metric] - low[metric] for metric in ("delta_L50", "delta_L90", "delta_edge_weight", "delta_center20_mass")}})
    groups = {
        "size_r0.05": metric_summaries([row for row in size_rows if row["strength"] == 0.05]),
        "size_r0.1": metric_summaries([row for row in size_rows if row["strength"] == 0.1]),
        "strength_N400": metric_summaries([row for row in strength_rows if row["n"] == 400]),
        "strength_N600": metric_summaries([row for row in strength_rows if row["n"] == 600]),
        "interaction": metric_summaries(interaction),
    }
    return {"size_at_fixed_strength": size_rows, "strength_at_fixed_size": strength_rows, "interaction": interaction}, groups


def figure(data):
    fig, axes = plt.subplots(2, 2, figsize=(12, 8.4), constrained_layout=False)
    specs = [
        ("size_at_fixed_strength", "strength", "delta_edge_weight", "固定强度：尺寸差 Δ端点权重"),
        ("size_at_fixed_strength", "strength", "delta_L50", "固定强度：尺寸差 ΔL50"),
        ("strength_at_fixed_size", "n", "delta_edge_weight", "固定尺寸：强度差 Δ端点权重"),
        ("strength_at_fixed_size", "n", "delta_L50", "固定尺寸：强度差 ΔL50"),
    ]
    colors = ["#356A64", "#A25B3F"]
    for axis, (group, factor, metric, title) in zip(axes.flat, specs):
        rows = data["contrasts"][group]
        for value, color in zip(sorted({row[factor] for row in rows}), colors):
            selected = [row for row in rows if row[factor] == value]
            axis.plot([row["seed"] for row in selected], [row[metric] for row in selected], marker="o", lw=1.3, ms=6, color=color, label=f"{factor}={value}")
            for row in selected:
                axis.annotate(f"{row[metric]:.2g}", (row["seed"], row[metric]), textcoords="offset points", xytext=(4, 4), fontsize=8, color=color)
        axis.axhline(0, color="#666666", lw=0.8, ls="--")
        axis.set_xticks(SEEDS)
        axis.set_xlabel("预登记种子")
        axis.set_ylabel(metric)
        axis.set_title(title)
        axis.grid(alpha=0.2)
        axis.legend(frameon=False)
    fig.subplots_adjust(top=0.88, bottom=0.09, left=0.09, right=0.98, hspace=0.4, wspace=0.28)
    fig.suptitle("四个预登记种子的对照方向与反转（全部保留）", fontsize=16, y=0.975)
    fig.savefig(ROOT / "multi-seed-control.png", bbox_inches="tight")
    plt.close(fig)


def fmt(value):
    return f"{value:.5g}"


def markdown(data):
    lines = [
        "# Floquet-BdG 多种子稳健性对照",
        "",
        "> 日期：2026-11-11。4 个预登记种子 seed=0、1、2、3，N=400／600 × r=0.05／0.1，共 16 个单元。新案例不补算体 winding，未计算 N=640。",
        "",
        "## 一、方向计数总表",
        "",
        "以下 `+／−／0` 是四个种子的方向计数。方向计数不是置信区间，也不是统计显著性。所有中位数和极值都只描述本次试点。",
        "",
        "| 对照 | 指标 | +／−／0 | 中位数 | 最小值 | 最大值 |",
        "|:---|:---|:---:|---:|---:|---:|",
    ]
    for group, summaries in data["sign_summaries"].items():
        for metric, summary in summaries.items():
            signs = f"{summary['positive']}／{summary['negative']}／{summary['zero']}"
            lines.append(f"| {group} | {metric} | {signs} | {fmt(summary['median'])} | {fmt(summary['minimum'])} | {fmt(summary['maximum'])} |")
    lines += [
        "",
        "图 1 插入位置：方向计数之后、逐种子结果之前。",
        "",
        "![图 1：四个种子的对照方向](multi-seed-control.png)",
        "",
        "**图 1**　四个种子全部保留，方向反转不做删除或平滑。",
        "",
        "## 二、固定强度的逐种子尺寸差",
        "",
        "| seed | r | ΔL50 | ΔL90 | Δ端点权重 | Δ中心20%质量 |",
        "|---:|---:|---:|---:|---:|---:|",
    ]
    for row in data["contrasts"]["size_at_fixed_strength"]:
        lines.append(f"| {row['seed']} | {row['strength']} | {row['delta_L50']} | {row['delta_L90']} | {fmt(row['delta_edge_weight'])} | {fmt(row['delta_center20_mass'])} |")
    lines += [
        "",
        "## 三、固定尺寸的逐种子强度差",
        "",
        "| seed | N | ΔL50 | ΔL90 | Δ端点权重 | Δ中心20%质量 |",
        "|---:|---:|---:|---:|---:|---:|",
    ]
    for row in data["contrasts"]["strength_at_fixed_size"]:
        lines.append(f"| {row['seed']} | {row['n']} | {row['delta_L50']} | {row['delta_L90']} | {fmt(row['delta_edge_weight'])} | {fmt(row['delta_center20_mass'])} |")
    lines += [
        "",
        "## 四、逐种子交互项",
        "",
        "| seed | ΔL50 | ΔL90 | Δ端点权重 | Δ中心20%质量 |",
        "|---:|---:|---:|---:|---:|",
    ]
    for row in data["contrasts"]["interaction"]:
        lines.append(f"| {row['seed']} | {row['delta_L50']} | {row['delta_L90']} | {fmt(row['delta_edge_weight'])} | {fmt(row['delta_center20_mass'])} |")
    interaction = data["sign_summaries"]["interaction"]
    lines += [
        "",
        f"交互项端点权重的方向计数为 {interaction['delta_edge_weight']['positive']} 正、{interaction['delta_edge_weight']['negative']} 负、{interaction['delta_edge_weight']['zero']} 零；交互项仍只是四个种子的描述量。",
        "",
        "## 五、稳定性分层：哪些方向保留，哪些必须放弃普适化",
        "",
        "尺寸端点权重并非全员同号：r=0.05 与 r=0.1 下均为 3 正 1 负，L50 则均为 2 正 2 负。尺寸效应的符号反转不能普适化，seed=0 的方向不能代表其他随机实现。",
        "",
        "两种强度下，尺寸差的中心 20% 质量均在 4/4 种子中下降。该方向在本网格一致，但只能支持当前有限模型的中心区稀释现象，不能直接给出衰减指数或热力学标度。",
        "",
        "强度升高端点权重在 4/4 种子中增加，N=400 和 N=600 分别成立。L50 在 N=400 的 4/4 种子中缩短，在 N=600 的 3/4 种子中缩短；seed=1 的 N=600 反例为 ΔL50=+1，必须保留。",
        "",
        "因此，强度效应是本网格中较稳定的观察方向，尺寸效应则不稳定。幅度差异和 2 正 2 负的交互项进一步阻止将 seed=0 的符号反转提升为普适规律。",
        "",
        "## 六、解释边界与下一步",
        "",
        "该试点检验的是 profile 方向是否能跨随机实现保持，不证明单调物理规律。只有方向、幅度和候选子空间共同稳定时，才值得进入下一轮体积分或尺寸标度。",
        "",
        "不补算体 winding，尤其不把单个种子的局部通过升级为拓扑恢复。下一步应针对方向不稳定或反转的单元分析其谱隔离与端部不对称，而不是追加种子直到出现想要的结果。",
        "",
        "复现：`python research/floquet-bdg-tbc/analyze_multi_seed.py`。全部 16 个单元、两对候选模和逐种子差值均保存在 `multi_seed_profile_control.json`。",
        "",
    ]
    (ROOT / "MULTI_SEED_CONTROL.md").write_text("\n".join(lines), encoding="utf-8")


def main():
    cases = [compute_case(n, strength, seed) for n, strength, seed in GRID]
    contrast_rows, sign_summaries = contrasts(cases)
    data = {
        "schema": "floquet-bdg-multi-seed-profile-control-v1",
        "analysis_date": "2026-11-11",
        "protocol_sha256": sha(PROTOCOL),
        "matched_source_sha256": sha(MATCHED),
        "seeds": SEEDS,
        "cases": cases,
        "contrasts": contrast_rows,
        "sign_summaries": sign_summaries,
        "new_winding_computed": False,
        "n640_computed": False,
        "causal_or_statistical_claim": False,
        "post_hoc_seed_selection": False,
        "thermodynamic_limit_proof": False,
    }
    (ROOT / "multi_seed_profile_control.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    figure(data)
    markdown(data)
    print(json.dumps({"contrasts": contrast_rows, "sign_summaries": sign_summaries, "cases": len(cases), "new_winding_computed": False, "n640_computed": False}, ensure_ascii=False, indent=2))
    print("generated multi_seed_profile_control.json multi-seed-control.png MULTI_SEED_CONTROL.md")


if __name__ == "__main__":
    main()
