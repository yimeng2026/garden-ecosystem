"""Build independent navigation and reference remediation assets."""

import csv
import hashlib
import json
import re
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from test_remediation import EXPECTED_HASHES

ROOT = Path(__file__).resolve().parent
AUDIT_ROOT = ROOT.parent / "paper-direction-audit-2026-11-10"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_root():
    for parent in ROOT.parents:
        candidate = parent / "toe-sylva-audit/papers/room_temp_sc"
        if candidate.is_dir():
            return candidate
    raise FileNotFoundError("room_temp_sc source root")


def source_paths():
    paper = source_root()
    return {
        "coverage_inventory": AUDIT_ROOT / "project-intro/sources/coverage-inventory.json",
        "base_bib": paper / "organized/09-参考文献/01-参考文献.bib",
        "main_claims_review": AUDIT_ROOT / "main-claims/review.json",
        "main_claims_builder": AUDIT_ROOT / "main-claims/build_report.js",
        "old_enhanced_bib": paper / "organized/09-参考文献/02-增强参考文献.bib",
    }


def display_path(source_id, path):
    if source_id in {"base_bib", "old_enhanced_bib"}:
        return f"toe-sylva-audit/papers/room_temp_sc/organized/09-参考文献/{path.name}"
    return path.relative_to(AUDIT_ROOT).as_posix()


def modern_suffix():
    return r"""
% =============================================================================
% MODERN EVIDENCE ADDITIONS (verified roles; not a blanket validation claim)
% =============================================================================

% theoretical prediction only; not experimental confirmation
@article{he2024predicted,
  title={Predicted hot superconductivity in LaSc2H24 under pressure},
  author={He and others},
  journal={Proceedings of the National Academy of Sciences},
  volume={121},
  number={26},
  pages={e2401840121},
  year={2024},
  doi={10.1073/pnas.2401840121},
  url={https://www.pnas.org/doi/10.1073/pnas.2401840121}
}

% author-reported positive preprint; not independent confirmation
@misc{song2025roomtemperature,
  title={Room-Temperature Superconductivity at 298 K in Ternary La-Sc-H System at High-pressure Conditions},
  author={Song and others},
  year={2025},
  eprint={2510.01273},
  archivePrefix={arXiv},
  note={v2, 2025-10-06; author-reported positive preprint, not independent confirmation},
  url={https://arxiv.org/abs/2510.01273}
}

% independent negative replication preprint; not a final refutation
@misc{semenok2026stability,
  title={Stability analysis of superconductivity in P6/mmm-LaSc2H24 and its experimental reproducibility from La-Sc alloys},
  author={Semenok and others},
  year={2026},
  eprint={2605.29985},
  archivePrefix={arXiv},
  note={v2, 2026-08-20; independent negative replication preprint, not a final refutation},
  url={https://arxiv.org/abs/2605.29985}
}
"""


def build_index(data):
    lines = [
        "# Sylva 室温超导项目：真实 44 份导航（修复版）",
        "",
        "> 由 `coverage.csv` 与 `remediation.json` 生成。原始文件只读；此目录不替代科学审计。",
        "",
        "## 使用边界",
        "",
        "- **40＋4＝44／44**：前十批 40 份，目录与项目介绍 4 份；无遗漏、无重复。",
        "- **PRL 版本未找到**，不列为现有成品。主论文当前只列实际存在的版本。",
        "- Lean、DFT、实验复现和独立 Meissner 仍为开放工作，不按“技术验证已完成”导航。",
        "- 参考文献使用本包 `references_repaired.bib`；27 条可解析不代表全部回源或全部可信。",
        "- 目录组：" + "、".join(data["coverage"]["groups"]) + "。",
        "",
        "## 推荐阅读顺序",
        "",
        "1. `01-封面与介绍/01-项目说明.md`：只按 0.1-alpha 草案阅读，先查看证明债务。",
        "2. `02-主论文/`：对照主论文审计，区分条件框架、预测和实验争议。",
        "3. `03-理论框架` → `04-材料预测` → `05-实验验证`：同时打开对应审计，不使用必然性成稿口吻。",
        "4. `07-形式化代码/`：先检查真实模块、编译命令和退出码，不把 admit/sorry 当完成。",
        "5. `09-参考文献/`：旧增强文件不可用；使用本包新库并保留证据角色。",
        "",
        "## 44 份文档与审计入口",
        "",
        "| 序号 | 文档路径 | 来源 ID | 批次 | 共享方向 | 审计 |",
        "|--:|:--|:--|:--|:--|:--|",
    ]
    for index, row in enumerate(data["coverage"]["rows"], 1):
        review = f"../paper-direction-audit-2026-11-10/{row['batch']}/REVIEW.md"
        lines.append(f"| {index} | `{row['path']}` | `{row['source_id']}` | `{row['batch']}` | {'、'.join(f'`{item}`' for item in row['direction_ids'])} | [打开]({review}) |")
    lines += [
        "",
        "## 未竟工作",
        "",
        "覆盖完成不等于研究闭合。请优先处理各审计中的 P0／P1 项；不得把此导航当作科学验证、Lean 证明、全部文献回源或实验复现的完成证明。",
        "",
    ]
    return "\n".join(lines)


