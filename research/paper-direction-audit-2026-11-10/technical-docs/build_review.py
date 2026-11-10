"""Build the technical-delivery and validation evidence audit."""

import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

AUDIT = Path(__file__).resolve().parent
EXPECTED_HASHES = {
    "delivery_summary": "957e71d98c74e813bed8780614552b20b0802f0ec6c4c598e2f3a39d2c49cdfc",
    "final_report": "563b2fae7222a9ac9ccec3fac849b467e9ae46d571e99def0ef423a9f878e667",
    "progress_report": "a4ffcdc575a2d9f0ae21108b5679856ed022c827bdd549020dc1f3be59d524bb",
    "quality_progress": "0da15ed8122b1908bb8ce155956aebd55166330ca094982f81c6637624354d64",
    "integration_checklist": "1510c3bc360560a1b131c9352616cd28717691abee41ff3951231a65d26d2909",
    "main_claims_review": "e9ac6ff0bc88f11b1c2c91ae61ce398a05fc077815803f48669b46536d6f2f45",
    "validation_review": "17eaa27d30df6849f752e3712d563ebe492ae394ea9c74b1b072ac0755acb491",
    "methods_review": "f30d15d8665644d11957166efaea95d59f7a742037dc697b737704cd15dc9e21",
    "handbook_review": "0394b996c271a6ca24b4692d7bd078b4c0fa8925eefde6df0347a478f298ac48",
}


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_root():
    for parent in AUDIT.parents:
        candidate = parent / "toe-sylva-audit/papers/room_temp_sc/organized"
        if candidate.is_dir():
            return candidate
    raise FileNotFoundError("room_temp_sc organized root")


def load_review(name):
    return json.loads((AUDIT.parent / name / "review.json").read_text(encoding="utf-8"))


