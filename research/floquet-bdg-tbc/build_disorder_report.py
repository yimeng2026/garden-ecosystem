"""Generate figures and a data-bound Markdown report from corrected TBC results."""

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent
DATA = json.loads((ROOT / "disorder_results.json").read_text(encoding="utf-8"))
INDEPENDENT = json.loads((ROOT / "disorder_independent.json").read_text(encoding="utf-8"))
BASELINE = json.loads((ROOT / "results.json").read_text(encoding="utf-8"))

plt.rcParams.update({
    "font.sans-serif": ["Microsoft YaHei", "SimHei", "Noto Sans CJK SC", "DejaVu Sans"],
    "axes.unicode_minus": False,
    "font.size": 10,
    "axes.titlesize": 12,
    "figure.dpi": 160,
})
COLORS = {"disorder": "#A25B3F", "uniform_mean": "#356A64"}
LABELS = {"disorder": "无序", "uniform_mean": "均匀均值"}


def rows_for(strength, kind):
    return sorted(
        [row for row in DATA["realizations"] if row["strength"] == strength and row["kind"] == kind],
        key=lambda row: row["seed"],
    )


def independent_for(row, target):
    for check in INDEPENDENT["checks"]:
        if (
            check["strength"] == row["strength"] and check["seed"] == row["seed"]
            and check["kind"] == row["kind"] and check["target"] == target
        ):
            return check
    return None


def winding_figure():
    fig, axes = plt.subplots(3, 2, figsize=(11, 11), constrained_layout=False)
    for i, strength in enumerate((0.05, 0.1, 0.2)):
        for j, target in enumerate(("zero", "pi")):
            ax = axes[i, j]
            for kind, offset in (("disorder", -0.12), ("uniform_mean", 0.12)):
                for row in rows_for(strength, kind):
                    result = row[target]
                    x = row["seed"] + offset
                    if result["status"] == "ok":
                        ax.scatter(x, result["value"], s=52, color=COLORS[kind], zorder=3)
                    else:
                        ax.scatter(x, 0.5, s=72, marker="x", color="#8B3A3A", linewidth=2, zorder=4)
                        ax.text(x, 0.56, "未收敛", ha="center", color="#8B3A3A", fontsize=8)
                    check = independent_for(row, target)
                    if check is not None and check["independent"]["value"] is not None:
                        ax.scatter(x, check["independent"]["value"], s=105, marker="D", facecolors="none", edgecolors="#2E5C55", linewidths=1.1, zorder=2)
            ax.axhline(1, color="#777777", lw=0.8, ls="--")
            ax.axhline(0, color="#999999", lw=0.7, ls=":")
            ax.set_ylim(-0.13, 1.18)
            ax.set_xlim(-0.55, 3.55)
            ax.set_xticks(range(4), [f"seed {k}" for k in range(4)])
            ax.set_yticks([0, 0.5, 1])
            ax.grid(axis="y", alpha=0.2)
            ax.set_title(f"r={strength} · {'0 隙' if target == 'zero' else 'π 隙'}")
            if j == 0:
                ax.set_ylabel("winding（原始值）")
    handles = [
        plt.Line2D([0], [0], marker="o", color="w", markerfacecolor=COLORS["disorder"], markersize=8, label="无序"),
        plt.Line2D([0], [0], marker="o", color="w", markerfacecolor=COLORS["uniform_mean"], markersize=8, label="均匀均值"),
        plt.Line2D([0], [0], marker="x", color="#8B3A3A", lw=0, markersize=8, label="主积分未收敛"),
        plt.Line2D([0], [0], marker="D", color="#2E5C55", markerfacecolor="none", lw=0, markersize=9, label="独立行列式复核"),
    ]
    fig.subplots_adjust(top=0.90, bottom=0.06, hspace=0.36, wspace=0.18)
    fig.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, 0.955), ncol=4, frameon=False)
    fig.suptitle("N=80：逐实现 TBC dynamical winding", fontsize=16, y=0.995)
    fig.savefig(ROOT / "disorder-winding.png", bbox_inches="tight")
    plt.close(fig)


