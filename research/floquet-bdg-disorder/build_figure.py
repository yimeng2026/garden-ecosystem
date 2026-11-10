"""Plot all disorder verdicts and mean-matched comparisons without seed selection."""

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent
data = json.loads((ROOT / "results.json").read_text(encoding="utf-8"))
sizes = data["sizes"]
strengths = data["strengths"]
plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "Noto Sans CJK SC", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False
colors = {"zero": "#356A64", "pi": "#A25B3F"}
labels = {"zero": "0 模", "pi": "π 模"}
summary = {(row["n"], row["strength"], row["target"]): row for row in data["summary"]}
mean_summary = {(row["n"], row["strength"], row["target"]): row for row in data["mean_matched_summary"]}
fig, axes = plt.subplots(2, 2, figsize=(12, 8), facecolor="#FAFAF8", constrained_layout=True)
fig.suptitle("无序主检验未通过：平均驱动与无序涨落必须分开", fontsize=18, fontweight="bold", color="#293B40")

for ax, target, panel in ((axes[0, 0], "zero", "A"), (axes[0, 1], "pi", "B")):
    values = np.array([[summary[(n, r, target)]["pass_count"] / summary[(n, r, target)]["total"] for n in sizes] for r in strengths])
    image = ax.imshow(values, vmin=0, vmax=1, cmap="YlGnBu", aspect="auto")
    for i, r in enumerate(strengths):
        for j, n in enumerate(sizes):
            row = summary[(n, r, target)]
            text_color = "#F7F8FA" if values[i, j] > 0.55 else "#263238"
            ax.text(j, i, f"{row['pass_count']}/{row['total']}", ha="center", va="center", fontsize=10, color=text_color)
    ax.set(xticks=range(len(sizes)), xticklabels=[f"N={n}" for n in sizes], yticks=range(len(strengths)), yticklabels=[f"r={r}" for r in strengths], title=f"{panel}. {labels[target]}无序实现通过数")
    fig.colorbar(image, ax=ax, label="通过比例")

ax = axes[1, 0]
for target in ("zero", "pi"):
    disordered = [summary[(160, r, target)]["pass_count"] / 16 for r in strengths]
    uniform = [mean_summary[(160, r, target)]["pass_count"] / 16 for r in strengths]
    ax.plot(strengths, disordered, marker="o", lw=2, color=colors[target], label=f"{labels[target]}无序")
    ax.plot(strengths, uniform, marker="s", lw=1.7, ls="--", color=colors[target], alpha=0.65, label=f"{labels[target]}均匀均值")
ax.set(xticks=strengths, xlabel="无序强度 r", ylabel="联合判据通过比例", ylim=(-0.03, 1.05), title="C. N=160：无序与均匀均值对照")
ax.grid(True, alpha=0.2)
ax.legend(fontsize=8, ncol=2)

ax = axes[1, 1]
for target, marker in (("zero", "o"), ("pi", "s")):
    disordered = [row for row in data["realizations"] if row["n"] == 160 and row["strength"] == 0.1]
    uniform = [row for row in data["mean_matched"] if row["n"] == 160 and row["strength"] == 0.1]
    disordered.sort(key=lambda row: row["seed"])
    uniform.sort(key=lambda row: row["seed"])
    seeds = [row["seed"] for row in disordered]
    ax.plot(seeds, [row[target]["edge_weight"] for row in disordered], marker=marker, lw=1.6, color=colors[target], label=f"{labels[target]}无序")
    ax.plot(seeds, [row[target]["edge_weight"] for row in uniform], marker=".", lw=1.2, ls="--", color=colors[target], alpha=0.6, label=f"{labels[target]}均匀均值")
ax.axhline(0.5, color="#7C6A54", ls="--", lw=1)
ax.set(xticks=range(16), xlabel="固定实现 seed", ylabel="端点权重", ylim=(0, 1.02), title="D. N=160、r=0.1：全部 16 个实现")
ax.grid(True, alpha=0.2)
ax.legend(fontsize=8, ncol=2)
fig.text(0.5, -0.015, "not_supported 不等于无序单独破坏拓扑；主检验与 r=0.2 压力测试分开，所有实现保留。", ha="center", fontsize=10, color="#5D696B")
svg_path = ROOT / "disorder.svg"
fig.savefig(svg_path, format="svg", bbox_inches="tight")
svg_path.write_text("\n".join(line.rstrip() for line in svg_path.read_text(encoding="utf-8").splitlines()) + "\n", encoding="utf-8")
fig.savefig(ROOT / "disorder.png", dpi=180, bbox_inches="tight")
plt.close(fig)
print(ROOT / "disorder.png")