def build_data():
    root = source_root()
    inventory_path = AUDIT / "sources/artifact-inventory.json"
    inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
    paths = {
        "delivery_summary": root / "10-技术文档/01-交付摘要.md",
        "final_report": root / "10-技术文档/02-最终报告.md",
        "progress_report": root / "10-技术文档/03-进度报告.md",
        "quality_progress": root / "10-技术文档/04-质量进展.md",
        "integration_checklist": root / "10-技术文档/05-整合检查清单.md",
        "artifact_inventory": inventory_path,
        "main_claims_review": AUDIT.parent / "main-claims/review.json",
        "validation_review": AUDIT.parent / "validation-materials/review.json",
        "methods_review": AUDIT.parent / "room-temp-methods/review.json",
        "handbook_review": AUDIT.parent / "handbook-chapters/review.json",
    }
    display = {
        "delivery_summary": "toe-sylva-audit/papers/room_temp_sc/organized/10-技术文档/01-交付摘要.md",
        "final_report": "toe-sylva-audit/papers/room_temp_sc/organized/10-技术文档/02-最终报告.md",
        "progress_report": "toe-sylva-audit/papers/room_temp_sc/organized/10-技术文档/03-进度报告.md",
        "quality_progress": "toe-sylva-audit/papers/room_temp_sc/organized/10-技术文档/04-质量进展.md",
        "integration_checklist": "toe-sylva-audit/papers/room_temp_sc/organized/10-技术文档/05-整合检查清单.md",
        "artifact_inventory": "sources/artifact-inventory.json",
        "main_claims_review": "main-claims/review.json",
        "validation_review": "validation-materials/review.json",
        "methods_review": "room-temp-methods/review.json",
        "handbook_review": "handbook-chapters/review.json",
    }
    sources = []
    for source_id, path in paths.items():
        actual = sha256(path)
        expected = EXPECTED_HASHES.get(source_id, sha256(inventory_path) if source_id == "artifact_inventory" else None)
        if actual != expected:
            raise ValueError(f"source hash changed: {source_id}: {actual} != {expected}")
        sources.append({"id": source_id, "path": display[source_id], "sha256": actual, "read_only": True})
    validation = load_review("validation-materials")
    methods = load_review("room-temp-methods")
    main = load_review("main-claims")
    return {
        "schema": "technical-docs-audit-v1",
        "date": "2026-11-10",
        "scope": "五份技术文档及当前资产；只审计，不修改原文，不重跑计算或实验。",
        "sources": sources,
        "source_lineage": {
            "research_program_count": 1,
            "decision": "五份文档属于同一研究纲领的进度、质量与交付叙事，不是五个独立新理论。",
        },
        "directions": [
            {
                "id": "artifact_existence",
                "role": "压缩包、哈希、图件、引用库、版本和实际路径的可验证资产清单",
                "closed": "压缩包、图、引用库缺失与四个 LaTeX、替代 Lean／SI 的存在状态已固定。",
                "unfinished": "最终压缩包、全部图件、完整引用库、全格式版本和 MD5 验证未闭合。",
                "next": "以实际路径和哈希生成资产清单，交付前逐项验收，不接受口头完成。",
            },
            {
                "id": "status_evidence",
                "role": "最终 100%、运行中、模板和占位状态的时间线与一致性治理",
                "closed": "最终 100% 与 A／D 运行中、质量深化中和模板清单的矛盾已定位。",
                "unfinished": "历史状态、当前状态和交付状态没有统一证据源。",
                "next": "以任务状态机和实际验收记录替代静态完成叙事，保留时间戳。",
            },
            {
                "id": "scientific_validation",
                "role": "公式、评分、Lean、SI、实验角色和证据等级验证",
                "closed": "H₃S 复算、评分缺口、Lean 未编译、SI 模板和实验角色已核清。",
                "unfinished": "公式链、评分卡、Lean 构建、DFT 输入、声子谱和独立实验未闭合。",
                "next": "先完成最小科学垂直切片，再恢复验证通过与可发表措辞。",
            },
            {
                "id": "delivery_governance",
                "role": "把整合清单转化为带资产、命令、退出码和责任边界的验收任务",
                "closed": "TEMPLATE／PARTIAL／PLACEHOLDERS 与实际交付缺口已对应。",
                "unfinished": "最终资产、全部质量检查、作者信息和投稿前审查未完成。",
                "next": "按资产、脚本、验证、复核四列验收，失败项保持未完成。",
            },
        ],
        "evidence": {
            "status": {
                "final_100_claimed": True,
                "a_and_d_running": True,
                "quality_deepening_ongoing": True,
                "checklist_template": True,
                "contradiction": True,
            },
            "assets": inventory,
            "science": {
                "h3s_computed_tc_k": validation["evidence"]["formula_spotcheck"]["h3s"]["computed_tc_k"],
                "h3s_claimed_tc_k": validation["evidence"]["formula_spotcheck"]["h3s"]["claimed_tc_k"],
                "scoring_rubric_available": validation["evidence"]["scoring"]["rubric_available"],
                "lean_build_passed": methods["evidence"]["lean"]["build_passed"],
                "direct_meissner_completed": main["evidence"]["song"]["direct_meissner_completed"],
                "independent_positive_replication": main["evidence"]["song"]["independent_positive_replication"],
                "pnas_is_prediction": main["evidence"]["pnas_prediction"]["role"] == "2024 理论预测",
            },
            "metadata": {
                "delivery_date": "2025-04-19",
                "cited_breakthrough_month": "2025-10",
                "date_precedes_cited_breakthrough": True,
            },
        },
        "corrections": [
            {"id": "status_contradiction", "severity": "P0", "finding": "最终 100% 与 A／D 运行中、质量深化中和模板清单并存。", "action": "改为状态矛盾未解决，按实际验收记录更新，不宣称完成。"},
            {"id": "tar_md5", "severity": "P0", "finding": "声称的 63KB 压缩包当前未找到，MD5 不可验证。", "action": "标为资产未验证；重新生成后记录路径、大小和实际哈希，不沿用旧 MD5。"},
            {"id": "figures_references", "severity": "P0", "finding": "99 条引用库和六张图当前未找到。", "action": "标为缺失资产，补齐前不写引用和可视化已完成。"},
            {"id": "versions", "severity": "P1", "finding": "PRL 和所称 Markdown 对应文件未找到，多版本只部分存在。", "action": "保留四个已存在 LaTeX 文件，其余版本列为未竟，不写全格式完成。"},
            {"id": "metadata_time", "severity": "P1", "finding": "交付日期 2025-04-19 早于所引 2025-10 突破。", "action": "核对版本血缘和实际生成时间，只标元数据矛盾，不判造假。"},
            {"id": "formula_scoring", "severity": "P0", "finding": "H₃S 公式复算约 161.081844 K 且评分无规则，B／C 路仍写完成。", "action": "科学验证保持未闭合，先修公式链和公开评分卡，再讨论完成度。"},
            {"id": "lean_si", "severity": "P0", "finding": "Lean 未编译且 SI 有 31 处占位，仍写不会报错和验证完成。", "action": "保持草案与模板状态，清偿证明债务并补齐 DFT 输入、声子谱和日志。"},
            {"id": "experimental_roles", "severity": "P0", "finding": "Song 与 PNAS 被写成完美实验验证，直接 Meissner 和独立复现未确立。", "action": "分开作者预印本、理论预测和独立复现，不写完美验证或可发表保证。"},
        ],
        "open_boundaries": {
            "tar_verified": False,
            "figures_verified": False,
            "references99_verified": False,
            "scientific_validation": False,
            "delivery_ready": False,
            "full_repository_audit": False,
        },
        "figure": {
            "svg": "technical-status-evidence.svg",
            "png": "technical-status-evidence.png",
            "labels": ["完成状态 100%", "TEMPLATE", "room_temp_sc_paper_FINAL_v2.tar.gz", "references_enhanced.bib", "manuscript_prl.tex"],
            "caption": "图 1　交付状态与实际资产不能互相替代",
            "insert_after": "资产清单表",
            "insert_before": "结果解释",
            "completion_percentage_plotted": False,
        },
        "verification_scope": {
            "source_documents_modified": False,
            "new_dft_lean_or_experiment": False,
            "tar_or_figures_rebuilt": False,
            "full_repository_audit": False,
        },
    }


