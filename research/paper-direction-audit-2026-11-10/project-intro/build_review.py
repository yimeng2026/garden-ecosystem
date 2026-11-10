"""Build final project-intro audit and organized 44-document coverage report."""

import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

AUDIT = Path(__file__).resolve().parent
INVENTORY = json.loads((AUDIT / "sources/coverage-inventory.json").read_text(encoding="utf-8"))
BATCH_ORDER = [
    "main-claims", "theory-breakthrough", "validation-materials", "isotope-dft",
    "dmrg-qec", "data-governance", "handbook-chapters", "room-temp-methods",
    "technical-docs", "magazine-design", "project-intro",
]


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def assessment(source_id, title, direction_ids, role, unfinished, next_step):
    return {
        "id": source_id,
        "title": title,
        "represents_new_theory": False,
        "direction_ids": direction_ids,
        "role": role,
        "unfinished": unfinished,
        "next": next_step,
    }


def build_data():
    directions = [
        {
            "id": "coverage_governance",
            "role": "目录、证据导航、批次血缘与 44 份覆盖图",
            "closed": "前十批 40 份与本批 4 份已逐路径核对，遗漏和重复均为空。",
            "unfinished": "原目录遗漏 12–21、PRL 和不可用链接尚未在原目录修复。",
            "next": "以机器生成的覆盖图作为导航事实源，记录批次、共享方向、哈希和开放状态。",
        },
        {
            "id": "conditional_formalization",
            "role": "把必然性草案拆成假设、定义、证明债务和编译验收",
            "closed": "admit/sorry、M1–M5 待实现、精确路径缺失和不会报错措辞已定位。",
            "unfinished": "定义、M1–M5、证明、编译、数值案例和物理映射均未闭合。",
            "next": "保留 0.1-alpha 草案级，先定义最小命题并真实编译；禁止以 sorry 换取不会报错。",
        },
        {
            "id": "handbook_reference_governance",
            "role": "手册版本、日期、资产元数据和参考文献可用性",
            "closed": "版本分歧、时间矛盾、24／0 条文献和原手册元数据已核清。",
            "unfinished": "手册视觉、文献补齐、现代关键条目、版本血缘和引用验收未完成。",
            "next": "冻结版本清单，修复时间线，补齐并校验 BibTeX，再验收页数、图件与公式。",
        },
        {
            "id": "public_communication",
            "role": "杂志策划、公众预期和科学传播边界",
            "closed": "策划的栏目、视觉与互动方向已保留，科学措辞和媒介边界已连接前批审计。",
            "unfinished": "首刊标题、真实内容、互动可访问性和实际发布物未验收。",
            "next": "以条件性科学表述制作样章，模拟互动明确标记，不把策划案当理论或成品。",
        },
    ]
    documents = [
        assessment("directory_index", "00-目录索引", ["coverage_governance"], "项目导航与推荐阅读路线", "遗漏 12–21，PRL 和不可用增强文献／Lean 路线未修正。", "由覆盖图生成真实目录，并为每条路线附证据状态和未竟工作。"),
        assessment("project_intro", "01-项目说明", ["conditional_formalization"], "0.1-alpha 必然性形式化草案", "H1–H6、M1–M5、证明、编译和版本血缘未闭合，且有不会报错措辞。", "删除编译保证，建立最小可编译命题和证明债务清单。"),
        assessment("handbook_intro", "02-手册说明", ["handbook_reference_governance"], "手册结构、读者与参考文献入口", "2025-04 早于 2025-10 内容，完美实验叙事和资产元数据未验收。", "核对版本时间，按证据等级改写并修复文献和原手册验收。"),
        assessment("magazine_plan", "03-杂志简介", ["public_communication"], "科技人文杂志策划任务书", "首刊标题、真实内容、AR／长按和发布资产仍是策划或愿景。", "保留创意，使用条件性标题并制作可访问样章，不称新物理理论。"),
    ]
    corrections = [
        {"id": "index_omissions", "severity": "P1", "finding": "目录只列 01–11，遗漏 12–21 的资料收集与技术复盘。", "action": "以 44 份覆盖图补齐真实目录，保留原目录版本和修改留痕。"},
        {"id": "prl_missing", "severity": "P1", "finding": "目录写主论文加 Nature／Science／arXiv／PRL 四版本，但 PRL 未找到。", "action": "改为当前实际版本清单，PRL 标未竟或缺失，不写已存在。"},
        {"id": "necessity_overclaim", "severity": "P0", "finding": "项目说明以严格数学框架和必然性为主线，但证明与物理映射未闭合。", "action": "保持探索性假说和条件命题，标题与摘要不得超过证明状态。"},
        {"id": "lean_paths", "severity": "P1", "finding": "理论文档、所称 Lean 与 M1–M5 精确路径未找到。", "action": "建立真实模块索引；未找到路径不得作为可编译或已交付证据。"},
        {"id": "sorry_compile_claim", "severity": "P0", "finding": "项目说明同时承认 admit/sorry 并声称使用它们确保不会报错。", "action": "删除保证；以真实编译命令、退出码和证明债务报告替代。"},
        {"id": "readme_divergence", "severity": "P1", "finding": "原 README 为 v7.33，组织后项目说明为 0.1-alpha，内容并不相同。", "action": "分开版本血缘，不把 v7.33 的较审慎声明自动回填到旧草案。"},
        {"id": "handbook_timeline", "severity": "P1", "finding": "手册说明标 2025 年 4 月更新，却包含 2025 年 10 月突破。", "action": "核对实际生成和修改时间，只标元数据矛盾，不判造假。"},
        {"id": "handbook_asset", "severity": "P1", "finding": "原手册 DOCX 存在，但 Pages=1、Words=0、媒体=0、OMML=false。", "action": "不以文件大小推断约 50 页或图文并茂；重新渲染并检查页数、图件和公式。"},
        {"id": "base_bib_gaps", "severity": "P1", "finding": "基础文献有 24 条和 5 处占位，缺少 Song、Semenok 与 PNAS 关键标识。", "action": "补全并校验条目、DOI／arXiv、证据角色和撤回状态，不能只增加数量。"},
        {"id": "enhanced_bib_unusable", "severity": "P0", "finding": "目录推荐的增强文献文件仅 22 字节、0 条 BibTeX。", "action": "从推荐阅读移除直至生成可解析文献库；文件存在不等于可用。"},
        {"id": "experimental_narrative", "severity": "P0", "finding": "手册说明使用完美对应、历史实现和 13 次从偶然到必然的叙事。", "action": "按 Song／Semenok／PNAS 的证据角色改写，保留独立复现与直接磁测量待办。"},
        {"id": "magazine_expectation", "severity": "P2", "finding": "杂志首刊标题和互动策划可能提前放大科学结论与完成感。", "action": "标题改为条件性表达，模拟互动标注，提供非手势路径和可访问样章。"},
    ]
    return {
        "schema": "project-intro-organized-coverage-audit-v1",
        "date": "2026-11-10",
        "scope": "目录、3 份项目介绍及 organized 44 份 Markdown 覆盖；只审计，不修改原文。",
        "sources": INVENTORY["sources"],
        "source_lineage": {
            "research_program_count": 1,
            "new_theory_count": 0,
            "development_direction_count": 4,
            "decision": "4 份文档分别承担导航、形式化草案、手册与公众策划，不独立构成新理论；44 份覆盖完成不等于研究闭合。",
        },
        "directions": directions,
        "document_assessments": documents,
        "coverage": INVENTORY["coverage"],
        "evidence": INVENTORY["evidence"],
        "corrections": corrections,
        "open_boundaries": {
            "organized_44_coverage_complete": True,
            "scientific_validation_complete": False,
            "all_unfinished_work_completed": False,
            "index_updated": False,
            "reference_library_ready": False,
            "lean_proof_complete": False,
            "production_ready": False,
            "whole_repository_research_complete": False,
        },
        "figure": {
            "svg": "organized-coverage-evidence.svg",
            "png": "organized-coverage-evidence.png",
            "labels": ["44／44", "40＋4", "增强 BibTeX 0 条", "Pages=1／Words=0", "12–21 未入目录"],
            "caption": "图 1　44 份文档覆盖与仍然开放的科学、文献和交付边界",
            "insert_after": "覆盖总览表",
            "insert_before": "4 份文档逐篇裁决",
            "completion_percentage_plotted": False,
        },
        "verification_scope": {
            "source_documents_modified": False,
            "new_lean_or_experiment": False,
            "original_handbook_visual_reviewed": False,
            "whole_repository_beyond_44_reviewed": False,
        },
    }


