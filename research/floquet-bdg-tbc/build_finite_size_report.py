"""Generate N=80/160/320 zero-gap finite-size evidence and figures."""

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent
FINITE = json.loads((ROOT / "finite_size_zero.json").read_text(encoding="utf-8"))
INDEPENDENT = json.loads((ROOT / "finite_size_independent.json").read_text(encoding="utf-8"))
N80_DATA = json.loads((ROOT / "disorder_results.json").read_text(encoding="utf-8"))
OLD = json.loads((ROOT.parent / "floquet-bdg-disorder" / "results.json").read_text(encoding="utf-8"))

plt.rcParams.update({
    "font.sans-serif": ["Microsoft YaHei", "SimHei", "Noto Sans CJK SC", "DejaVu Sans"],
    "axes.unicode_minus": False, "font.size": 10, "figure.dpi": 160,
})
COLORS = {0.05: "#805500", 0.1: "#A25B3F", 0.2: "#356A64"}


def old_row(n, strength, seed):
    return next(row for row in OLD["realizations"] if row["n"] == n and row["strength"] == strength and row["seed"] == seed)


def n80_row(strength, seed):
    return next(row for row in N80_DATA["realizations"] if row["strength"] == strength and row["seed"] == seed and row["kind"] == "disorder")


def finite_row(strength, seed):
    return next(row for row in FINITE["rows"] if row["strength"] == strength and row["seed"] == seed and row["kind"] == "disorder")


def independent_row(strength, seed):
    return next((row for row in INDEPENDENT["checks"] if row["strength"] == strength and row["seed"] == seed and row["kind"] == "disorder"), None)


def endpoint_row(n, strength, seed):
    return n80_row(strength, seed) if n == 80 else old_row(n, strength, seed)


def trend(strength, n):
    rows = [endpoint_row(n, strength, seed) for seed in range(4)]
    return {
        "strength": strength, "n": n,
        "pass_count": sum(row["endpoint"]["zero"]["joint_pass"] if n == 80 else row["zero"]["joint_pass"] for row in rows),
        "total": 4,
        "median_edge": float(np.median([row["endpoint"]["zero"]["edge_weight"] if n == 80 else row["zero"]["edge_weight"] for row in rows])),
        "median_separation": float(np.median([max(row["endpoint"]["zero"]["separation_ratios"] if n == 80 else row["zero"]["separation_ratios"]) for row in rows])),
    }


def validate_n160_endpoint_agreement():
    for strength in (0.05, 0.1):
        for seed in range(4):
            current = finite_row(strength, seed)["endpoint"]["zero"]
            previous = old_row(160, strength, seed)["zero"]
            if current["joint_pass"] != previous["joint_pass"] or abs(current["edge_weight"] - previous["edge_weight"]) > 1e-12:
                raise ValueError("N=160 endpoint convention or sequence mismatch")


def figure_winding():
    rows = FINITE["rows"]
    labels = [f"U{row['strength']}" if row["kind"] == "uniform_mean" else f"D{row['strength']}s{row['seed']}" for row in rows]
    x = np.arange(len(rows))
    fig, axes = plt.subplots(2, 1, figsize=(12, 7), constrained_layout=False)
    for row, xi in zip(rows, x):
        color = "#356A64" if row["kind"] == "uniform_mean" else "#A25B3F"
        axes[0].scatter(xi, row["zero"]["value"], s=58, color=color, zorder=3)
        check = independent_row(row["strength"], row["seed"]) if row["kind"] == "disorder" else next((item for item in INDEPENDENT["checks"] if item["strength"] == row["strength"] and item["kind"] == "uniform_mean"), None)
        if check is not None:
            axes[0].scatter(xi, check["independent"]["value"], s=115, marker="D", facecolors="none", edgecolors="#2E5C55", linewidths=1.1)
        axes[1].scatter(xi, row["zero"]["min_bulk_gap"], s=58, color=color)
    axes[0].set_ylim(0.99970, 1.00003)
    axes[0].set_ylabel("W0 原始值")
    axes[0].grid(axis="y", alpha=0.2)
    axes[1].set_yscale("log")
    axes[1].set_ylabel("最小 0 体隙")
    axes[1].set_xticks(x, labels, rotation=45, ha="right")
    axes[1].grid(axis="y", which="both", alpha=0.2)
    for ax in axes:
        ax.set_xlim(-0.7, len(rows) - 0.3)
    fig.subplots_adjust(top=0.86, bottom=0.22, hspace=0.32)
    fig.suptitle("N=160：11 个定向 0 隙算例均为有效 W0=1", fontsize=16, y=0.97)
    fig.text(0.5, 0.91, "U：均匀控制；D：无序；空心菱形：独立行列式复核", ha="center", color="#555555")
    fig.savefig(ROOT / "finite-size-winding.png", bbox_inches="tight")
    plt.close(fig)


