import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
data = json.loads((ROOT / "floquet-approximation.json").read_text(encoding="utf-8"))
plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
fig, (left, right) = plt.subplots(1, 2, figsize=(14, 6.5), facecolor="#F7F8FA", constrained_layout=True)
fig.suptitle("显式误差界：零误差关系已证明 ≠ Floquet 增强已证明", fontsize=20, fontweight="bold", color="#263238")
for ax, title, color in ((left, "A. 已验证的语义", "#2E6B57"), (right, "B. 未闭合的命题", "#8A4B4B")):
    ax.axis("off")
    ax.set_title(title, fontsize=16, fontweight="bold", color=color, pad=16)
left_rows = [
    ("DriveApprox", "|omega_drive - 2 * Delta / hbar| <= epsilon"),
    ("零误差推出精确等式", "driveApprox_zero_exact"),
    ("精确等式推出零误差", "driveApprox_of_exact"),
    ("真实编译", "3 个定理；退出码 0；无 sorryAx"),
]
for index, (label, value) in enumerate(left_rows):
    y = 0.87 - index * 0.205
    left.add_patch(plt.Rectangle((0.04, y - 0.11), 0.92, 0.14, transform=left.transAxes, facecolor="#E2F0E8", edgecolor="#8AAE9E"))
    left.text(0.07, y, label, transform=left.transAxes, fontsize=10.5, color="#455A64", va="center")
    left.text(0.93, y, value, transform=left.transAxes, fontsize=9.7, color="#245044", va="center", ha="right")
left.text(0.04, 0.02, "只证明误差语义，不宣称 Floquet 增强。", transform=left.transAxes, fontsize=11, color="#455A64")
right_rows = [
    ("HasEquiv Real", "未引入实例；不强行通过"),
    ("原文件", "直译仍不兼容；未修改"),
    ("Floquet 增强", "未证明 T_c_F > T_c_eq"),
    ("物理与实验", "材料、数值和复现均未验证"),
]
for index, (label, value) in enumerate(right_rows):
    y = 0.87 - index * 0.205
    right.add_patch(plt.Rectangle((0.04, y - 0.11), 0.92, 0.14, transform=right.transAxes, facecolor="#F7E8E6", edgecolor="#C4A3A0"))
    right.text(0.07, y, label, transform=right.transAxes, fontsize=10.5, color="#455A64", va="center")
    right.text(0.93, y, value, transform=right.transAxes, fontsize=9.7, color="#7A3D3D", va="center", ha="right")
right.text(0.04, 0.02, "语义切片不是项目级证明完成。", transform=right.transAxes, fontsize=11, color="#8A4B4B")
fig.savefig(ROOT / "floquet-approximation.svg", format="svg")
fig.savefig(ROOT / "floquet-approximation.png", dpi=180)
plt.close(fig)
print(ROOT / "floquet-approximation.png")