def build_figure(data):
    plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False
    fig = plt.figure(figsize=(15, 9), facecolor="#F7F8FA", constrained_layout=True)
    grid = fig.add_gridspec(1, 2, width_ratios=[1.25, 1])
    left = fig.add_subplot(grid[0, 0])
    right = fig.add_subplot(grid[0, 1])
    fig.suptitle("44 份覆盖完成 ≠ 科学研究闭合", fontsize=23, fontweight="bold", color="#263238")

    counts = [data["coverage"]["batch_counts"][batch] for batch in BATCH_ORDER]
    labels = ["主论文／末两章", "理论／突破", "实验／材料", "同位素／多层", "DMRG／QEC", "数据治理", "手册前三章", "方法／Lean／SI", "技术文档", "杂志设计", "目录／介绍"]
    colors = ["#78909C"] * 10 + ["#7E57C2"]
    y = np.arange(len(BATCH_ORDER))
    bars = left.barh(y, counts, color=colors, edgecolor="#546E7A")
    for bar, value in zip(bars, counts):
        left.text(value + 0.18, bar.get_y() + bar.get_height() / 2, str(value), va="center", fontsize=10, fontweight="bold")
    left.set_yticks(y, labels)
    left.invert_yaxis()
    left.set_xlim(0, 13)
    left.set_xlabel("")
    left.set_title("A. 前十批 40 份＋本批 4 份＝44 份", fontsize=15, fontweight="bold", color="#37474F", pad=15)
    left.grid(axis="x", alpha=0.18)
    left.text(0.02, 0.02, "实际 44 个路径；uncovered=[]；duplicates=[]；覆盖≠科学验证", transform=left.transAxes, fontsize=10.5, color="#455A64")

    right.axis("off")
    right.set_title("B. 覆盖后仍未闭合的证据门", fontsize=15, fontweight="bold", color="#37474F", pad=15)
    cards = [
        ("目录", "12–21 未列入；PRL 未找到", "#FCE8E6"),
        ("基础 BibTeX", "24 条 · 5 处占位 · 缺现代关键条目", "#FFF4D6"),
        ("增强 BibTeX", "0 条 · 22 字节 · 不可用", "#FCE8E6"),
        ("形式化", "admit/sorry；M1–M5 与精确路径未找到", "#FCE8E6"),
        ("版本", "v7.33 ≠ 0.1-alpha；2025-04 早于 2025-10", "#FFF4D6"),
        ("原手册资产", "Pages=1／Words=0；媒体 0；OMML=false", "#E4EEF5"),
    ]
    for index, (label, value, color) in enumerate(cards):
        y = 0.89 - index * 0.14
        right.add_patch(plt.Rectangle((0.03, y - 0.085), 0.94, 0.11, transform=right.transAxes, facecolor=color, edgecolor="#B0BEC5"))
        right.text(0.06, y, label, transform=right.transAxes, fontsize=10.5, color="#455A64", va="center")
        right.text(0.94, y, value, transform=right.transAxes, fontsize=9.8, color="#263238", va="center", ha="right")
    right.text(0.03, 0.015, "前十批另有 64 个 false 开放状态项（含交叉重复）。", transform=right.transAxes, fontsize=10, color="#8A4B4B")
    fig.savefig(AUDIT / data["figure"]["svg"], format="svg")
    fig.savefig(AUDIT / data["figure"]["png"], dpi=180)
    plt.close(fig)


