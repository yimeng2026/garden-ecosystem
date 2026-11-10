"""Plot only the recorded/recomputed Floquet-BdG numerical evidence."""

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from floquet_bdg import candidate_modes, kicked_floquet, quasienergy_spectrum, site_weights

ROOT = Path(__file__).resolve().parent
data = json.loads((ROOT / "results.json").read_text(encoding="utf-8"))
sizes = data["sizes"]
plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "Noto Sans CJK SC", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False
colors = {"zero": "#356A64", "pi": "#A25B3F"}
labels = {"zero": "0 模候选（λ=+1）", "pi": "π 模候选（λ=−1）"}

fig, axes = plt.subplots(2, 2, figsize=(12, 8), facecolor="#FAFAF8", constrained_layout=True)
fig.suptitle("有限 Kitaev 链：π 候选通过；0 候选分离仍未闭合", fontsize=18, fontweight="bold", color="#293B40")

ax = axes[0, 0]
archive = np.load(ROOT / "spectra.npz")
phase = archive["n160_phase"] / np.pi
ax.scatter(phase, np.zeros_like(phase), s=12, color="#5E7479", alpha=0.65, label="N=160 全部本征值")
for target, y in (("zero", 0.035), ("pi", 1.035)):
    row = data["size_studies"][-1][target]
    ax.scatter(np.array(row["phase"]) / np.pi, np.full(2, y), s=65, color=colors[target], label=labels[target], zorder=3)
ax.axvline(0, color=colors["zero"], lw=1, ls="--")
ax.axvline(1, color=colors["pi"], lw=1, ls="--")
ax.set(xlabel="arg(λ) / π", ylim=(-0.08, 0.11), yticks=[], title="A. 实际 Floquet 相位谱")
ax.legend(fontsize=8, loc="upper center", ncol=2)
ax.spines[["left", "right", "top"]].set_visible(False)

ax = axes[0, 1]
for target in ("zero", "pi"):
    distances = [max(row[target]["distances"]) for row in data["size_studies"]]
    ax.plot(sizes, distances, marker="o", color=colors[target], lw=2, label=labels[target])
    for n, distance in zip(sizes, distances):
        ax.annotate(f"{distance:.1e}", (n, distance), xytext=(0, 6), textcoords="offset points", ha="center", fontsize=8)
ax.set(xscale="log", yscale="log", xticks=sizes, xticklabels=[str(n) for n in sizes], xlabel="格点数 N", ylabel="max |λ−target|", title="B. 候选距离随尺寸下降")
ax.grid(True, which="both", alpha=0.2)
ax.legend(fontsize=9)

ax = axes[1, 0]
for target in ("zero", "pi"):
    weights = [min(row[target]["edge_weights"]) for row in data["size_studies"]]
    ax.plot(sizes, weights, marker="o", color=colors[target], lw=2, label=labels[target])
ax.axhline(0.5, color="#7C6A54", ls="--", lw=1.2, label="预注册局域阈值 0.5")
ax.set(xticks=sizes, xlabel="格点数 N", ylabel="两端各 10% 格点最小权重", ylim=(0, 1.03), title="C. 端点局域性随尺寸增强")
ax.grid(True, alpha=0.2)
ax.legend(fontsize=9)

ax = axes[1, 1]
u, period = kicked_floquet(160, 2.5, 0.2, 7.0)
spectrum = quasienergy_spectrum(u, period)
weights = site_weights(spectrum["eigenvectors"], 160)
for target, value in (("zero", 1.0), ("pi", -1.0)):
    candidate = candidate_modes(spectrum, 160, value)
    index = candidate["indices"][0]
    ax.plot(np.arange(1, 161), weights[:, index], color=colors[target], lw=1.6, label=labels[target])
ax.set(xlabel="格点 j", ylabel="概率权重", title="D. N=160 候选空间分布")
ax.grid(True, alpha=0.2)
ax.legend(fontsize=9)
fig.text(0.5, -0.015, "二次型、无相互作用／耗散；解析端点计数不等于有限尺寸边缘模证明，更不是材料 Tc 或实验验证。", ha="center", fontsize=10, color="#5D696B")
svg_path = ROOT / "quasienergy.svg"
fig.savefig(svg_path, format="svg", bbox_inches="tight")
# Matplotlib emits trailing spaces in path data; strip them without changing geometry.
svg_path.write_text("\n".join(line.rstrip() for line in svg_path.read_text(encoding="utf-8").splitlines()) + "\n", encoding="utf-8")
fig.savefig(ROOT / "quasienergy.png", dpi=180, bbox_inches="tight")
plt.close(fig)
print(ROOT / "quasienergy.png")
