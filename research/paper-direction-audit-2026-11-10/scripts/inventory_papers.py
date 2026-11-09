"""Build a deduplicated, evidence-oriented inventory of research manuscripts.

This script reads only selected paths inside the current workspace. It does not
infer novelty or completion from keywords; those markers are surfaced for the
subsequent human/model review pass.
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

AUDIT_DIR = Path(__file__).resolve().parents[1]
WORKSPACE = Path(__file__).resolve().parents[4]
PROVIDER = WORKSPACE / ".worktrees" / "provider-main-integration"
TOE = WORKSPACE / "toe-sylva-audit"
FRONTIER = WORKSPACE / "frontier-breakthrough"

HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
FUTURE = re.compile(r"未来|展望|局限|限制|未完成|后续|开放问题|future|limitation|outlook|open problem", re.I)
CONCLUSION = re.compile(r"结论|总结|conclusion", re.I)
NOVELTY = re.compile(r"原创|首次|新颖|本文提出|我们提出|novel|new contribution|we propose|we introduce", re.I)
DEBT = re.compile(r"TODO|TBD|FIXME|placeholder|占位|未实现|尚未|未完成|sorry|axiom|postulate|待补|待验证", re.I)
REFERENCE = re.compile(r"https?://|doi\b|arxiv|\[[0-9]+\]", re.I)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def title_of(path: Path, text: str) -> str:
    if path.suffix == ".tex":
        match = re.search(r"\\title(?:\[[^]]*\])?\{([^}]+)\}", text)
        if match:
            return match.group(1).strip()
    for line in text.splitlines():
        match = HEADING.match(line)
        if match:
            return match.group(2).strip()
    return path.stem


def section(text: str, pattern: re.Pattern[str], limit: int = 12000) -> str:
    lines = text.splitlines()
    for index, line in enumerate(lines):
        match = HEADING.match(line)
        if not match or not pattern.search(match.group(2)):
            continue
        level = len(match.group(1))
        body = []
        for following in lines[index + 1:]:
            next_heading = HEADING.match(following)
            if next_heading and len(next_heading.group(1)) <= level:
                break
            body.append(following)
        return "\n".join(body).strip()[:limit]
    return ""


def excerpts(text: str, pattern: re.Pattern[str], maximum: int = 12) -> list[str]:
    result = []
    for number, line in enumerate(text.splitlines(), 1):
        if pattern.search(line):
            result.append(f"L{number}: {line.strip()[:500]}")
            if len(result) >= maximum:
                break
    return result


def kind_of(source: str, relative: Path) -> str:
    lower = relative.as_posix().lower()
    name = relative.name.lower()
    if "submission_covers" in lower:
        return "cover_letter"
    if "回应与评论" in lower or any(token in name for token in ("reply", "回应", "回复", "辩护")):
        return "response_or_commentary"
    if source == "frontier":
        return "research_report"
    if "total_report" in name or "math_physics_worldview" in name:
        return "integrated_research_report"
    if name in {"contents.md", "contributors.md", "open_problems.md", "errata.md", "duplicate_index.md", "subdir_duplicate_report.md"}:
        return "index_or_meta"
    if any(token in name for token in ("audit", "hallucination", "lessons", "report", "审计", "评价")):
        return "audit_or_meta"
    if "protocol" in name or "协议" in name:
        return "methodology"
    if "综述" in name or "survey" in name or "review" in name:
        return "survey"
    if "readme" in name or "index" in name or "dashboard" in name:
        return "index_or_meta"
    return "manuscript"


def record(source: str, path: Path, root: Path) -> dict:
    raw = path.read_bytes()
    text = raw.decode("utf-8-sig")
    relative = path.relative_to(root)
    parent = path.parent
    broad_parents = {
        WORKSPACE,
        TOE / "papers",
        PROVIDER / "papers" / "topo-quantum-internet",
        FRONTIER / "docs",
    }
    recursive_assets = parent not in broad_parents
    candidates = parent.rglob("*") if recursive_assets else parent.glob("*")
    asset_files = [p for p in candidates if p.is_file() and ".venv" not in p.parts]
    scripts = sorted(p.relative_to(parent).as_posix() for p in asset_files
                     if p.suffix == ".py" and p.name.startswith(("verify", "validate", "analyze", "simulate")))
    figures = sum(1 for p in asset_files if p.suffix.lower() in {".png", ".svg", ".jpg", ".jpeg"})
    lean_files = sum(1 for p in asset_files if p.suffix == ".lean")
    return {
        "id": f"{source}:{relative.as_posix()}",
        "source": source,
        "path": path.relative_to(WORKSPACE).as_posix(),
        "relative_path": relative.as_posix(),
        "kind": kind_of(source, relative),
        "title": title_of(path, text),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "bytes": len(raw),
        "lines": len(text.splitlines()),
        "headings": [match.group(2).strip() for line in text.splitlines() if (match := HEADING.match(line))][:100],
        "abstract": section(text, re.compile(r"摘要|abstract", re.I), 5000),
        "future_or_limitations": section(text, FUTURE),
        "conclusion": section(text, CONCLUSION),
        "novelty_markers": excerpts(text, NOVELTY),
        "debt_markers": excerpts(text, DEBT),
        "reference_lines": sum(1 for line in text.splitlines() if REFERENCE.search(line)),
        "scripts": scripts,
        "figure_count": figures,
        "lean_file_count": lean_files,
        "content_read": True,
    }


def selected_records() -> list[dict]:
    records = []
    topo = PROVIDER / "papers" / "topo-quantum-internet"
    for path in sorted(topo.glob("*.md")):
        if path.name not in {"all_papers_export.md", "README.md"}:
            records.append(record("provider-topo", path, PROVIDER))
    qec = PROVIDER / "papers" / "qec-ftqc"
    for path in sorted(qec.rglob("*.md")):
        if "完整合并版" not in path.name and path.name != "README.md":
            records.append(record("provider-qec", path, PROVIDER))
    for path in [
        PROVIDER / "research" / "physical-intuition" / "MATH_PHYSICS_WORLDVIEW_2026.md",
        PROVIDER / "research" / "physical-intuition" / "TOTAL_PROJECT_2026-11-08" / "TOTAL_REPORT.md",
    ]:
        if path.is_file():
            records.append(record("physical-intuition", path, PROVIDER))
    root_patterns = [
        "*_学术论文_最终版.md",
        "SYLVAPaper_arXiv_2026-06-24_COMPLETE.tex",
        "科学计算与高性能计算_综述.agent.final.md",
    ]
    for pattern in root_patterns:
        for path in sorted(WORKSPACE.glob(pattern)):
            records.append(record("workspace-manuscript", path, WORKSPACE))
    for path in sorted((FRONTIER / "docs").glob("*.md")):
        records.append(record("frontier", path, FRONTIER))
    for path in sorted((TOE / "papers").rglob("*")):
        if path.is_file() and path.suffix.lower() in {".md", ".tex"} and path.name.lower() != "readme.md":
            if "完整合并版" not in path.name and path.name != "all_papers_export.md":
                records.append(record("toe-sylva", path, TOE))
    return records


def write_outputs(records: list[dict]) -> None:
    records.sort(key=lambda item: (item["source"], item["relative_path"]))
    duplicates = []
    by_hash = defaultdict(list)
    for item in records:
        by_hash[item["sha256"]].append(item["id"])
    for digest, ids in sorted(by_hash.items()):
        if len(ids) > 1:
            duplicates.append({"sha256": digest, "ids": ids})
    payload = {
        "schema": "paper-direction-inventory-v1",
        "workspace": str(WORKSPACE),
        "record_count": len(records),
        "source_counts": dict(sorted(Counter(item["source"] for item in records).items())),
        "kind_counts": dict(sorted(Counter(item["kind"] for item in records).items())),
        "exact_duplicate_groups": duplicates,
        "interpretation_boundary": "Keywords and file metadata are review leads, not judgments of novelty, validity, or completion.",
        "records": records,
    }
    (AUDIT_DIR / "inventory.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    fields = ["id", "kind", "title", "path", "lines", "bytes", "reference_lines", "figure_count", "lean_file_count", "scripts", "sha256"]
    with (AUDIT_DIR / "inventory.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for item in records:
            row = dict(item)
            row["scripts"] = ";".join(item["scripts"])
            writer.writerow(row)
    lines = [
        "# 论文与研究方向盘点底账",
        "",
        "> 这是正文级清单，不是新颖性或正确性的最终裁决。合订本、README、重复导出和纯 Lean 文件不计为独立论文。",
        "",
        f"- 实际读取：**{len(records)} 份**",
        f"- 完全重复组：**{len(duplicates)} 组**",
        "- 后续裁决字段：方向角色、证据等级、外部对应、未竟工作、下一步可执行实验。",
        "",
        "## 来源与类型统计",
        "",
        "| 来源 | 份数 |",
        "|---|---:|",
    ]
    lines.extend(f"| {source} | {count} |" for source, count in payload["source_counts"].items())
    lines.extend(["", "| 类型 | 份数 |", "|---|---:|"])
    lines.extend(f"| {kind} | {count} |" for kind, count in payload["kind_counts"].items())
    lines.extend(["", "## 完全重复组", ""])
    if duplicates:
        for group in duplicates:
            lines.append(f"- `{group['sha256'][:12]}`：" + "；".join(f"`{item}`" for item in group["ids"]))
    else:
        lines.append("本轮所选权威文件中未发现字节级完全重复。")
    lines.extend([
        "",
        "## 逐份清单",
        "",
        "| ID | 类型 | 标题 | 行数 | 图 | 验证脚本 | 未竟标记数 |",
        "|---|---|---|---:|---:|---:|---:|",
    ])
    for item in records:
        title = item["title"].replace("|", "\\|")
        lines.append(f"| `{item['id']}` | {item['kind']} | {title} | {item['lines']} | {item['figure_count']} | {len(item['scripts'])} | {len(item['debt_markers'])} |")
    lines.extend([
        "",
        "## 证据边界",
        "",
        "“未竟标记数”只用于定位需要阅读的段落，不能直接等同于未完成工作数量；出现 `axiom` 可能是在讨论公理方法，出现“原创”也不能证明外部新颖性。逐篇裁决必须回到摘要、结论、局限、验证脚本及外部文献。",
        "",
    ])
    (AUDIT_DIR / "INVENTORY.md").write_text("\n".join(lines), encoding="utf-8", newline="\n")
    print(json.dumps({"records": len(records), "sources": payload["source_counts"], "kinds": payload["kind_counts"], "exact_duplicate_groups": len(duplicates)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    write_outputs(selected_records())
