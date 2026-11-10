"""Build a unified, read-only evidence audit for theory and breakthrough documents."""

import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

from numeric_and_text_checks import find_source_root, scan_breakthrough, scan_theory

AUDIT = Path(__file__).resolve().parent
EXPECTED_HASHES = {
    "theory_framework": "c53b9b8fbab8018e3e2948e8ecff71d0232dd47e60c8a86f4281e58200c262fb",
    "breakthrough_report": "7d9711df200880690a82c814380e4392f35a1ca3c6df957cabe6607678ba00ce",
    "main_claims_review": "e9ac6ff0bc88f11b1c2c91ae61ce398a05fc077815803f48669b46536d6f2f45",
    "methods_review": "f30d15d8665644d11957166efaea95d59f7a742037dc697b737704cd15dc9e21",
}


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def find_prior(name):
    relative = f"research/paper-direction-audit-2026-11-10/{name}/review.json"
    for parent in AUDIT.parents:
        candidate = parent / relative
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(relative)


def build_data():
    source_root = find_source_root()
    paths = {
        "theory_framework": source_root / "organized/03-理论框架/01-理论框架.md",
        "breakthrough_report": source_root / "organized/06-突破详解/01-2025年10月突破.md",
        "main_claims_review": find_prior("main-claims"),
        "methods_review": find_prior("room-temp-methods"),
    }
    display = {
        "theory_framework": "toe-sylva-audit/papers/room_temp_sc/organized/03-理论框架/01-理论框架.md",
        "breakthrough_report": "toe-sylva-audit/papers/room_temp_sc/organized/06-突破详解/01-2025年10月突破.md",
        "main_claims_review": "research/paper-direction-audit-2026-11-10/main-claims/review.json",
        "methods_review": "research/paper-direction-audit-2026-11-10/room-temp-methods/review.json",
    }
    sources = []
    for source_id, path in paths.items():
        actual = sha256(path)
        if actual != EXPECTED_HASHES[source_id]:
            raise ValueError(f"source hash changed: {source_id}: {actual}")
        sources.append({"id": source_id, "path": display[source_id], "sha256": actual, "read_only": True})

    prior = json.loads(paths["main_claims_review"].read_text(encoding="utf-8"))
    methods = json.loads(paths["methods_review"].read_text(encoding="utf-8"))
    theory = scan_theory()
    breakthrough = scan_breakthrough()
    if theory["admit_count"] != 17 or theory["sorry_count"] != 5:
        raise ValueError(f"unexpected proof debt counts: {theory['admit_count']}/{theory['sorry_count']}")
    if theory["repository_module_match_count"] != 0:
        raise ValueError("module resolution changed; inspect matches before generating audit")

    song_prior = prior["evidence"]["song"]
    semenok_prior = prior["evidence"]["semenok"]
    pnas_prior = prior["evidence"]["pnas_prediction"]
    anchor = prior["evidence"]["critical_manifold"]["temperature_anchors"][0]
    if max(song_prior["onset_tc_k"]) >= 300:
        raise ValueError("Song onset boundary changed")

    data = {
        "schema": "theory-breakthrough-audit-v1",
        "date": "2026-11-10",
        "scope": "理论框架与突破详解两份文档；只审计，不修改原文，不新增形式证明、材料预测或实验验证。",
        "sources": sources,
        "source_lineage": {
            "research_program_count": 1,
            "decision": "两份文档属于同一研究纲领的理论陈述与实验叙事，不是两个独立新理论。",
        },
        "directions": [
            {
                "id": "conditional_proof",
                "role": "把普遍必然性收缩为明确假设下的条件化命题与证明工程",
                "closed": "17 处 admit、5 处 sorry 和单点到全称的逻辑断点已定位。",
                "unfinished": "命题类型、模块实现、假设充分性、全部证明体和真实构建未闭合。",
                "next": "先固定最小可证命题与定义，再逐引理清偿并执行公理审计。",
            },
            {
                "id": "assumption_falsifiability",
                "role": "把 H1–H6、适用域和竞争相转为可操作的可证伪检验",
                "closed": "H1–H5 不自动给出 Tc>300 K，单点存在和连续性不足以支持全称命题。",
                "unfinished": "阈值一致性、模型适用域、竞争相排除和材料级测量接口仍缺失。",
                "next": "为每个假设绑定可观测量、反例条件和失败后的理论降级规则。",
            },
            {
                "id": "experimental_controversy",
                "role": "并列正向与负向预印本，推进前驱体、跨实验室和直接磁测量",
                "closed": "Song、Semenok 与 PNAS 的证据角色已分开，298 K 与预测 316/331 K 不再混写。",
                "unfinished": "独立正向复现、直接 Meissner、同行评议、前驱体有序化和总尝试分母。",
                "next": "保存双方原始数据，优先做可重复合成与直接磁测量的对照实验。",
            },
            {
                "id": "provenance_governance",
                "role": "修复时间、预测／实验、作者运行／独立复现和证据等级口径",
                "closed": "298/316 角色混合、P6/mmm 推准二维、13 次独立实验和日期矛盾已定位。",
                "unfinished": "原文修订、版本血缘、引用同步和跨文档一致性尚未完成。",
                "next": "建立带来源定位的证据卡，修订留痕并同步所有派生版本。",
            },
        ],
        "evidence": {
            "theory": {
                "admit_count": theory["admit_count"],
                "sorry_count": theory["sorry_count"],
                "proof_debt_total": theory["proof_debt_total"],
                "module_references": theory["module_references"],
                "repository_module_match_count": theory["repository_module_match_count"],
                "repository_core_theorem_match_count": sum(bool(paths) for paths in theory["core_theorem_matches"].values()),
                "lean_file_count_searched": theory["lean_file_count_searched"],
                "module_search_scope": theory["search_scope"],
                "lean_compilation_attempted": False,
                "formal_proof_completed": False,
                "document_status": "0.1-alpha pseudocode draft",
            },
            "logic": {
                "existence_to_universal_valid": False,
                "continuity_bridges_universal": False,
                "simplified_formula_anchor": {
                    "lambda": anchor["lambda"],
                    "mu_star": anchor["mu_star"],
                    "omega_log_meV": anchor["omega_log_meV"],
                    "tc_k": anchor["tc_K"],
                },
                "full_eliashberg_refuted": False,
                "specific_material_refuted": False,
                "strict_bound_necessity_proven": methods["evidence"]["eliashberg"]["room_temp_necessity_proven"],
            },
            "experiment": {
                "song": {
                    "arxiv": song_prior["arxiv"],
                    "version": song_prior["version"],
                    "url": song_prior["url"],
                    "onset_tc_k": song_prior["onset_tc_k"],
                    "pressure_gpa": song_prior["pressure_gpa"],
                    "reproducible_runs_reported": song_prior["reproducible_runs_reported"],
                    "preprint": True,
                    "peer_review_established": song_prior["peer_review_established"],
                    "independent_positive_replication": song_prior["independent_positive_replication"],
                    "direct_meissner_completed": song_prior["direct_meissner_completed"],
                    "author_runs_equal_independent_labs": False,
                },
                "semenok": {
                    "arxiv": semenok_prior["arxiv"],
                    "version": semenok_prior["version"],
                    "url": semenok_prior["url"],
                    "unsuccessful_attempts": semenok_prior["unsuccessful_attempts"],
                    "synthesis_pressure_gpa": semenok_prior["synthesis_pressure_gpa"],
                    "no_superconductivity_range_k": semenok_prior["no_superconductivity_range_k"],
                    "final_refutation_of_material_family": False,
                },
                "pnas": {
                    "citation": pnas_prior["citation"],
                    "url": pnas_prior["url"],
                    "predicted_tc_k": [row["maximum_tc_k"] for row in pnas_prior["predictions"]],
                    "pressure_gpa": [row["pressure_gpa"] for row in pnas_prior["predictions"]],
                    "theoretical_prediction": True,
                },
            },
            "breakthrough": {
                "tc_298_316_mixed_roles": breakthrough["contains_298_316_range"],
                "p6mmm_implies_quasi_2d": False,
                "mechanism_verified_by_structure_and_tc": False,
                "metadata_date_precedes_cited_preprint": breakthrough["metadata_date_precedes_cited_preprint"],
                "document_date": breakthrough["document_date"],
                "cited_preprint_month": breakthrough["cited_preprint_month"],
                "contains_13_independent_experiments": breakthrough["contains_13_independent_experiments"],
                "contains_perfect_theorem_verification": breakthrough["contains_perfect_theorem_verification"],
            },
        },
        "corrections": [
            {
                "id": "proof_debt",
                "severity": "P0",
                "finding": "构造性存在证明措辞与 17 处 admit、5 处 sorry 并存。",
                "action": "保持草案和条件化命题身份；不得以占位可解析宣称机器证明完成。",
            },
            {
                "id": "existence_universal_gap",
                "severity": "P0",
                "finding": "单点 Tc>300 K 存在性被用于所有满足假设材料的普遍必然性。",
                "action": "补齐从存在点到全称命题的充分条件与证明；连续性本身不构成该桥梁。",
            },
            {
                "id": "experimental_overclaim",
                "severity": "P0",
                "finding": "298 K 实验 onset 与 316 K 理论预测被拼成 298–316 K，并用于完美验证必然性。",
                "action": "分开实验与预测；298 K 低于 300 K，且单个材料不能证明全称数学命题。",
            },
            {
                "id": "independent_runs",
                "severity": "P1",
                "finding": "13 次作者报告运行被写成 13 次独立实验。",
                "action": "改为 13 次可重复运行；独立实验室与总尝试分母仍待提供。",
            },
            {
                "id": "structure_mechanism",
                "severity": "P1",
                "finding": "P6/mmm 被直接等同准二维，结构与 Tc 一致被用于验证微观机制。",
                "action": "分别提供层状各向异性、谱函数、同位素和配对机制证据，不由空间群自动推出。",
            },
            {
                "id": "metadata_time",
                "severity": "P1",
                "finding": "文档生成日期 2025-04-19 早于所引 2025-10 预印本。",
                "action": "核对版本血缘和实际生成时间；只标元数据矛盾，不判造假。",
            },
        ],
        "open_boundaries": {
            "formal_proof_completed": False,
            "lean_modules_resolved": False,
            "necessity_experimentally_proven": False,
            "independent_positive_replication": False,
            "direct_meissner_completed": False,
            "full_repository_audit": False,
        },
        "figure": {
            "svg": "logic-evidence-map.svg",
            "png": "logic-evidence-map.png",
            "labels": ["单点存在", "普遍必然", "PNAS 预测", "Song 预印本", "Semenok 负向复现"],
            "caption": "图 1　理论链与实验链均不能越级",
            "insert_after": "证据角色表",
            "insert_before": "结果解释",
            "success_percentage_plotted": False,
        },
        "verification_scope": {
            "source_documents_modified": False,
            "lean_compilation_run": False,
            "new_dft_or_eliashberg_calculation": False,
            "new_experiment_or_independent_replication": False,
            "full_repository_audit": False,
        },
    }
    return data


