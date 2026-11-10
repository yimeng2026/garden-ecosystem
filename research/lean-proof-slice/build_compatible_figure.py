import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
data = json.loads((ROOT / "compatible-definitions.json").read_text(encoding="utf-8"))
plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
fig, (left, right) = plt.subplots(1, 2, figsize=(14, 6.5), facecolor="#F7F8FA", constrained_layout=True)
fig.suptitle("局部兼容清偿：两个定义通过 ≠ 全部问题解决", fontsize=20, fontweight="bold", color="#263238")
for ax, title, color in ((left, "A. 本切片已验证", "#2E6B57"), (right, "B. 仍然开放", "#8A4B4B")):
    ax.axis("off")
    ax.set_title(title, fontsize=16, fontweight="bold", color=color, pad=16)
left_rows = [
    ("Euler 常量", "Real.eulerMascheroniConstant"),
    ("ASCII 绑定", "lam；不使用 λ 作为变量"),
    ("Debye 类型", "omega0 : Real；debyeModel : Real -> Real"),
    ("真实编译", "2 个 rfl；退出码 0；无 sorryAx"),
]
for index, (label, value) in enumerate(left_rows):
    y = 0.87 - index * 0.205
    left.add_patch(plt.Rectangle((0.04, y - 0.11), 0.92, 0.14, transform=left.transAxes, facecolor="#E2F0E8", edgecolor="#8AAE9E"))
    left.text(0.07, y, label, transform=left.transAxes, fontsize=11, color="#455A64", va="center")
    left.text(0.93, y, value, transform=left.transAxes, fontsize=10.2, color="#245044", va="center", ha="right")
left.text(0.04, 0.02, "只验证定义展开与依赖，不验证物理有效性。", transform=left.transAxes, fontsize=11, color="#455A64")
right_rows = [
    ("原文件", "直译仍不兼容；未修改"),
    ("原三条定理", "sorryAx 审计不可用"),
    ("HasEquiv Real", "命题语义开放；禁止虚假实例"),
    ("物理与实验", "材料、数值和复现均未验证"),
]
for index, (label, value) in enumerate(right_rows):
    y = 0.87 - index * 0.205
    right.add_patch(plt.Rectangle((0.04, y - 0.11), 0.92, 0.14, transform=right.transAxes, facecolor="#F7E8E6", edgecolor="#C4A3A0"))
    right.text(0.07, y, label, transform=right.transAxes, fontsize=11, color="#455A64", va="center")
    right.text(0.93, y, value, transform=right.transAxes, fontsize=10.2, color="#7A3D3D", va="center", ha="right")
right.text(0.04, 0.02, "兼容清偿不是项目级证明完成。", transform=right.transAxes, fontsize=11, color="#8A4B4B")
fig.savefig(ROOT / "compatible-definitions.svg", format="svg")
fig.savefig(ROOT / "compatible-definitions.png", dpi=180)
plt.close(fig)
print(ROOT / "compatible-definitions.png")
