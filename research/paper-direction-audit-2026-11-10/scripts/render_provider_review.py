"""Render and validate the 31-paper direction review."""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from urllib.parse import quote

AUDIT = Path(__file__).resolve().parents[1]
WORKSPACE = Path(__file__).resolve().parents[4]
inventory = json.loads((AUDIT / "inventory.json").read_text(encoding="utf-8"))
review = json.loads((AUDIT / "provider-review.json").read_text(encoding="utf-8"))
by_id = {item["id"]: item for item in inventory["records"]}
records = review["records"]
expected = {item["id"] for item in inventory["records"] if item["source"] in {"provider-topo", "provider-qec"}}
actual = {item["id"] for item in records}
if actual != expected or len(records) != len(expected):
    raise SystemExit(json.dumps({"missing": sorted(expected - actual), "extra": sorted(actual - expected), "count": len(records)}, ensure_ascii=False))


def local_citation(item: dict) -> str:
    absolute = WORKSPACE / item["path"]
    target = f"kimi-cite://text?path={quote(str(absolute))}&text={quote(item['title'])}"
    return f"[{Path(item['relative_path']).stem}]({target} \"citation\")"


def web(url: str, label: str = "原始来源") -> str:
    return f"[{label}](kimi-cite://web?url={quote(url, safe='')} \"citation\")"


counts = Counter(item["priority"] for item in records)
lines = [
    "# 主花园两套量子系列：逐篇方向与未竟工作初审",
    "",
    "> 范围：拓扑量子互联网 16 篇、QEC–FTQC 15 篇；合订本不重复计数。这里把“项目内能否成为独立方向”与“外部是否新颖”分开，避免把系列编号误当成创新证明。",
    "",
    "## 总体裁决",
    "",
    f"31 篇全部完成摘要、结论、局限与配套资产的首轮核查。优先级为 **P0 {counts['P0']} 篇、P1 {counts['P1']} 篇、P2 {counts['P2']} 篇**。P0 表示中心命题存在矛盾、验证逻辑缺口或数据出处不足，必须先修正再扩展；P1 表示有明确可执行的研究下一步；P2 表示以教学、维护和真实数据接入为主。",
    "",
    "两个系列都不应整体宣称为“新理论”。基础模型与综述主要承担导航作用；TQIPS／GEM、三层统计验证协议、拓扑 ISA、qLDPC 构造、解码硬件、错误预算和标准化治理可以成为独立项目方向。它们能否形成外部新颖贡献，取决于是否提供公开算法、统一对照、原始数据与可复核实验，而不是篇幅或图表数量。",
    "",
    "## 外部基线如何改变裁决",
    "",
    "- Google 的 below-threshold 实验是 d=7、101 个物理比特、0.143%／周期的真实硬件结果；本仓库的公式曲线不能借用其证据等级。" + web("https://arxiv.org/abs/2408.13687", "arXiv"),
    "- Stim＋PyMatching 支持真实逐 shot 电路级蒙特卡洛，文档示例在特定电路噪声下得到约 0.7% 阈值，说明噪声模型必须与阈值一起报告。" + web("https://pymatching.readthedocs.io/", "PyMatching 文档"),
    "- Majorana 2 的约 20 秒宇称寿命有 2026 年预印本，但公开文献仍在讨论平庸态模拟和拓扑判定，不能把该数字等同于非阿贝尔统计已被独立确认。" + web("https://arxiv.org/html/2606.03884v1", "寿命预印本") + "、" + web("https://arxiv.org/pdf/2606.23183", "讨论文献"),
    "- 2024 年已有超导处理器 Fibonacci 任意子编织演示，因此本系列只能在梯子模型、协议或编译上寻求增量。" + web("https://cqi.tsinghua.edu.cn/en/info/1018/2930.htm", "清华大学"),
    "- qLDPC 已进入多平台实验与后验解码复核阶段，论文十四的“首个验证尚在未来”必须更新。" + web("https://arxiv.org/html/2609.26958v1", "实验数据复核") + "、" + web("https://arxiv.org/html/2503.22071v2", "离子链研究"),
    "- 魔术态研究已包含 cultivation 实验：40 倍误差降低、保留 8% 尝试；旧蒸馏比较仍有价值，但已不再是唯一前沿。" + web("https://arxiv.org/abs/2512.13908", "arXiv"),
    "- AM–SC 角点模和编织已有多篇工作，且原作者明确留下 T 门、双比特门、无序和测量协议等开放项，适合作为本系列的直接对照。" + web("https://arxiv.org/html/2506.08095v1", "2025 年工作") + "、" + web("https://arxiv.org/html/2611.07645v1", "2026 年工作"),
    "- 量子网络已有 IRTF 多平面架构与协议草案，TQIPS 必须给出接口级差异，不能只改五层名称。" + web("https://datatracker.ietf.org/doc/draft-irtf-qirg-qi-multiplane-arch/01/", "IETF Datatracker"),
    "- 实时解码已有 FPGA 实现与产业路线，论文中的延迟模型需要与真实系统对照，不能把 ASIC 写成唯一道路。" + web("https://www.riverlane.com/blog/why-the-decoder-is-the-beating-heart-of-qec", "Riverlane"),
    "",
    "## 拓扑量子互联网：16 篇逐篇裁决",
    "",
    "| 论文 | 方向角色 | 外部新颖性初判 | 未竟事业与下一步 | 优先级 |",
    "|---|---|---|---|---|",
]
for item in [entry for entry in records if entry["id"].startswith("provider-topo:")]:
    source = by_id[item["id"]]
    lines.append(f"| {local_citation(source)} | {item['role']} | {item['external_novelty']} | {item['unfinished']} | **{item['priority']}** |")