def build_markdown(data):
    lines = [
        "# 目录、项目介绍与 44 份文档覆盖图审计",
        "",
        "> 2026-11-10。只读审计，不修改原文。**覆盖完成不等于研究闭合。**",
        "",
        "## 一、覆盖裁决与四个方向",
        "",
        data["source_lineage"]["decision"],
        "",
        "实际 44 个 Markdown 路径：前十批 40 份，本批 4 份，即 **40＋4＝44／44**；`uncovered=[]`，`duplicates=[]`。",
        "",
        "| 方向 | 已闭合的局部审计 | 未竟工作与下一步 |",
        "|:--|:--|:--|",
    ]
    for row in data["directions"]:
        lines.append(f"| `{row['id']}`：{row['role']} | {row['closed']} | {row['unfinished']} **下一步：**{row['next']} |")
    lines += ["", "## 二、批次覆盖与证据图", "", "| 批次 | 覆盖数 | 前批 false 开放状态项（含重叠） |", "|:--|--:|--:|"]
    for batch in BATCH_ORDER:
        lines.append(f"| `{batch}` | {data['coverage']['batch_counts'][batch]} | {data['coverage']['batch_open_false'].get(batch, '本批')} |")
    lines += [
        "",
        "前十批共有 64 个 false 开放状态项，彼此可能重叠，不能解释为 64 个独立科学任务。",
        "",
        "![图 1：44 份文档覆盖与开放边界](organized-coverage-evidence.svg)",
        "",
        "**图件插入顺序：图 1 位于覆盖总览表之后、4 份文档逐篇裁决之前。**",
        "",
        "## 三、4 份文档逐篇裁决",
        "",
        "| 文档 | 方向 | 角色 | 未竟工作与下一步 |",
        "|:--|:--|:--|:--|",
    ]
    for row in data["document_assessments"]:
        lines.append(f"| {row['title']} | {'、'.join(f'`{item}`' for item in row['direction_ids'])} | {row['role']} | {row['unfinished']} **下一步：**{row['next']} |")
    lines += [
        "",
        "## 四、目录、形式化、手册与文献证据",
        "",
        "- 目录遗漏 12–21；PRL 未找到。增强文献虽被推荐，但当前文件只有 22 字节、**0 条** BibTeX。",
        "- 基础文献有 **24 条** BibTeX 和 5 处占位，未找到 `2510.01273`、`2605.29985`、`2401840121`。",
        "- 项目说明包含 admit/sorry 和“不会报错”；理论文档、所称 Lean 和 M1–M5 精确路径未找到。",
        "- 原 README 为 v7.33，组织后项目说明为 0.1-alpha，两者不是同一版本。",
        "- 手册说明的 2025 年 4 月早于其中 2025 年 10 月内容；只标版本时间矛盾。",
        "- 原手册 DOCX 存在，但应用元数据 Pages=1、Words=0，媒体=0、OMML=false；约 50 页未据此验证。",
        "",
        "## 五、十二项分级勘误",
        "",
        "| 级别 | 已观察问题 | 建议动作 |",
        "|:--|:--|:--|",
    ]
    for row in data["corrections"]:
        lines.append(f"| {row['severity']} | {row['finding']} | {row['action']} |")
    lines += ["", "## 六、44 份文档覆盖清单", "", "共享批次方向不等于单篇独立首创或新理论。", "", "| 文档路径 | 来源 ID | 批次 | 共享方向 |", "|:--|:--|:--|:--|"]
    for row in data["coverage"]["rows"]:
        lines.append(f"| `{row['path']}` | `{row['source_id']}` | `{row['batch']}` | {'、'.join(f'`{item}`' for item in row['direction_ids'])} |")
    lines += ["", "## 七、19 项冻结来源", "", "| 来源 | 只读路径 | SHA-256 |", "|:--|:--|:--|"]
    for source in data["sources"]:
        lines.append(f"| `{source['id']}` | `{source['path']}` | `{source['sha256']}` |")
    lines += ["", "## 八、双边界与后续", "", "| 边界 | 状态 |", "|:--|:--|"]
    for key, value in data["open_boundaries"].items():
        lines.append(f"| `{key}` | `{str(value).lower()}` |")
    lines += [
        "",
        "本批完成的是 organized 44 份文档的覆盖审计与证据导航，不是整个仓库、科学验证、Lean 证明、文献库或生产交付的完成。命令与退出码见 `run.log`；Word 验收见 `word-qa/report.json`。",
        "",
        "**覆盖完成不等于研究闭合；所有未竟工作继续按四个方向推进。**",
        "",
    ]
    return "\n".join(lines)


def main():
    data = build_data()
    (AUDIT / "review.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    build_figure(data)
    (AUDIT / "REVIEW.md").write_text(build_markdown(data), encoding="utf-8")
    print(json.dumps({
        "sources": len(data["sources"]),
        "documents": len(data["document_assessments"]),
        "directions": len(data["directions"]),
        "corrections": len(data["corrections"]),
        "covered": data["coverage"]["covered_count"],
        "uncovered": data["coverage"]["uncovered"],
        "duplicates": data["coverage"]["duplicates"],
        "review_sha256": sha256(AUDIT / "review.json"),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
