"""Generate the seven-case N=320 comparison report and figures."""

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent
DATA = json.loads((ROOT / "n320_zero.json").read_text(encoding="utf-8"))
INDEPENDENT = json.loads((ROOT / "n320_independent.json").read_text(encoding="utf-8"))
plt.rcParams.update({
    "font.sans-serif": ["Microsoft YaHei", "SimHei", "Noto Sans CJK SC", "DejaVu Sans"],
    "axes.unicode_minus": False, "font.size": 10, "figure.dpi": 160,
})
COLORS = {"recovered": "#356A64", "not_recovered": "#A25B3F", "uniform_control": "#596B9A"}
LABELS = {"recovered": "端点恢复", "not_recovered": "端点未恢复", "uniform_control": "均匀控制"}


def label(row):
    prefix = "R" if row["endpoint_class"] == "recovered" else "N" if row["endpoint_class"] == "not_recovered" else "U"
    return f"{prefix}{row['strength']}s{row['seed']}"


def independent_for(row):
    return next(item for item in INDEPENDENT["checks"] if item["case"]["strength"] == row["strength"] and item["case"]["seed"] == row["seed"] and item["case"]["kind"] == row["kind"])


def group_summary():
    groups = []
    for kind in ("recovered", "not_recovered", "uniform_control"):
        rows = [row for row in DATA["rows"] if row["endpoint_class"] == kind]
        groups.append({
            "class": kind, "count": len(rows),
            "winding_valid": sum(row["zero"]["status"] == "ok" for row in rows),
            "winding_one": sum(row["zero"]["nearest_integer"] == 1 for row in rows),
            "endpoint_pass": sum(row["endpoint"]["zero"]["joint_pass"] for row in rows),
            "min_gap": min(row["zero"]["min_bulk_gap"] for row in rows),
        })
    return groups


def figure_winding():
    rows = DATA["rows"]
    x = np.arange(len(rows))
    fig, axes = plt.subplots(2, 1, figsize=(11, 7), constrained_layout=False)
    for index, row in enumerate(rows):
        color = COLORS[row["endpoint_class"]]
        axes[0].scatter(index, row["zero"]["value"], s=62, color=color, zorder=3)
        check = independent_for(row)
        axes[0].scatter(index, check["independent"]["value"], s=115, marker="D", facecolors="none", edgecolors="#2E5C55", linewidths=1.1)
        axes[1].scatter(index, row["zero"]["min_bulk_gap"], s=62, color=color)
    axes[0].set_ylim(0.99985, 1.00003)
    axes[0].set_ylabel("W0 原始值")
    axes[0].grid(axis="y", alpha=0.2)
    axes[1].set_yscale("log")
    axes[1].set_ylabel("最小 0 体隙")
    axes[1].set_xticks(x, [label(row) for row in rows], rotation=35, ha="right")
    axes[1].grid(axis="y", which="both", alpha=0.2)
    for ax in axes:
        ax.set_xlim(-0.7, len(rows) - 0.3)
    handles = [plt.Line2D([0], [0], marker="o", color="w", markerfacecolor=COLORS[k], markersize=8, label=LABELS[k]) for k in COLORS]
    handles.append(plt.Line2D([0], [0], marker="D", color="#2E5C55", markerfacecolor="none", lw=0, markersize=9, label="独立行列式复核"))
    fig.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, 0.94), ncol=4, frameon=False)
    fig.subplots_adjust(top=0.82, bottom=0.18, hspace=0.30)
    fig.suptitle("N=320：七例主积分与独立复核均为 W0=1", fontsize=16, y=0.98)
    fig.savefig(ROOT / "n320-winding.png", bbox_inches="tight")
    plt.close(fig)


def figure_endpoints():
    rows = DATA["rows"]
    x = np.arange(len(rows))
    fig, axes = plt.subplots(2, 1, figsize=(11, 7), constrained_layout=False)
    for index, row in enumerate(rows):
        endpoint = row["endpoint"]["zero"]
        color = COLORS[row["endpoint_class"]]
        axes[0].scatter(index, endpoint["edge_weight"], s=68, color=color)
        axes[1].scatter(index, max(endpoint["separation_ratios"]), s=68, color=color)
    axes[0].axhline(0.5, color="#777777", ls="--", lw=1, label="端点权重阈值 0.5")
    axes[0].set_ylim(0, 1)
    axes[0].set_ylabel("端点权重")
    axes[0].grid(axis="y", alpha=0.2)
    axes[0].legend(frameon=False, loc="lower right")
    axes[1].axhline(0.1, color="#777777", ls="--", lw=1, label="分离度阈值 0.1")
    axes[1].set_yscale("log")
    axes[1].set_ylabel("最大分离比（对数坐标）")
    axes[1].set_xticks(x, [label(row) for row in rows], rotation=35, ha="right")
    axes[1].grid(axis="y", which="both", alpha=0.2)
    axes[1].legend(frameon=False)
    for ax in axes:
        ax.set_xlim(-0.7, len(rows) - 0.3)
    handles = [plt.Line2D([0], [0], marker="o", color="w", markerfacecolor=COLORS[k], markersize=8, label=LABELS[k]) for k in COLORS]
    fig.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, 0.94), ncol=3, frameon=False)
    fig.subplots_adjust(top=0.82, bottom=0.18, hspace=0.30)
    fig.suptitle("R：恢复；N：未恢复；U：均匀控制", fontsize=15, y=0.98)
    fig.savefig(ROOT / "n320-endpoints.png", bbox_inches="tight")
    plt.close(fig)