def figure_endpoints():
    fig, axes = plt.subplots(1, 2, figsize=(12, 5.5), constrained_layout=False)
    for strength in (0.05, 0.1, 0.2):
        rows = [trend(strength, n) for n in (80, 160, 320)]
        axes[0].plot([80, 160, 320], [row["pass_count"] / 4 for row in rows], marker="o", ms=8, lw=1.8, color=COLORS[strength], label=f"r={strength}")
    axes[0].set_xticks([80, 160, 320])
    axes[0].set_ylim(-0.05, 1.05)
    axes[0].set_ylabel("0 模端点联合通过率")
    axes[0].set_xlabel("链长 N")
    axes[0].grid(alpha=0.2)
    axes[0].legend(frameon=False)
    for strength, linestyle in ((0.05, "-"), (0.1, "--")):
        for seed in range(4):
            weights = [endpoint_row(n, strength, seed)["endpoint"]["zero"]["edge_weight"] if n == 80 else endpoint_row(n, strength, seed)["zero"]["edge_weight"] for n in (80, 160, 320)]
            axes[1].plot([80, 160, 320], weights, marker="o", ms=5, lw=1.1, ls=linestyle, color=COLORS[strength], alpha=0.75, label=f"r={strength}, seed={seed}")
    axes[1].axhline(0.5, color="#777777", ls=":", lw=1)
    axes[1].set_xticks([80, 160, 320])
    axes[1].set_ylim(0, 1)
    axes[1].set_ylabel("0 模端点权重")
    axes[1].set_xlabel("链长 N")
    axes[1].grid(alpha=0.2)
    axes[1].legend(frameon=False, fontsize=8, ncol=2)
    fig.subplots_adjust(top=0.82, bottom=0.14, wspace=0.25)
    fig.suptitle("端点候选随尺寸恢复并不一致，且 N=320 尚无 TBC winding", fontsize=15, y=0.97)
    fig.savefig(ROOT / "finite-size-endpoints.png", bbox_inches="tight")
    plt.close(fig)


def fmt(value, digits=6):
    if value is None:
        return "—"
    if isinstance(value, str):
        return value
    return f"{value:.{digits}g}"