def build_figure(data):
    plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False
    fig, (left, right) = plt.subplots(1, 2, figsize=(14, 7), facecolor="#F7F8FA", constrained_layout=True)
    fig.suptitle("导航与引用交付修复：可机检不等于科学闭合", fontsize=20, fontweight="bold", color="#263238")
    for ax in (left, right):
        ax.set_facecolor("white")
        for spine in ax.spines.values():
            spine.set_color("#CFD8DC")

    labels = ["真实文档", "CSV 行", "目录组", "审计链接"]
    values = [44, 44, 22, 44]
    bars = left.barh(range(4), values, color=["#7E57C2", "#607D8B", "#90A4AE", "#455A64"])
    for bar, value in zip(bars, values):
        left.text(value + 0.7, bar.get_y() + bar.get_height() / 2, str(value), va="center", fontsize=11, fontweight="bold")
    left.set_yticks(range(4), labels)
    left.invert_yaxis()
    left.set_xlim(0, 52)
    left.set_title("A. 40＋4＝44／44；00–21 全组", fontsize=15, fontweight="bold", color="#37474F")
    left.set_xlabel("可机检数量")
    left.grid(axis="x", alpha=0.18)
    left.text(0.03, 0.03, "uncovered=[]；duplicates=[]；PRL 不列为成品", transform=left.transAxes, fontsize=10.5, color="#455A64", bbox={"facecolor": "white", "alpha": 0.88, "edgecolor": "none", "pad": 2})

    labels = ["旧增强文件", "基础保留", "现代新增", "新库合计"]
    values = [0, 24, 3, 27]
    colors = ["#C62828", "#78909C", "#7E57C2", "#455A64"]
    bars = right.barh(range(4), values, color=colors)
    for bar, value in zip(bars, values):
        right.text(value + 0.45, bar.get_y() + bar.get_height() / 2, str(value), va="center", fontsize=11, fontweight="bold")
    right.set_yticks(range(4), labels)
    right.invert_yaxis()
    right.set_xlim(0, 32)
    right.set_title("B. 24＋3＝27 条可解析 BibTeX", fontsize=15, fontweight="bold", color="#37474F")
    right.set_xlabel("唯一条目数")
    right.grid(axis="x", alpha=0.18)
    right.text(0.03, 0.03, "仍有 5 个待补区块；可解析≠全部回源", transform=right.transAxes, fontsize=10.5, color="#8A4B4B", bbox={"facecolor": "white", "alpha": 0.88, "edgecolor": "none", "pad": 2})
    fig.savefig(ROOT / data["figure"]["svg"], format="svg")
    fig.savefig(ROOT / data["figure"]["png"], dpi=180)
    plt.close(fig)


