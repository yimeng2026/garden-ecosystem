"""Plot homogeneous pass maps and exact mean/fluctuation categories."""

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent
data = json.loads((ROOT / "results.json").read_text(encoding="utf-8"))
sensitivity = json.loads((ROOT / "sensitivity.json").read_text(encoding="utf-8"))
disorder = json.loads((ROOT.parent / "floquet-bdg-disorder" / "results.json").read_text(encoding="utf-8"))
amplitudes = data["amplitudes"]
sizes = [80, 160, 320]
plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "Noto Sans CJK SC", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False
colors = {"zero": "#356A64", "pi": "#A25B3F"}
labels = {"zero": "0 模", "pi": "π 模"}
fig, axes = plt.subplots(2, 2, figsize=(12, 8), facecolor="#FAFAF8", constrained_layout=True)
fig.suptitle("均匀 kick 参数图与无序涨落分解", fontsize=18, fontweight="bold", color="#293B40")

for ax, target, panel in ((axes[0, 0], "zero", "A"), (axes[0, 1], "pi", "B")):
    values = np.array([[next(row for row in data["grid"] if row["n"] == n and row["a"] == a)[target]["joint_pass"] for a in amplitudes] for n in sizes], dtype=float)
    ax.imshow(values, vmin=0, vmax=1, cmap="YlGnBu", aspect="auto")
    for i, n in enumerate(sizes):
        for j, a in enumerate(amplitudes):
            row = next(row for row in data["grid"] if row["n"] == n and row["a"] == a)
            value = values[i, j]
            ax.text(j, i, "通" if value else "×", ha="center", va="center", fontsize=11, color="#F7F8FA" if value else "#5E6668")
    ax.axvline(0, color="#7C6A54", ls=":", lw=1.4)
    ax.axvline(amplitudes.index(np.pi / 14), color="#7C6A54", ls="--", lw=1.4)
    ax.set(xticks=range(len(amplitudes)), xticklabels=[f"{a:.3g}" for a in amplitudes], yticks=range(len(sizes)), yticklabels=[f"N={n}" for n in sizes], xlabel="均匀 kick 振幅 a", title=f"{panel}. {labels[target]}联合判据通过图")
    ax.tick_params(axis="x", labelrotation=55)
    ax.text(0.2, -0.75, "a=0: U(0)=+I", fontsize=8, color="#5D696B")
    ax.text(6.2, -0.75, "a_c=π/14: U(π)=−I", fontsize=8, color="#5D696B")

ax = axes[1, 0]
for target, marker in (("zero", "o"), ("pi", "s")):
    disordered_rows = sorted((row for row in disorder["realizations"] if row["n"] == 160 and row["strength"] == 0.1), key=lambda row: row["seed"])
    uniform_rows = sorted((row for row in disorder["mean_matched"] if row["n"] == 160 and row["strength"] == 0.1), key=lambda row: row["seed"])
    seeds = [row["seed"] for row in disordered_rows]
    ax.plot(seeds, [row[target]["edge_weight"] for row in disordered_rows], marker=marker, lw=1.6, color=colors[target], label=f"{labels[target]}无序")
    ax.plot(seeds, [row[target]["edge_weight"] for row in uniform_rows], marker=".", lw=1.2, ls="--", color=colors[target], alpha=0.6, label=f"{labels[target]}均匀均值")
ax.axhline(0.5, color="#7C6A54", ls="--", lw=1)
ax.set(xticks=range(16), xlabel="固定实现 seed", ylabel="端点权重", ylim=(0, 1.02), title="C. N=160、r=0.1：无序与均匀均值")
ax.grid(True, alpha=0.2)
ax.legend(fontsize=8, ncol=2)

ax = axes[1, 1]
categories = ["both_pass", "fluctuation_sensitive", "uniform_fails", "fluctuation_assisted"]
category_labels = ["均通过", "涨落敏感", "均匀失败", "涨落助通过"]
category_colors = ["#356A64", "#A25B3F", "#7A8588", "#8B6F8E"]
groups = [(160, "zero", "N160 0"), (160, "pi", "N160 π"), (320, "zero", "N320 0"), (320, "pi", "N320 π")]
bottom = np.zeros(len(groups))
for category, label, color in zip(categories, category_labels, category_colors):
    values = []
    for n, target, _ in groups:
        total = 16 if n == 160 else 4
        count = sum(row["count"] for row in sensitivity["summary"] if row["n"] == n and row["strength"] == 0.1 and row["target"] == target and row["category"] == category)
        values.append(count / total)
    ax.bar(range(len(groups)), values, bottom=bottom, color=color, label=label)
    bottom += values
ax.set(xticks=range(len(groups)), xticklabels=[label for _, _, label in groups], ylim=(0, 1), ylabel="实现比例", title="D. r=0.1：机械结果类别分解")
ax.legend(fontsize=8, ncol=2)
ax.grid(True, axis="y", alpha=0.2)
fig.text(0.5, -0.015, "联合候选通过不等于拓扑证明；机械类别不等于拓扑生灭。原始 not_supported 与全尺寸未决均保留。", ha="center", fontsize=10, color="#5D696B")
svg_path = ROOT / "kick-map.svg"
fig.savefig(svg_path, format="svg", bbox_inches="tight")
svg_path.write_text("\n".join(line.rstrip() for line in svg_path.read_text(encoding="utf-8").splitlines()) + "\n", encoding="utf-8")
fig.savefig(ROOT / "kick-map.png", dpi=180, bbox_inches="tight")
plt.close(fig)
print(ROOT / "kick-map.png")