lines.extend([
    "",
    "## QEC–FTQC：15 篇逐篇裁决",
    "",
    "| 论文 | 方向角色 | 外部新颖性初判 | 未竟事业与下一步 | 优先级 |",
    "|---|---|---|---|---|",
])
for item in [entry for entry in records if entry["id"].startswith("provider-qec:")]:
    source = by_id[item["id"]]
    lines.append(f"| {local_citation(source)} | {item['role']} | {item['external_novelty']} | {item['unfinished']} | **{item['priority']}** |")
lines.extend([
    "",
    "## P0 风险登记：先修正，再发展",
    "",
    "| 论文 | 当前主要风险 |",
    "|---|---|",
])
for item in [entry for entry in records if entry["priority"] == "P0"]:
    source = by_id[item["id"]]
    lines.append(f"| {local_citation(source)} | {item['risk']} |")
lines.extend([
    "",
    "## 首轮执行顺序",
    "",
    "1. **先修内部一致性**：统一 p+ip 相图、陈数符号、物理比特计数、阈值百分数和延迟单位；每项保留原稿、修订理由与证据链接。",
    "2. **建立真实阈值基准**：以 Stim＋PyMatching 重算表面码，再扩展颜色码、qLDPC 与多解码器；保存电路、DEM、种子、shots、置信区间和原始输出。",
    "3. **把候选创新写成算法或协议**：优先三层统计验证、复合编织脉冲、TQIPS／GEM 和拓扑 ISA；每项必须有零模型、基线和可证伪条件。",
    "4. **更新外部前沿**：qLDPC、cultivation、Majorana 2、AM–SC、实时解码与 IRTF 架构均按当前状态重写，不把预测写成事实。",
    "5. **最后再扩写论文**：只有完成上述证据闭环的方向才进入新论文；其余稿件保持综述、复现或勘误状态。",
    "",
    "本轮裁决不是对 31 篇论文的最终外部查新。后续仍需对 644 份 TOE 文档、67 份前沿报告、两份物理直觉总报告和 7 份根目录独立稿件应用同一标准，并把完全重复与近重复版本映射到唯一权威稿。",
    "",
])
(AUDIT / "PROVIDER_REVIEW.md").write_text("\n".join(lines), encoding="utf-8", newline="\n")
print(json.dumps({"reviewed": len(records), "priorities": counts, "output": "PROVIDER_REVIEW.md"}, ensure_ascii=False, default=dict, indent=2))