def build_report_markdown(data):
    references = data["references"]
    lines = [
        "# 导航与参考文献修复包：交付、验证与剩余边界",
        "",
        "> 2026-11-11。独立新增文件，原始证据只读。**可解析≠全部回源，44／44 覆盖≠科学验证。**",
        "",
        "## 一、交付结果",
        "",
        "- 真实导航 **44／44**：40＋4，00–21 全组，无遗漏、无重复。",
        "- 新参考文献 **24＋3＝27** 条唯一 BibTeX；旧增强文件为 0 条，不能继续使用。",
        "- 仍有 **5 个待补区块**、6 次占位字符串；旧 24 条不因复制而自动获得可信度背书。",
        "",
        "| 文件 | 用途 | 验收重点 |",
        "|:--|:--|:--|",
        "| `INDEX.md` | 真实 44 份导航与审计入口 | 全路径、全目录组、无 PRL 成品、链接存在 |",
        "| `coverage.csv` | 44 行机器覆盖表 | 唯一路径、来源哈希、方向与评审路径 |",
        "| `references_repaired.bib` | 27 条新库 | 唯一 key、旧前缀保留、三条现代标识 |",
        "| `remediation.json` | 统一结构化结果 | 输入哈希、证据角色和双边界 |",
        "| `REMEDIATION.docx` | 原生整改报告 | 公式、表格、图件、脚注和逐页 QA |",
        "",
        "![图 1：导航与引用交付修复](remediation-evidence.svg)",
        "",
        "**图件插入顺序：图 1 位于整改资产表之后、剩余证据边界之前。**",
        "",
        "## 二、三条现代来源及角色",
        "",
        "| 来源 | 标识 | 允许角色 | 禁止升级 |",
        "|:--|:--|:--|:--|",
        "| PNAS 2024 | `10.1073/pnas.2401840121` | 理论预测 | 实验确认 |",
        "| Song 2025 v2 | `2510.01273` | 作者正向实验预印本 | 独立确认或必然性证明 |",
        "| Semenok 2026 v2 | `2605.29985` | 独立负向复现预印本 | 对 Song 或材料族的最终否证 |",
        "",
        "作者字段只使用已核实的 `He and others`、`Song and others`、`Semenok and others`，没有虚构完整作者列表。",
        "",
        "## 三、输入血缘",
        "",
        "| 输入 | SHA-256 |",
        "|:--|:--|",
    ]
    for source in data["source_inputs"]:
        lines.append(f"| `{source['id']}`：`{source['path']}` | `{source['sha256']}` |")
    lines += [
        "",
        "## 四、仍需推进的工作",
        "",
        "1. 旧 24 条逐条回源并清偿 5 个待补区块；不得只追求条目数量。",
        "2. 修正原目录前保留版本血缘；新导航可重复生成，原文件未被替换。",
        "3. Lean 需要真实模块、最小命题和编译退出码；实验需要独立正向复现和直接 Meissner。",
        "4. 参考文献可解析只表示交付可用，不表示全部可信、全部回源或科学验证完成。",
        "",
        "## 五、双边界",
        "",
        "| 边界 | 状态 |",
        "|:--|:--|",
    ]
    for key, value in data["open_boundaries"].items():
        lines.append(f"| `{key}` | `{str(value).lower()}` |")
    lines += [
        "",
        "验证命令与退出码见 `run.log`；Word 逐页结果见 `word-qa/report.json`。未修改原始证据，未新增证明、实验或独立复现。",
        "",
    ]
    return "\n".join(lines)


