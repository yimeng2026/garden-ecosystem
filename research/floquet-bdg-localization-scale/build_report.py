"""Build localization-scale figures and the data-bound Markdown report."""

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
DATA = json.loads((ROOT / "localization_scale.json").read_text(encoding="utf-8"))
plt.rcParams.update({
    "font.sans-serif": ["Microsoft YaHei", "SimHei", "Noto Sans CJK SC", "DejaVu Sans"],
    "axes.unicode_minus": False, "font.size": 10, "figure.dpi": 160,
})
COLORS = {(0.05, 0): "#8B3A3A", (0.1, 0): "#A25B3F", (0.05, 2): "#356A64", (0.05, 3): "#4E7E75", (0.1, 2): "#596B9A"}
LABELS = {(0.05, 0): "N.05s0", (0.1, 0): "N.1s0", (0.05, 2): "R.05s2", (0.05, 3): "R.05s3", (0.1, 2): "R.1s2"}
SIZES = (80, 160, 320)


def case_label(case):
    return LABELS[(case["strength"], case["seed"])]


def coverage_figure():
    fig, axes = plt.subplots(1, 2, figsize=(12, 5.5), constrained_layout=False)
    for case in DATA["cases"]:
        key = (case["strength"], case["seed"])
        for ax, metric in zip(axes, ("L50", "L90")):
            ax.plot(SIZES, [row[metric] for row in case["rows"]], marker="o", ms=7, lw=1.5, color=COLORS[key], label=case_label(case))
    for ax, metric in zip(axes, ("L50", "L90")):
        ax.set_xticks(SIZES)
        ax.set_xlabel("链长 N")
        ax.set_ylabel(f"{metric}（直接两端覆盖）")
        ax.grid(alpha=0.2)
        ax.legend(frameon=False, fontsize=8)
    fig.subplots_adjust(top=0.82, bottom=0.15, wspace=0.25)
    fig.suptitle("覆盖尾长：平台、增长与已测恢复必须分开", fontsize=16, y=0.97)
    fig.savefig(ROOT / "coverage-scale.png", bbox_inches="tight")
    plt.close(fig)


def diagnostics_figure():
    metrics = (("mass20", "固定 20 格点端点质量", False), ("edge_weight", "原 10% 端点权重", False), ("n_subspace_ipr", "N × 子空间 IPR", False), ("envelope", "包络拟合 R²", False))
    fig, axes = plt.subplots(2, 2, figsize=(12, 8), constrained_layout=False)
    for case in DATA["cases"]:
        key = (case["strength"], case["seed"])
        for ax, (metric, ylabel, _) in zip(axes.flat, metrics):
            values = [row[metric] if metric != "envelope" else row["envelope"]["r_squared"] for row in case["rows"]]
            ax.plot(SIZES, values, marker="o", ms=6, lw=1.3, color=COLORS[key], label=case_label(case))
    for ax, (_, ylabel, _) in zip(axes.flat, metrics):
        ax.set_xticks(SIZES)
        ax.set_xlabel("链长 N")
        ax.set_ylabel(ylabel)
        ax.grid(alpha=0.2)
    axes[1, 0].axhline(0.5, color="#777777", ls="--", lw=1)
    axes[1, 1].axhline(0.5, color="#777777", ls="--", lw=1)
    axes[0, 0].legend(frameon=False, fontsize=8)
    fig.subplots_adjust(top=0.86, bottom=0.12, hspace=0.35, wspace=0.25)
    fig.suptitle("端点质量、IPR 与低优度包络拟合的联合诊断", fontsize=16, y=0.98)
    fig.savefig(ROOT / "scale-diagnostics.png", bbox_inches="tight")
    plt.close(fig)


def fmt(value, digits=6):
    if value is None:
        return "—"
    if isinstance(value, str):
        return value
    return f"{value:.{digits}g}"