def box(axis, x, y, width, height, text, face, edge="#455A64", size=11):
    patch = FancyBboxPatch(
        (x, y), width, height,
        boxstyle="round,pad=0.012,rounding_size=0.018",
        linewidth=1.3, edgecolor=edge, facecolor=face,
        transform=axis.transAxes,
    )
    axis.add_patch(patch)
    axis.text(x + width / 2, y + height / 2, text, transform=axis.transAxes,
              ha="center", va="center", fontsize=size, color="#263238", linespacing=1.45)


def arrow(axis, start, end, color="#607D8B", style="-"):
    axis.annotate("", xy=end, xytext=start, xycoords="axes fraction", textcoords="axes fraction",
                  arrowprops={"arrowstyle": "->", "color": color, "lw": 1.8, "linestyle": style})


def build_figure(data):
    plt.rcParams["font.family"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False
    fig, axes = plt.subplots(1, 2, figsize=(12.8, 7.2), gridspec_kw={"wspace": 0.12})
    fig.patch.set_facecolor("#FAFBFC")
    for axis in axes:
        axis.set_axis_off()
        axis.set_xlim(0, 1)
        axis.set_ylim(0, 1)
    axes[0].set_title("理论链：单点存在 ≠ 普遍必然", fontsize=16, fontweight="bold", color="#263238", pad=18)
    box(axes[0], 0.17, 0.76, 0.66, 0.13, "假设与配对映射\nH1–H6 仍需材料级验证", "#E8F0F2")
    box(axes[0], 0.17, 0.48, 0.66, 0.13, "单点存在\n∃p：Tc(p) > 300 K", "#E4EFE9")
    box(axes[0], 0.17, 0.15, 0.66, 0.15, "普遍必然\n∀m∈D：Tc(m) > 300 K", "#F5E8E4", edge="#A65D4E")
    arrow(axes[0], (0.50, 0.76), (0.50, 0.62))
    arrow(axes[0], (0.50, 0.48), (0.50, 0.31), color="#A65D4E", style="--")
    axes[0].text(0.54, 0.395, "断点：缺整段全称证明\n连续性本身不能补桥", transform=axes[0].transAxes,
                 ha="left", va="center", fontsize=11, color="#8C4A3E")
    axes[0].text(0.50, 0.045, "17 处 admit＋5 处 sorry；五个模块本次未解析", transform=axes[0].transAxes,
                 ha="center", va="center", fontsize=10.5, color="#546E7A")

    axes[1].set_title("实验链：预测与正负预印本分轨", fontsize=16, fontweight="bold", color="#263238", pad=18)
    box(axes[1], 0.10, 0.76, 0.80, 0.13, "PNAS 预测\n316 K@167 GPa；331 K@250 GPa", "#E8F0F2")
    box(axes[1], 0.10, 0.53, 0.80, 0.14, "Song 预印本\nonset 271–298 K；13 次作者报告运行", "#E4EFE9")
    box(axes[1], 0.10, 0.30, 0.80, 0.14, "Semenok 负向复现\n7 次未成功；不是整个材料族的最终否证", "#F3EEE4")
    axes[1].text(0.50, 0.14, "仍缺：独立正向复现＋直接 Meissner\n298 K < 300 K；不能拼成 298–316 K 实验", transform=axes[1].transAxes,
                 ha="center", va="center", fontsize=11, color="#8C4A3E", linespacing=1.5,
                 bbox={"boxstyle": "round,pad=0.55", "facecolor": "#F5E8E4", "edgecolor": "#A65D4E"})
    fig.suptitle("理论链与实验链均不能越级", fontsize=20, fontweight="bold", color="#263238", y=0.985)
    fig.text(0.5, 0.012, "只显示证据角色，不构造成功率、证明完成度或真伪投票。", ha="center", fontsize=10, color="#607D8B")
    fig.subplots_adjust(left=0.035, right=0.98, top=0.87, bottom=0.08)
    fig.savefig(AUDIT / data["figure"]["svg"], metadata={"Date": None})
    fig.savefig(AUDIT / data["figure"]["png"], dpi=220, metadata={"Software": None})
    plt.close(fig)


def build_markdown(data):
    theory = data["evidence"]["theory"]
    logic = data["evidence"]["logic"]
    experiment = data["evidence"]["experiment"]
    breakthrough = data["evidence"]["breakthrough"]
    lines = [
        "# 理论框架与突破详解：证明链、实验角色与未竟工作审计",
        "",
        "> 日期：2026-11-10。只审计，不修改原文，不新增形式证明、材料预测或实验验证。",
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
    lines += [
        "",
        "| 方向 | 已闭合的局部审计 | 未竟工作与下一步 |",
        "|:--|:--|:--|",
    ]
    for row in data["directions"]:
        lines.append(f"| `{row['id']}`：{row['role']} | {row['closed']} | {row['unfinished']}**下一步：**{row['next']} |")
    lines += [
        "",
        "## 二、理论证明链：17 处 admit、5 处 sorry",
        "",
        f"理论文档有 **17 处 admit、5 处 sorry**，合计 {theory['proof_debt_total']} 处显式证明债务。五个 `Superconductivity.*` 模块引用及三个核心定理名在本次 `toe-sylva-audit/**/*.lean` 检索中未解析；扫描 {theory['lean_file_count_searched']} 个 Lean 文件。未解析不等于其他位置绝对不存在实现，本批也未运行 Lean 编译。",
        "",
        "| 项目 | 审计结果 | 不能升级为 |",
        "|:--|:--|:--|",
        f"| 显式证明债务 | {theory['admit_count']} 处 admit；{theory['sorry_count']} 处 sorry | 构造性证明已完成 |",
        f"| 模块解析 | 五个引用；本次仓库命中 {theory['repository_module_match_count']} | 已有可构建实现或其他位置不存在 |",
        "| 单点存在到普遍必然 | 不是有效逻辑推论 | 连续性自动把所有材料变为室温超导 |",
        f"| 简化公式锚点 | λ={logic['simplified_formula_anchor']['lambda']}、μ*={logic['simplified_formula_anchor']['mu_star']}、ωlog={logic['simplified_formula_anchor']['omega_log_meV']} meV 时 Tc≈{logic['simplified_formula_anchor']['tc_k']:.6f} K | 否定完整 Eliashberg 或特定材料 |",
        "",
        "形式化断点可写为：",
        "",
        "$$(\\exists p: T_c(p)>300\\,K) \\nRightarrow (\\forall m\\in D: T_c(m)>300\\,K).$$",
        "",
        "需要发展的不是更强的标题，而是最小可证命题、模块实现、充分条件和逐引理清偿。H1–H6 应绑定可观测量、反例条件和失败后的降级规则。",
        "",
        "## 三、突破详解：实验与预测必须分轨",
        "",
        "| 来源 | 数值与角色 | 尚未确立 |",
        "|:--|:--|:--|",
        f"| PNAS 2024 | 167 GPa→{experiment['pnas']['predicted_tc_k'][0]} K；250 GPa→{experiment['pnas']['predicted_tc_k'][1]} K；理论预测 | 不能作为后续实验值 |",
        f"| Song 2025 预印本 | onset {experiment['song']['onset_tc_k'][0]}–{experiment['song']['onset_tc_k'][1]} K；{experiment['song']['reproducible_runs_reported']} 次作者报告可重复运行 | 独立正向复现、直接 Meissner、同行评议、总尝试分母 |",
        f"| Semenok 2026 预印本 | {experiment['semenok']['unsuccessful_attempts']} 次未成功；独立负向复现 | 不是对 Song 或整个材料族的最终逻辑否证 |",
        "",
        "![图 1：理论链与实验链均不能越级](logic-evidence-map.svg)",
        "",
        "**图件插入顺序：图 1 位于证据角色表之后、结果解释之前。** 图中没有成功率或证明完成百分比。",
        "",
        "**298 K 低于 300 K。** 不能把 Song 的 298 K 与 PNAS 的 316 K 拼成 298–316 K 实验结果，更不能由单个材料报告证明所有满足抽象假设的材料必然室温超导。",
        "",
        "13 次作者报告的可重复运行不等于 13 个独立实验室；`P6/mmm` 不自动证明准二维，结构与 Tc 一致也不单独验证微观配对机制。",
        "",
        f"突破文档日期为 {breakthrough['document_date']}，却引用 {breakthrough['cited_preprint_month']} 预印本，构成元数据时间矛盾。下一步应核查版本血缘，不直接判定造假。",
        "",
        "## 四、分档勘误与发展任务",
        "",
        "| 级别 | 已观察问题 | 建议动作 |",
        "|:--|:--|:--|",
    ]
    for row in data["corrections"]:
        lines.append(f"| {row['severity']} | {row['finding']} | {row['action']} |")
    lines += [
        "",
        "四个方向都值得继续，但它们是同一研究纲领的方法任务，不是四个已经成立的新理论。优先级应是：先收缩命题并建立最小证明核，再做假设—测量接口与争议实验对照，最后同步全部派生文档。",
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
        "本批使用冻结哈希、原文独立文本扫描、既有原始来源审计和独立数值复算。命令与退出码见 `run.log`；Word 逐页结果见 `word-qa/report.json`。",
        "",
        "本批没有运行 Lean、没有新做 DFT/Eliashberg、没有新做实验或独立复现、没有修改两份原文。**全库审计尚未完成。**",
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
        "research_program_count": data["source_lineage"]["research_program_count"],
        "directions": len(data["directions"]),
        "corrections": len(data["corrections"]),
        "admit": data["evidence"]["theory"]["admit_count"],
        "sorry": data["evidence"]["theory"]["sorry_count"],
        "song_max_onset": max(data["evidence"]["experiment"]["song"]["onset_tc_k"]),
        "semenok_unsuccessful": data["evidence"]["experiment"]["semenok"]["unsuccessful_attempts"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