def markdown():
    lines = [
        "# N=160 Floquet-BdG TBC 0 隙有限尺寸对照",
        "",
        "> 日期：2026-11-11。本文检验有限尺寸体 winding 与端点候选的对应关系，不宣称 N=320 winding、热力学极限或材料实验结论。",
        "",
        "## 一、定向问题与 11 例注册",
        "",
        "三种均匀控制（r=0.05/0.1/0.2）与两种无序强度（r=0.05/0.1）各 4 个固定 seed 组成 11 个 N=160 的 0 隙算例。K 矩阵参数为 rβ，半 kick 角为 rβ，完整对称旋转角为 2rβ。",
        "",
        "| r | seed／控制 | 类型 | W0 原始值 | 整数 | 最小体隙 | 端点联合通过 |",
        "|---:|:---:|:---|---:|---:|---:|:---:|",
    ]
    for row in FINITE["rows"]:
        label = "—" if row["kind"] == "uniform_mean" else str(row["seed"])
        lines.append(f"| {row['strength']} | {label} | {'均匀均值' if row['kind'] == 'uniform_mean' else '无序'} | {fmt(row['zero']['value'], 12)} | {row['zero']['nearest_integer']} | {fmt(row['zero']['min_bulk_gap'])} | {str(row['endpoint']['zero']['joint_pass'])} |")
    lines += [
        "",
        "全部 11 个主积分结果有效，最近整数均为 1。N=80 时 r=0.05、seed=2/3 的主积分未收敛，在 N=160 转为有效 1。",
        "",
        "图 1 插入位置：11 例注册表之后、尺寸趋势之前。",
        "",
        "![图 1：N160 定向 winding 与体隙](finite-size-winding.png)",
        "",
        "**图 1**　所有 N=160 定向算例均为有效 W0=1；空心菱形为独立行列式复核。",
        "",
        "## 二、N=80／160／320 端点趋势",
        "",
        "| r | N | 0 模联合通过/4 | 端点权重中位数 | 分离度中位数 |",
        "|---:|---:|---:|---:|---:|",
    ]
    for strength in (0.05, 0.1, 0.2):
        for n in (80, 160, 320):
            row = trend(strength, n)
            lines.append(f"| {strength} | {n} | {row['pass_count']}/4 | {fmt(row['median_edge'])} | {fmt(row['median_separation'])} |")
    lines += [
        "",
        "图 2 插入位置：尺寸趋势表之后、逐 seed 对照之前。",
        "",
        "![图 2：端点通过率与权重尺寸趋势](finite-size-endpoints.png)",
        "",
        "**图 2**　端点恢复不是全体一致的单调过程。线段只连接三个已测尺寸，不表示连续相界。",
        "",
        "| r | seed | N=80 W0 状态/整数 | N=160 W0 整数 | N=320 端点通过 | N=320 端点权重 |",
        "|---:|---:|:---|:---|:---:|:---:|",
    ]
    for strength in (0.05, 0.1):
        for seed in range(4):
            n80 = n80_row(strength, seed)["zero"]
            n160 = finite_row(strength, seed)["zero"]
            n320 = old_row(320, strength, seed)["zero"]
            lines.append(f"| {strength} | {seed} | {n80['status']}/{n80['nearest_integer']} | {n160['nearest_integer']} | {str(n320['joint_pass'])} | {fmt(n320['edge_weight'])} |")
    lines += [
        "",
        "N=320 的 TBC winding 尚未计算，表中只引用既有开链端点观测，不能从端点恢复反推体不变量。",
        "",
        "## 三、独立复核与解释边界",
        "",
        f"独立行列式复核共 {INDEPENDENT['selected_count']} 项，passed={str(INDEPENDENT['passed']).lower()}：三种均匀控制、两种强度的代表无序样本，以及 N=80 的两个原未收敛样本。所有整数一致。",
        "",
        "N=160 的 r=0.05 与 r=0.1 无序 0 模端点联合判据均为 0/4 通过，而对应体 W0 均为 1。这真实确认了中间尺寸的判据分离。N=320 的部分端点恢复支持有限尺寸交叉作为后续假说，但尚不能证明热力学体边对应或排除所有体边失配。",
        "",
        "下一步应选择 N=320 中端点已恢复的 r=0.05、seed=2/3 与 r=0.1、seed=2 做定向 TBC winding；未恢复的 seed 保留为对照。",
        "",
        "复现：python research/floquet-bdg-tbc/run_finite_size.py --merge-only；python research/floquet-bdg-tbc/verify_finite_size.py --merge-only。原始证据：finite_size_zero.json、finite_size_independent.json 及既有 floquet-bdg-disorder/results.json。",
        "",
    ]
    (ROOT / "FINITE_SIZE.md").write_text("\n".join(lines), encoding="utf-8")


def main():
    if not FINITE.get("complete") or len(FINITE["rows"]) != 11:
        raise ValueError("finite-size registry is incomplete")
    if not INDEPENDENT.get("passed") or INDEPENDENT.get("selected_count") != 7:
        raise ValueError("finite-size independent evidence is incomplete")
    validate_n160_endpoint_agreement()
    figure_winding()
    figure_endpoints()
    markdown()
    print("generated finite-size-winding.png finite-size-endpoints.png FINITE_SIZE.md")


if __name__ == "__main__":
    main()