def markdown():
    lines = [
        "# Floquet-BdG 局域与恢复尺度分析",
        "",
        "> 日期：2026-11-11。范围：5 个案例、N=80/160/320 的 15 个基无关 rank-2 子空间 profile。本文不把下一诊断尺寸写成恢复预测，也不包含 N=640 计算。",
        "",
        "## 一、覆盖定义与判据",
        "",
        "对原 profile q，直接计算两端累计质量：",
        "",
        "$$C_m=\\sum_{j=0}^{m-1}q_j+\\sum_{j=N-m}^{N-1}q_j,\\qquad L_p=\\min\\{m:C_m\\geq p\\}.$$",
        "",
        "此前对平均序列 `(q+q[::-1])/2` 求累计会在 N/2 处恒得 0.5，不能作为 localization length。本报告改用上述直接两端和。",
        "",
        "恢复平台判据：最近两尺寸 L50 相对变化 ≤0.25、固定 20 格点端点质量比 ≥0.8、N=320 分离度 <0.1。包络 R²<0.5 时不得用指数恢复律。",
        "",
        "## 二、恢复分类与下一诊断尺寸",
        "",
        "| 案例 | 状态 | L50（80/160/320） | L90（80/160/320） | 下一诊断尺寸 | 解释 |",
        "|:---|:---|:---|:---|---:|:---|",
    ]
    for case in DATA["cases"]:
        a = case["assessment"]
        lines.append(f"| {case_label(case)} | {a['status']} | {[row['L50'] for row in case['rows']]} | {[row['L90'] for row in case['rows']]} | {a['next_size']} | {a['reason']} |")
    lines += [
        "",
        "N.1s0 的 L50 区间为 330–380，因此 N=400 是阈值边缘诊断；N.05s0 未满足平台条件，N=600 仅用于检验尾长是否继续增长。两者都不是恢复承诺，也没有选择 N=640 作为默认答案。",
        "",
        "图 1 插入位置：恢复分类之后、详细数值之前。",
        "",
        "![图 1：直接两端覆盖尾长](coverage-scale.png)",
        "",
        "**图 1**　直接两端覆盖 L50 与 L90。已恢复案例不自动等于短尾平台，未恢复案例也不等于拓扑消失。",
        "",
        "## 三、逐尺寸证据",
        "",
        "| 案例 | N | L50 | L90 | 固定20质量 | 中心20%质量 | N·IPR | 包络 R² |",
        "|:---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for case in DATA["cases"]:
        for row in case["rows"]:
            lines.append(f"| {case_label(case)} | {row['n']} | {row['L50']} | {row['L90']} | {fmt(row['mass20'])} | {fmt(row['center20_mass'])} | {fmt(row['n_subspace_ipr'])} | {fmt(row['envelope']['r_squared'])} |")
    lines += [
        "",
        "图 2 插入位置：逐尺寸证据之后、解释边界之前。",
        "",
        "![图 2：端点质量、IPR 与包络优度](scale-diagnostics.png)",
        "",
        "**图 2**　固定宽度端点质量、原端点权重、N·IPR 与包络拟合优度。虚线为相应阈值或参考线。",
        "",
        "## 四、解释边界与后续实验",
        "",
        "N.05s0 的 L50 从 21→31→51 增长，未满足平台条件；其包络 R² 最高仅约 0.188，不能给出恢复区间。N.1s0 满足机械平台条件，但 L90 仍从 36→71→129 增长，说明 90% 覆盖的尾部并不短，因此 N=400 只检验局部阈值穿越，不能证明整体局域化。",
        "",
        "三个已恢复案例保留 measured_recovered，不要求它们同时满足所有平台子条件。N=640 尚未计算；后续应先做 N=400 的阈值边缘诊断与 N=600 的尾长增长诊断，并沿用逐网格检查点。",
        "",
        "原始依据：floquet-bdg-disorder/profiles.npz 与 results.json；分析数据：localization_scale.json、localization_scale.csv。原始 profile 全部重新验证归一化和 N=320 端点权重一致性。",
        "",
    ]
    (ROOT / "REPORT.md").write_text("\n".join(lines), encoding="utf-8")


def main():
    coverage_figure()
    diagnostics_figure()
    markdown()
    print("generated coverage-scale.png scale-diagnostics.png REPORT.md")


if __name__ == "__main__":
    main()