def gap_figure():
    fig, axes = plt.subplots(3, 2, figsize=(11, 11), constrained_layout=False)
    for i, strength in enumerate((0.05, 0.1, 0.2)):
        for j, target in enumerate(("zero", "pi")):
            ax = axes[i, j]
            for kind, offset in (("disorder", -0.12), ("uniform_mean", 0.12)):
                for row in rows_for(strength, kind):
                    result = row[target]
                    endpoint = row["endpoint"][target]
                    x = row["seed"] + offset
                    marker = "x" if result["status"] != "ok" else "o"
                    ax.scatter(
                        x, result["min_bulk_gap"], s=70, marker=marker,
                        color=COLORS[kind], linewidth=1.8 if marker == "x" else 1.0,
                        zorder=3,
                    )
                    if endpoint["joint_pass"]:
                        ax.scatter(x, result["min_bulk_gap"], s=125, facecolors="none", edgecolors="#222222", linewidths=1.1, zorder=2)
            ax.set_yscale("log")
            ax.set_xlim(-0.55, 3.55)
            ax.set_xticks(range(4), [f"seed {k}" for k in range(4)])
            ax.grid(axis="y", which="both", alpha=0.2)
            ax.set_title(f"r={strength} · {'0 隙' if target == 'zero' else 'π 隙'}")
            if j == 0:
                ax.set_ylabel("最小体隙（对数坐标）")
    handles = [
        plt.Line2D([0], [0], marker="o", color="w", markerfacecolor=COLORS["disorder"], markersize=8, label="无序"),
        plt.Line2D([0], [0], marker="o", color="w", markerfacecolor=COLORS["uniform_mean"], markersize=8, label="均匀均值"),
        plt.Line2D([0], [0], marker="o", color="#222222", markerfacecolor="none", lw=0, markersize=10, label="外圈：端点联合判据通过"),
        plt.Line2D([0], [0], marker="x", color="#8B3A3A", lw=0, markersize=8, label="主积分未收敛"),
    ]
    fig.subplots_adjust(top=0.90, bottom=0.06, hspace=0.36, wspace=0.18)
    fig.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, 0.955), ncol=4, frameon=False)
    fig.suptitle("体隙与有限开链端点判据不是同一观测量", fontsize=16, y=0.995)
    fig.savefig(ROOT / "disorder-gaps.png", bbox_inches="tight")
    plt.close(fig)


def fmt(value, digits=6):
    if value is None:
        return "—"
    if isinstance(value, str):
        return value
    return f"{value:.{digits}g}"


