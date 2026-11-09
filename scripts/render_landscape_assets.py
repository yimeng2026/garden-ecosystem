"""Render the two factual figures used by the research report."""
from pathlib import Path
import collections
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "research" / "assets"
ASSETS.mkdir(parents=True, exist_ok=True)
plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

catalog = json.loads((ROOT / "research/project-catalog.json").read_text(encoding="utf-8"))
counts = collections.Counter(row["site"] for row in catalog["projects"])
sites = ["github", "gitlab", "huggingface", "codeberg", "gitee"]
values = [counts.get(site, 0) for site in sites]
fig, ax = plt.subplots(figsize=(10, 5.4), dpi=160)
colors = ["#315b7d", "#517a96", "#7194a6", "#93acb8", "#b4c2c8"]
bars = ax.bar(sites, values, color=colors, width=0.62)
ax.bar_label(bars, padding=5, fontsize=11)
ax.set_title("公开检索去重条目（候选池，含噪声）", fontsize=17, pad=16)
ax.set_xlabel("平台")
ax.set_ylabel("项目／模型条目数")
ax.spines[["top", "right"]].set_visible(False)
ax.grid(axis="y", alpha=0.18)
ax.set_axisbelow(True)
ax.text(0.5, -0.20, "Gitee 的搜索 API 空结果不代表无仓库；25 个 dpsnet 仓库另行全量核查。",
        ha="center", transform=ax.transAxes, fontsize=10, color="#4f5d66")
fig.tight_layout()
fig.savefig(ASSETS / "platform-coverage.png", bbox_inches="tight")
plt.close(fig)

image = Image.new("RGB", (1800, 940), "#f5f7f8")
draw = ImageDraw.Draw(image)
font_path = Path("C:/Windows/Fonts/msyh.ttc")
font = ImageFont.truetype(str(font_path), 32)
small = ImageFont.truetype(str(font_path), 24)
title = ImageFont.truetype(str(font_path), 44)


def centered(x: int, y: int, text: str, face: ImageFont.FreeTypeFont, color: str = "#1d303e") -> None:
    draw.text((x, y), text, font=face, fill=color, anchor="mm")


def box(rect: tuple[int, int, int, int], heading: str, lines: list[str], fill: str) -> None:
    draw.rounded_rectangle(rect, radius=20, fill=fill, outline="#7d96a4", width=3)
    x1, y1, x2, y2 = rect
    centered((x1 + x2) // 2, y1 + 45, heading, font)
    for index, line in enumerate(lines):
        centered((x1 + x2) // 2, y1 + 105 + 40 * index, line, small)


centered(900, 68, "千界花园：公共底座＋受控外部能力", title)
box((90, 140, 560, 340), "主花园既有层", ["蜂群 · 多供应商池", "会话 · SSE · 人工干预"], "#dceaf0")
box((690, 140, 1110, 340), "统一接入边界", ["脱敏接口 · 能力画像", "默认拒绝 · 真实健康状态"], "#e2ecdf")
box((1240, 140, 1710, 340), "自有公共底座", ["预算 · 门禁 · 事务", "检查点 · 评测 · 证据"], "#e8e2ef")
for x in (625, 1175):
    draw.line((x - 45, 240, x + 45, 240), fill="#4b7189", width=7)
    draw.polygon([(x + 45, 240), (x + 20, 225), (x + 20, 255)], fill="#4b7189")
box((100, 470, 800, 780), "公共证据链", ["动作指纹与一次性审批", "来源、种子、版本与检查点", "机器检查 ≠ 数值复现 ≠ 独立实验"], "#edf0f2")
box((1000, 470, 1700, 780), "外部能力（默认不可用）", ["Lean / LeanDojo / Pantograph", "OpenFOAM / 沙箱 / MCP / 世界模型", "健康检查 → 门禁 → 执行 → 分级回执"], "#f4e9dd")
draw.line((900, 360, 900, 435), fill="#4b7189", width=7)
draw.polygon([(900, 435), (885, 410), (915, 410)], fill="#4b7189")
centered(900, 850, "模拟与 mock 必须标注；失败、负结果和回滚失败均保留", font, "#6f443a")
image.save(ASSETS / "ecosystem-architecture.png", optimize=True)
for path in ASSETS.glob("*.png"):
    print(path.name, path.stat().st_size)