def box(axis, y, text, face, edge="#455A64", height=0.15, size=11):
    patch = FancyBboxPatch((0.08, y), 0.84, height, boxstyle="round,pad=0.012,rounding_size=0.018",
                           transform=axis.transAxes, facecolor=face, edgecolor=edge, linewidth=1.3)
    axis.add_patch(patch)
    axis.text(0.50, y + height / 2, text, transform=axis.transAxes, ha="center", va="center",
              fontsize=size, color="#263238", linespacing=1.4)


def build_figure(data):
    plt.rcParams["font.family"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
    fig, axes = plt.subplots(1, 2, figsize=(12.8, 7.2), gridspec_kw={"wspace": 0.12})
    fig.patch.set_facecolor("#FAFBFC")
    for axis in axes:
        axis.set_axis_off()
        axis.set_xlim(0, 1)
        axis.set_ylim(0, 1)
    axes[0].set_title("状态叙事：100% 与运行中并存", fontsize=16, fontweight="bold", color="#263238", pad=18)
    box(axes[0], 0.74, "最终报告：完成状态 100%", "#F5E8E4", edge="#A65D4E")
    box(axes[0], 0.53, "A／D 两路：运行中\n质量深化：进行中", "#F3EEE4")
    box(axes[0], 0.31, "整合清单：TEMPLATE／PARTIAL／PLACEHOLDERS", "#F3EEE4")
    axes[0].text(0.50, 0.13, "结论：状态矛盾未解决，不能宣称最终交付。", transform=axes[0].transAxes,
                 ha="center", fontsize=11, color="#8C4A3E")

    axes[1].set_title("实际资产：缺失与部分存在", fontsize=16, fontweight="bold", color="#263238", pad=18)
    box(axes[1], 0.74, "未找到：压缩包／MD5 可验证性\nreferences_enhanced.bib／六张图", "#F5E8E4", edge="#A65D4E")
    box(axes[1], 0.50, "未找到：manuscript_prl.tex\n所称 Markdown 对应文件", "#F3EEE4")
    box(axes[1], 0.25, "已存在：四个 LaTeX 文件\n替代 Lean 与 SI 文件（但未编译／模板）", "#E4EFE9")
    axes[1].text(0.50, 0.10, "部分存在不能写成全格式完成；SI 有 31 处占位。", transform=axes[1].transAxes,
                 ha="center", fontsize=11, color="#546E7A")
    fig.suptitle("交付状态与实际资产不能互相替代", fontsize=20, fontweight="bold", color="#263238", y=0.985)
    fig.text(0.5, 0.012, "只显示当前资产和状态，不绘制完成百分比。", ha="center", fontsize=10, color="#607D8B")
    fig.subplots_adjust(left=0.035, right=0.98, top=0.87, bottom=0.08)
    fig.savefig(AUDIT / data["figure"]["svg"], metadata={"Date": None})
    fig.savefig(AUDIT / data["figure"]["png"], dpi=220, metadata={"Software": None})
    plt.close(fig)


def build_markdown(data):
    assets = data["evidence"]["assets"]
    science = data["evidence"]["science"]
    metadata = data["evidence"]["metadata"]
    lines = [
        "# 技术文档交付与验证：资产、状态和未竟工作审计",
        "",
        "> 日期：2026-11-10。只审计，不修改原文，不重跑计算或实验。",
        "",
        "## 一、血缘裁决与四个发展方向",
        "",
        data["source_lineage"]["decision"],
        "",
        "| 来源 ID | 只读路径 | SHA-256 |",
        "|:--|:--|:--|",
    ]
    for source in data["sources"]:
        lines.append(f"| `{source['id']}` | `{source['path']}` | `{source['sha256']}` |")
    lines += ["", "| 方向 | 已闭合的局部审计 | 未竟工作与下一步 |", "|:--|:--|:--|"]
    for row in data["directions"]:
        lines.append(f"| `{row['id']}`：{row['role']} | {row['closed']} | {row['unfinished']}**下一步：**{row['next']} |")
    lines += [
        "",
        "## 二、状态矛盾与实际资产",
        "",
        "最终报告写 **完成状态 100%**，但 A／D 两路仍运行中、质量深化仍进行中、整合清单仍为 `TEMPLATE／PARTIAL／PLACEHOLDERS`。这些状态不能直接合并为最终交付。",
        "",
        "| 资产 | 当前结果 | 验收裁决 |",
        "|:--|:--|:--|",
        "| `room_temp_sc_paper_FINAL_v2.tar.gz` | 未找到；63KB 和 MD5 不可验证 | 资产未验证，重新生成后计算新哈希 |",
        "| 六张图 | 未找到 | 不写可视化已完成 |",
        "| `references_enhanced.bib` | 未找到 | 不写 99 条引用已齐备 |",
        "| `manuscript_prl.tex` 与所称 Markdown 对应文件 | 未找到 | 多版本只部分存在，不写全格式完成 |",
        "| 四个 LaTeX 文件 | 已存在 | 保留，但不自动等于科学验证 |",
        "| 替代 Lean 与 SI 文件 | 已存在 | Lean 未编译；SI 有 31 处占位，仍是草案／模板 |",
        "",
        "![图 1：交付状态与实际资产不能互相替代](technical-status-evidence.svg)",
        "",
        "**图件插入顺序：图 1 位于资产清单表之后、结果解释之前。** 图中不把 100% 当成可验证完成度。",
        "",
        "## 三、科学验证仍不闭合",
        "",
        "| 项目 | 实际结果 | 不能升级为 |",
        "|:--|:--|:--|",
        f"| H₃S 公式 | 复算约 {science['h3s_computed_tc_k']:.6f} K，文中为 {science['h3s_claimed_tc_k']:.0f} K | 不能写公式链或材料预测已验证 |",
        "| 验证评分 | 没有公开可复算规则 | 不能把百分比当科学验证结果 |",
        "| Lean | 未编译且存在证明债务 | 不能写机器证明完成或不会报错 |",
        "| SI | 31 处占位；DFT 输入、声子谱、收敛日志未提供 | 不能写计算验证完成 |",
        "| Song／PNAS | 直接 Meissner 和独立复现未确立；PNAS 是理论预测 | 不能写完美实验验证或投稿保证 |",
        "",
        f"交付日期 {metadata['delivery_date']} 早于所引 {metadata['cited_breakthrough_month']} 突破，构成元数据时间矛盾，需核对版本血缘而不判造假。",
        "",
        "## 四、分档勘误与验收任务",
        "",
        "| 级别 | 已观察问题 | 建议动作 |",
        "|:--|:--|:--|",
    ]
    for row in data["corrections"]:
        lines.append(f"| {row['severity']} | {row['finding']} | {row['action']} |")
    lines += [
        "",
        "后续验收采用四列：资产路径与哈希、执行命令、退出码、复核边界。任何失败项保持未完成，直到真实资产和科学证据同时闭合。",
        "",
        "## 五、验证范围与开放边界",
        "",
        "| 边界 | 状态 |",
        "|:--|:--|",
    ]
    for key, value in data["open_boundaries"].items():
        lines.append(f"| `{key}` | `{str(value).lower()}` |")
    lines += [
        "",
        "本批使用十项冻结来源、实际资产清单和独立复核。命令与退出码见 `run.log`；Word 渲染状态见 `word-qa/report.json`。",
        "",
        "本批没有重跑计算或实验，没有重建压缩包或图件，没有修改五份原文。**全库审计尚未完成。**",
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
        "directions": len(data["directions"]),
        "corrections": len(data["corrections"]),
        "tar_exists": data["evidence"]["assets"]["tar_exists"],
        "figures_found": data["evidence"]["assets"]["figures_found"],
        "tex_variants_present": data["evidence"]["assets"]["tex_variants_present"],
        "h3s_computed": data["evidence"]["science"]["h3s_computed_tc_k"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
