"""Create bounded reading packets from the paper inventory."""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

AUDIT = Path(__file__).resolve().parents[1]
OUT = AUDIT / "review-packets"
OUT.mkdir(exist_ok=True)
records = json.loads((AUDIT / "inventory.json").read_text(encoding="utf-8"))["records"]
groups = defaultdict(list)
for record in records:
    groups[record["source"]].append(record)

manifest = []
for source, items in sorted(groups.items()):
    for start in range(0, len(items), 10):
        batch = items[start:start + 10]
        name = f"{source}-{start // 10 + 1:02d}.md"
        lines = [f"# 阅读包：{source}（{start + 1}–{start + len(batch)}）", ""]
        for item in batch:
            lines.extend([
                f"## {item['title']}",
                "",
                f"- ID：`{item['id']}`",
                f"- 类型：{item['kind']}；行数：{item['lines']}；图：{item['figure_count']}；Lean：{item['lean_file_count']}",
                f"- 脚本：{'; '.join(item['scripts']) if item['scripts'] else '未登记'}",
                f"- SHA-256：`{item['sha256']}`",
                "",
                "### 摘要节选",
                "",
                item["abstract"][:1400] or "未识别到独立摘要节；后续需读开头与结论。",
                "",
                "### 局限、未来或开放问题节选",
                "",
                item["future_or_limitations"][:2600] or "未识别到独立局限／未来节；后续需读结论与正文。",
                "",
                "### 结论节选",
                "",
                item["conclusion"][:1800] or "未识别到独立结论节。",
                "",
                "### 原创性措辞线索（不是新颖性证明）",
                "",
                *[f"- {line}" for line in item["novelty_markers"][:4]],
                "",
                "### 债务措辞线索（不是缺陷裁决）",
                "",
                *[f"- {line}" for line in item["debt_markers"][:4]],
                "",
            ])
        (OUT / name).write_text("\n".join(lines), encoding="utf-8", newline="\n")
        manifest.append({"source": source, "file": name, "count": len(batch), "ids": [item["id"] for item in batch]})
(AUDIT / "review-packets.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
print(json.dumps({"packets": len(manifest), "sources": {source: (len(items) + 9) // 10 for source, items in groups.items()}}, ensure_ascii=False, indent=2))