def fmt(value, digits=6):
    if value is None:
        return "—"
    if isinstance(value, str):
        return value
    return f"{value:.{digits}g}"


def markdown(groups):
    lines = [
        "# N=320 Floquet-BdG TBC 定向 0 隙对照",
        "",
        "> 日期：2026-11-11。范围：7 个定向有限二次型算例及原始 expm＋Schur 独立复核。本文不宣称任意无序、热力学极限或材料实验结论。",
        "",
        "## 一、分组结论",
        "",
        "| 分组 | 算例数 | 主 W0 有效数 | W0=1 数 | 端点联合通过数 | 最小体隙 |",
        "|:---|---:|---:|---:|---:|---:|",
    ]
    for row in groups:
        lines.append(f"| {LABELS[row['class']]} | {row['count']} | {row['winding_valid']} | {row['winding_one']} | {row['endpoint_pass']} | {fmt(row['min_gap'])} |")
    lines += [
        "",
        "七例主积分均为有效 W0=1，七项独立行列式复核均为 1。恢复与未恢复样本不能只用端点是否通过来解释体不变量。",
        "",
        "图 1 插入位置：分组结论之后、逐例对照之前。",
        "",
        "![图 1：N320 winding 与体隙](n320-winding.png)",
        "",
        "**图 1**　七例主积分和独立行列式复核一致；R 为恢复、N 为未恢复、U 为均匀控制。",
        "",
        "## 二、逐例体与端点对照",
        "",
        "| 分组 | r | seed | W0 原始值 | 最小体隙 | 端点权重 | 最大分离比 | 端点通过 |",
        "|:---|---:|---:|---:|---:|---:|---:|:---:|",
    ]
    for row in DATA["rows"]:
        endpoint = row["endpoint"]["zero"]
        lines.append(f"| {LABELS[row['endpoint_class']]} | {row['strength']} | {row['seed']} | {fmt(row['zero']['value'], 12)} | {fmt(row['zero']['min_bulk_gap'])} | {fmt(endpoint['edge_weight'])} | {fmt(max(endpoint['separation_ratios']))} | {str(endpoint['joint_pass'])} |")
    lines += [
        "",
        "图 2 插入位置：逐例对照表之后、独立复核之前。",
        "",
        "![图 2：端点权重与分离度](n320-endpoints.png)",
        "",
        "**图 2**　两个未恢复样本均在端点权重阈值 0.5 以下，但分离度通过；体 W0 仍为 1。",
        "",
        "## 三、独立复核与解释边界",
        "",
        "| 分组 | r | seed | 主状态／整数 | 独立状态／整数 | 独立原始值 |",
        "|:---|---:|---:|:---|:---|---:|",
    ]
    for row in INDEPENDENT["checks"]:
        case = row["case"]
        lines.append(f"| {LABELS[case['endpoint_class']]} | {case['strength']} | {case['seed']} | {row['production_status']}/{row['production_nearest_integer']} | {row['independent']['status']}/{row['independent']['nearest_integer']} | {fmt(row['independent']['value'], 10)} |")
    lines += [
        "",
        "三个恢复样本的体 winding 与端点候选一致；两个未恢复样本仍显示体 W0=1 与端点权重不足并存。由此，有限尺寸交叉假说得到加强，但体边对应并未对所有样本闭合。",
        "",
        "下一步不应直接盲目扫描 N=640，而应先利用子空间 IPR、端点权重和尾部长度估计各未恢复样本的局域／恢复尺度，再选择能区分尺度的尺寸。",
        "",
        "复现：python research/floquet-bdg-tbc/run_n320.py --merge-only；python research/floquet-bdg-tbc/verify_n320.py --merge-only。原始证据：n320_zero.json、n320_independent.json 及逐例独立文件。",
        "",
    ]
    (ROOT / "N320.md").write_text("\n".join(lines), encoding="utf-8")


def main():
    if not DATA.get("complete") or len(DATA["rows"]) != 7 or not INDEPENDENT.get("passed") or INDEPENDENT.get("selected_count") != 7:
        raise ValueError("N=320 evidence is incomplete")
    groups = group_summary()
    (ROOT / "n320_summary.json").write_text(json.dumps({"groups": groups}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    figure_winding()
    figure_endpoints()
    markdown(groups)
    print("generated n320-winding.png n320-endpoints.png N320.md n320_summary.json")


if __name__ == "__main__":
    main()