def main():
    paths = source_paths()
    source_inputs = []
    for source_id, expected in EXPECTED_HASHES.items():
        actual = sha256(paths[source_id])
        if actual != expected:
            raise ValueError(f"input hash changed: {source_id}: {actual} != {expected}")
        source_inputs.append({"id": source_id, "path": display_path(source_id, paths[source_id]), "sha256": actual, "read_only": True})

    inventory = json.loads(paths["coverage_inventory"].read_text(encoding="utf-8"))
    rows = inventory["coverage"]["rows"]
    if len(rows) != 44 or len({row["path"] for row in rows}) != 44:
        raise ValueError("coverage must contain 44 unique rows")
    paper = source_root()
    for row in rows:
        actual = sha256(paper / "organized" / row["path"])
        if actual != row["source_sha256"]:
            raise ValueError(f"source hash changed: {row['path']}")
        review = AUDIT_ROOT / row["batch"] / "REVIEW.md"
        if not review.exists():
            raise FileNotFoundError(f"audit report missing: {review}")

    with (ROOT / "coverage.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["path", "source_id", "batch", "direction_ids", "source_sha256", "review_path"])
        writer.writeheader()
        for row in rows:
            writer.writerow({
                "path": row["path"],
                "source_id": row["source_id"],
                "batch": row["batch"],
                "direction_ids": ";".join(row["direction_ids"]),
                "source_sha256": row["source_sha256"],
                "review_path": row["review_path"],
            })

    base_bytes = paths["base_bib"].read_bytes()
    separator = b"" if base_bytes.endswith(b"\n") else b"\n"
    new_bib = base_bytes + separator + modern_suffix().lstrip("\n").encode("utf-8")
    (ROOT / "references_repaired.bib").write_bytes(new_bib)
    bib_text = new_bib.decode("utf-8")
    entries = re.findall(r"(?m)^@(\w+)\{([^,]+),", bib_text)
    keys = [key for _, key in entries]
    if len(entries) != 27 or len(set(keys)) != 27:
        raise ValueError("BibTeX must contain 27 unique entries")

    data = {
        "schema": "organized-remediation-v1",
        "date": "2026-11-11",
        "scope": "独立导航与参考文献修复包；原始证据只读，不宣称科学验证或全部回源。",
        "source_inputs": source_inputs,
        "coverage": {
            "rows": rows,
            "actual_markdown_count": 44,
            "covered_count": 44,
            "prior_covered_count": 40,
            "current_batch_count": 4,
            "uncovered": [],
            "duplicates": [],
            "groups": [f"{number:02d}" for number in range(22)],
            "prl_delivered": False,
        },
        "navigation": {
            "index_file": "INDEX.md",
            "csv_file": "coverage.csv",
            "audit_links_verified": True,
        },
        "references": {
            "base_entries": 24,
            "new_entries": 3,
            "total_entries": len(entries),
            "unique_keys": len(set(keys)),
            "placeholder_sections": len(re.findall(r"(?m)^% \[TO_BE_COMPLETED", bib_text)),
            "placeholder_token_occurrences": bib_text.count("TO_BE_COMPLETED"),
            "old_enhanced_entries": 0,
            "old_enhanced_bytes": paths["old_enhanced_bib"].stat().st_size,
            "new_library_parseable": True,
            "reference_library_ready": False,
        },
        "modern_sources": [
            {"id": "pnas_2024", "identifier": "10.1073/pnas.2401840121", "role": "theoretical_prediction", "url": "https://www.pnas.org/doi/10.1073/pnas.2401840121"},
            {"id": "song_2025", "identifier": "2510.01273", "role": "author_positive_preprint", "url": "https://arxiv.org/abs/2510.01273"},
            {"id": "semenok_2026", "identifier": "2605.29985", "role": "independent_negative_preprint", "url": "https://arxiv.org/abs/2605.29985"},
        ],
        "open_boundaries": {
            "navigation_delivery_complete": True,
            "reference_delivery_parseable": True,
            "reference_library_ready": False,
            "scientific_validation_complete": False,
            "all_unfinished_work_completed": False,
            "lean_proof_complete": False,
            "experimental_replication_complete": False,
            "whole_repository_research_complete": False,
        },
        "figure": {
            "svg": "remediation-evidence.svg",
            "png": "remediation-evidence.png",
            "labels": ["44／44", "24＋3＝27", "5 个待补区块", "可解析≠全部回源"],
            "caption": "图 1　真实导航与新参考文献：交付改善与开放边界并存",
            "insert_after": "整改资产表",
            "insert_before": "剩余证据边界",
            "completion_percentage_plotted": False,
        },
        "verification_scope": {
            "source_documents_modified": False,
            "all_legacy_entries_reverified": False,
            "new_lean_or_experiment": False,
            "whole_repository_research_complete": False,
        },
    }
    (ROOT / "INDEX.md").write_text(build_index(data), encoding="utf-8")
    (ROOT / "remediation.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    build_figure(data)
    (ROOT / "REMEDIATION.md").write_text(build_report_markdown(data), encoding="utf-8")
    print(json.dumps({
        "coverage": data["coverage"]["covered_count"],
        "groups": len(data["coverage"]["groups"]),
        "bib_entries": len(entries),
        "unique_keys": len(set(keys)),
        "placeholder_sections": data["references"]["placeholder_sections"],
        "placeholder_tokens": data["references"]["placeholder_token_occurrences"],
        "remediation_sha256": sha256(ROOT / "remediation.json"),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
