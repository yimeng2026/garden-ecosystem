"""Plot tail, envelope and basis-invariant IPR evidence."""

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent
data = json.loads((ROOT / "results.json").read_text(encoding="utf-8"))
sizes = data["sizes"]
plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "Noto Sans CJK SC", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False
colors = {"zero": "#356A64", "pi": "#A25B3F"}
labels = {"zero": "0 模", "pi": "π 模"}
fig, axes = plt.subplots(2, 2, figsize=(12, 8), facecolor="#FAFAF8", constrained_layout=True)
fig.suptitle("短链 regime 获三尺度证据；全尺寸旧判据不变", fontsize=18, fontweight="bold", color="#293B40")

ax = axes[0, 0]
for target in ("zero", "pi"):
    weights = [study[target]["edge_weights"][0] for study in data["size_studies"]]
    ax.plot(sizes, weights, marker="o", lw=2, color=colors[target], label=labels[target])
ax.axhline(0.5, color="#7C6A54", ls="--", lw=1.2, label="原端点阈值 0.5")
ax.set(xticks=sizes, xlabel="格点数 N", ylabel="两端各 10% 格点权重", ylim=(0, 1.04), title="A. 长链边缘权重趋近 1")
ax.grid(True, alpha=0.2)
ax.legend(fontsize=9)

ax = axes[0, 1]
centers = [(n1 + n2) / 2 for n1, n2 in zip(sizes, sizes[1:])]
for target in ("zero", "pi"):
    lengths = [row["xi_tail"] for row in data["tail_estimates"][target]]
    ax.plot(centers, lengths, marker="o", lw=2, color=colors[target], label=labels[target])
ax.set(xticks=centers, xticklabels=[f"{a}/{b}" for a, b in zip(sizes, sizes[1:])], xlabel="相邻尺寸 N1/N2", ylabel="ξ_tail（格点）", ylim=(0, 14), title="B. 尾部亏损估计趋稳")
ax.grid(True, alpha=0.2)
ax.legend(fontsize=9)

ax = axes[1, 0]
for target in ("zero", "pi"):
    first = [study[target]["subspace_ipr"] for study in data["size_studies"]]
    second = [study[target]["second_pair_subspace_ipr"] for study in data["size_studies"]]
    ax.plot(sizes, first, marker="o", lw=2, color=colors[target], label=f"{labels[target]}第一对")
    ax.plot(sizes, second, marker="s", lw=1.6, ls="--", color=colors[target], alpha=0.7, label=f"{labels[target]}第二对")
ax.set(yscale="log", xticks=sizes, xlabel="格点数 N", ylabel="基无关子空间 I2", title="C. 第一对稳定、第二对近似 1/N 衰减")
ax.grid(True, which="both", alpha=0.2)
ax.legend(fontsize=8, ncol=2)

ax = axes[1, 1]
for target in ("zero", "pi"):
    lengths = [row["xi_env"] for row in data["envelope_fits"][target]]
    ax.plot(sizes, lengths, marker="o", lw=2, color=colors[target], label=labels[target])
ax.set(xticks=sizes, xlabel="格点数 N", ylabel="ξ_env（格点）", ylim=(0, 30), title="D. 镜像包络拟合长度")
ax.grid(True, alpha=0.2)
ax.legend(fontsize=9)
fig.text(0.5, -0.015, "短链 regime 支持不等于热力学极限证明；不修改全尺寸 inconclusive，不推出材料 Tc 或实验结论。", ha="center", fontsize=10, color="#5D696B")
svg_path = ROOT / "localization.svg"
fig.savefig(svg_path, format="svg", bbox_inches="tight")
svg_path.write_text("\n".join(line.rstrip() for line in svg_path.read_text(encoding="utf-8").splitlines()) + "\n", encoding="utf-8")
fig.savefig(ROOT / "localization.png", dpi=180, bbox_inches="tight")
plt.close(fig)
print(ROOT / "localization.png")
