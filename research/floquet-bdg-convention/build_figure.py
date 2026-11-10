"""Plot the corrected Floquet-BdG topology and open-chain evidence."""

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent
data = json.loads((ROOT / "results.json").read_text(encoding="utf-8"))
curve = np.load(ROOT / "bloch_curve.npz")
sizes = data["sizes"]
plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "Noto Sans CJK SC", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False
colors = {"zero": "#356A64", "pi": "#A25B3F"}
labels = {"zero": "0 模候选", "pi": "π 模候选"}
fig, axes = plt.subplots(2, 2, figsize=(12, 8), facecolor="#FAFAF8", constrained_layout=True)
fig.suptitle("Fock 修正后：W=2；大小尺寸候选一致，短链局域仍受限", fontsize=18, fontweight="bold", color="#293B40")

ax = axes[0, 0]
ax.plot(curve["n_z"], curve["n_y"], color="#356A64", lw=1.8, label="主算例 Bloch 轨迹")
ax.scatter([0], [0], color="#A25B3F", s=32, label="原点")
ax.set(xlabel="n_z", ylabel="n_y", title="A. Floquet 有效矢量轨迹：W=2")
ax.set_aspect("equal", adjustable="box")
ax.grid(True, alpha=0.2)
ax.legend(fontsize=9)

ax = axes[0, 1]
rows = data["winding"]["rows"]
nk = [row["nk"] for row in rows]
w = [row["winding"] for row in rows]
ax.plot(nk, w, marker="o", lw=2, color="#356A64", label="主算例 W=2")
ax.axhline(2, color="#6B7779", ls="--", lw=1)
ax.set(xscale="log", xticks=nk, xticklabels=[str(n) for n in nk], ylim=(1.8, 2.2), xlabel="动量网格 Nk", ylabel="winding", title="B. 动量网格收敛")
ax.xaxis.set_minor_locator(matplotlib.ticker.NullLocator())
ax.xaxis.set_major_formatter(matplotlib.ticker.ScalarFormatter())
ax.grid(True, which="major", alpha=0.2)
ax.legend(fontsize=9)

ax = axes[1, 0]
for target in ("zero", "pi"):
    distances = [max(study[target]["distances"]) for study in data["size_studies"]]
    ax.plot(sizes, distances, marker="o", lw=2, color=colors[target], label=labels[target])
    for n, distance in zip(sizes, distances):
        ax.annotate(f"{distance:.1e}", (n, distance), xytext=(0, 6), textcoords="offset points", ha="center", fontsize=8)
ax.set(yscale="log", xticks=sizes, xlabel="格点数 N", ylabel="max |λ−target|", title="C. 修正后候选距离随尺寸下降")
ax.grid(True, which="both", alpha=0.2)
ax.legend(fontsize=9)

ax = axes[1, 1]
for target in ("zero", "pi"):
    weights = [min(study[target]["edge_weights"]) for study in data["size_studies"]]
    ax.plot(sizes, weights, marker="o", lw=2, color=colors[target], label=labels[target])
ax.axhline(0.5, color="#7C6A54", ls="--", lw=1.2, label="旧联合判据阈值 0.5")
ax.set(xticks=sizes, xlabel="格点数 N", ylabel="两端各 10% 格点最小权重", ylim=(0, 1.03), title="D. 短链端点局域限制仍存在")
ax.grid(True, alpha=0.2)
ax.legend(fontsize=9)
fig.text(0.5, -0.015, "体拓扑与大尺寸候选一致，不等于全尺寸判据通过；无相互作用／耗散，不是材料 Tc 或实验验证。", ha="center", fontsize=10, color="#5D696B")
svg_path = ROOT / "topology.svg"
fig.savefig(svg_path, format="svg", bbox_inches="tight")
svg_path.write_text("\n".join(line.rstrip() for line in svg_path.read_text(encoding="utf-8").splitlines()) + "\n", encoding="utf-8")
fig.savefig(ROOT / "topology.png", dpi=180, bbox_inches="tight")
plt.close(fig)
print(ROOT / "topology.png")
