import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
data = json.loads((ROOT / "proof-slice.json").read_text(encoding="utf-8"))
plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
fig, (left, right) = plt.subplots(1, 2, figsize=(14, 7), facecolor="#F7F8FA", constrained_layout=True)
fig.suptitle("真实编译：定义切片通过 ≠ 原文件通过", fontsize=21, fontweight="bold", color="#263238")
for ax, title, color in ((left, "A. 清洁定义切片", "#2E6B57"), (right, "B. 原文件与证明债务", "#8A4B4B")):
    ax.axis("off")
    ax.set_title(title, fontsize=16, fontweight="bold", color=color, pad=16)

left_rows = [
    ("3 个定义", "allenDynesTc / H3S / LaH10"),
    ("3 个证明", "仅 rfl 定义展开"),
    ("编译结果", "退出码 0"),
    ("公理依赖", "仅标准三公理"),
    ("sorryAx", "无"),
]
for index, (label, value) in enumerate(left_rows):
    y = 0.88 - index * 0.16
    left.add_patch(plt.Rectangle((0.04, y - 0.09), 0.92, 0.12, transform=left.transAxes, facecolor="#E2F0E8", edgecolor="#8AAE9E"))
    left.text(0.07, y, label, transform=left.transAxes, fontsize=11, color="#455A64", va="center")
    left.text(0.93, y, value, transform=left.transAxes, fontsize=10.5, color="#245044", va="center", ha="right")
left.text(0.04, 0.02, "只验证定义，不验证物理有效性。", transform=left.transAxes, fontsize=11, color="#455A64")

right_rows = [
    ("eulerMascheroni", "未定义"),
    ("λ / ω_D", "标识符与绑定错误"),
    ("HasEquiv Real", "实例缺失"),
    ("既有证明债务", "3 处 sorry"),
    ("原定理审计", "编译失败，不可用"),
]
for index, (label, value) in enumerate(right_rows):
    y = 0.88 - index * 0.16
    right.add_patch(plt.Rectangle((0.04, y - 0.09), 0.92, 0.12, transform=right.transAxes, facecolor="#F7E8E6", edgecolor="#C4A3A0"))
    right.text(0.07, y, label, transform=right.transAxes, fontsize=11, color="#455A64", va="center")
    right.text(0.93, y, value, transform=right.transAxes, fontsize=10.5, color="#7A3D3D", va="center", ha="right")
right.text(0.04, 0.02, "原文件未修改；不以切片替代原证明。", transform=right.transAxes, fontsize=11, color="#8A4B4B")
fig.savefig(ROOT / "lean-proof-slice.svg", format="svg")
fig.savefig(ROOT / "lean-proof-slice.png", dpi=180)
plt.close(fig)
print(ROOT / "lean-proof-slice.png")