def markdown():
    lines = [
        "# Floquet-BdG TBC dynamical winding：无序与均匀均值对照",
        "",
        "> 日期：2026-11-11。范围：N=80、4 个固定 seed、r=0.05/0.1/0.2 的有限二次型模型。本文不宣称热力学极限、材料 Tc、相互作用、耗散或实验验证。",
        "",
        "## 一、结论分层",
        "",
        "- 静态拓扑／平凡与洁净 kicked 两级基准通过；洁净 N=80 的 W0、Wπ 与 p0=pπ=1 一致。",
        "- 正确无序协议的主积分器在 48 个能隙结果中给出 46 个有效结果，最近整数全部为 1；两个 r=0.05 的 0 支为 not_converged，未被改写为整数。",
        "- 两个未收敛类别的独立行列式相位绕数均为 1。它们说明主积分网格未收敛，不改变主结果状态，也不允许把未收敛记为 0。",
        "- 有限开链端点联合判据与体 winding 不等价。无序 0 模联合判据在 12 个实现中为 0/12 通过；不能据此宣称短链端点模全部通过。",
        "",
        "## 二、模型与必要修正",
        "",
        "Majorana 基为 (a1,b1,…,aN,bN)，S=diag(−1,+1,…)。TBC 只给 N→1 闭合键附加 exp(iθ)。对称时间帧为：",
        "",
        r"$$U_{step}(t)=F(t)H\quad(0<t<T),\qquad U_{step}(T)=H F(T)H,\qquad U_{step}(0)=I.$$",
        "",
        "周期化采用酉 Schur 分解及端点、半周期 chiral 共同筛选的能支：",
        "",
        r"$$\phi_{eff,val}=2\varepsilon-|\phi|,\qquad \phi_{eff,cond}=|\phi|-2\pi,$$",
        "",
        r"$$W_\varepsilon=\left|\pm\frac{i}{2\pi}\int_{-\pi}^{\pi}\operatorname{Tr}[U_{\varepsilon}^{\pm}(\theta)^{-1}\partial_\theta U_{\varepsilon}^{\pm}(\theta)]\,d\theta\right|.$$",
        "",
        "无序的 K 矩阵 onsite 参数是 rβ；半 kick 旋转角也是 rβ，完整对称旋转角为 2rβ。早期把 2rβ 误作矩阵参数的结果已原样归入 diagnostics/double-kick/，详见 ERRATA.md，不用于本报告结论。",
        "",
        "## 三、静态与洁净基准",
        "",
        "| 算例 | 能隙 | winding 原始值 | 最近整数 | 最小体隙 |",
        "|:---|:---:|---:|---:|---:|",
    ]
    baseline_rows = [
        ("静态拓扑 ω=7", "0", BASELINE["static"]["topological_omega7"]["zero"]),
        ("静态拓扑 ω=7", "π", BASELINE["static"]["topological_omega7"]["pi"]),
        ("静态平凡 ω=17", "0", BASELINE["static"]["trivial_omega17"]["zero"]),
        ("静态平凡 ω=17", "π", BASELINE["static"]["trivial_omega17"]["pi"]),
        ("洁净 kicked N=80", "0", BASELINE["clean"]["zero"]),
        ("洁净 kicked N=80", "π", BASELINE["clean"]["pi"]),
    ]
    for name, target, row in baseline_rows:
        lines.append(f"| {name} | {target} | {fmt(row['value'], 12)} | {row['nearest_integer']} | {fmt(row['min_bulk_gap'])} |")
    lines += [
        "",
        "静态 μ0=2.5、ω=7 的 0 隙为 gapless_or_undefined，未记为 0。",
        "",
        "## 四、无序与均值汇总",
        "",
        "| r | 类型 | 能隙 | 有效数/4 | 整数频数 | 最小体隙 | 端点联合通过/4 |",
        "|---:|:---|:---:|---:|:---|---:|---:|",
    ]
    for row in DATA["summary"]:
        target = "0" if row["target"] == "zero" else "π"
        freq = "；".join(f"{key}:{value}" for key, value in row["nearest_integer_frequencies"].items())
        lines.append(
            f"| {row['strength']} | {LABELS[row['kind']]} | {target} | {row['valid_winding_count']}/4 | {freq} | {fmt(row['minimum_bulk_gap'])} | {row['endpoint_joint_pass_count']}/4 |"
        )
    lines += [
        "",
        "统计口径：同一强度的均匀均值控制是同一均匀链，虽然为配对列出 4 次，但不能当作 4 个独立随机样本；独立无序实现共 12 个。",
        "",
        "图 1 插入位置：无序汇总表之后、未收敛诊断之前。",
        "",
        "![图 1：逐实现 winding 与独立复核](disorder-winding.png)",
        "",
        "**图 1**　圆点为主积分有效结果；叉号为 not_converged；空心菱形为独立行列式复核。未收敛不记为整数。",
        "",
        "## 五、两个未收敛类别",
        "",
        "| r | seed | 能隙 | dθ≈0.05 原始值 | dθ≈0.025 原始值 | 主状态 | 独立行列式 |",
        "|---:|---:|:---:|---:|---:|:---|---:|",
    ]
    for row in DATA["realizations"]:
        for target in ("zero", "pi"):
            if row[target]["status"] == "ok":
                continue
            check = independent_for(row, target)
            grids = row[target]["rows"]
            lines.append(
                f"| {row['strength']} | {row['seed']} | {'0' if target == 'zero' else 'π'} | {fmt(grids[0]['value'], 10)} | {fmt(grids[1]['value'], 10)} | {row[target]['status']} | {fmt(check['independent']['value'], 10)} |"
            )
    lines += [
        "",
        "图 2 插入位置：未收敛诊断之后、独立验证与科学边界之前。",
        "",
        "![图 2：体隙与端点联合判据](disorder-gaps.png)",
        "",
        "**图 2**　纵轴为对数体隙；黑色外圈表示有限开链端点联合判据通过。体 winding 与端点权重／分离度必须分别解释。",
        "",
        "## 六、独立验证与科学边界",
        "",
        f"独立检查共 {INDEPENDENT['selected_count']} 项，其中失败类别 {INDEPENDENT['rejection_category_count']} 项；程序状态 passed={str(INDEPENDENT['passed']).lower()}。独立方法重建矢量无序传播、酉 Schur 周期化和 det(block) 相位展开，名义步长 0.0125。",
        "",
        "当前证据支持：在这 24 个有限二次型样本中，体 winding 主结果或独立失败类别复核均与 W0=Wπ=1 相容。它不证明任意无序强度、任意尺寸或热力学极限的稳健性，也不替代端点模的有限尺寸分析。",
        "",
        "复现：python research/floquet-bdg-tbc/run_verification.py。原始数据：disorder_results.json、disorder_results.csv、disorder_independent.json；错误协议勘误：ERRATA.md。",
        "",
        "原始依据：Mondal et al., arXiv:2207.11928v2, Eq. (7)–(16)；Thakurathi et al., arXiv:1303.2300v2。实现中的时间帧和能支由端点与 chiral 合同独立筛选，未将印刷公式记号差异静默当作复现成功。",
        "",
    ]
    (ROOT / "REPORT.md").write_text("\n".join(lines), encoding="utf-8")


def main():
    winding_figure()
    gap_figure()
    markdown()
    print("generated", "disorder-winding.png", "disorder-gaps.png", "REPORT.md")


if __name__ == "__main__":
    main()
