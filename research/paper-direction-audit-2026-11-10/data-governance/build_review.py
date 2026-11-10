"""Build the overview/technical-review data-governance evidence audit."""

import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

AUDIT = Path(__file__).resolve().parent
EXPECTED_HASHES = {
    "hydrides_overview": "5b3c56d2ea572412b894f6643fb2ab7e31e693ad7755b63e112e51c0fa46f277",
    "batch_overview": "243ef403bc372d13b442cc0086807fade7f7f478dba010bbfef2d3b9eeb11167",
    "complete_overview": "314402bf0ae374bd74200c3a8492af8727b53082062d26b3bb7eaf28f2aa4fc7",
    "technical_review": "992707a8092e65297ebe604d16d5ca203c0f2e0e32a76b43132e16133b7bea05",
    "htsc_pdf": "b1669a6771c685519a5fbcfb45258dd606b957df23720405663408f59809af01",
    "patsnap_excerpts": "4c43394d89bf1d8eb48e2a9dadb6b7396b2640f1a702f7ae87a19c65bb6d6a10",
    "boron_prb111_excerpts": "542a2bac4ad20821e68b87879c7a07a1c10128dabfe3b6e9c8207f5c51973883",
    "main_claims_review": "e9ac6ff0bc88f11b1c2c91ae61ce398a05fc077815803f48669b46536d6f2f45",
    "validation_materials_review": "17eaa27d30df6849f752e3712d563ebe492ae394ea9c74b1b072ac0755acb491",
    "isotope_dft_review": "e04428ca5980171619ca97bd2cc450fa772074cd9edd73f980905a72b1c2d4b4",
    "dmrg_qec_review": "367fada5ec9f68011ea50bb437922d140aa7fcb77bbab7517d8548196332a68d",
    "methods_review": "f30d15d8665644d11957166efaea95d59f7a742037dc697b737704cd15dc9e21",
}


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_root():
    for parent in AUDIT.parents:
        candidate = parent / "toe-sylva-audit/papers/room_temp_sc/organized"
        if candidate.is_dir():
            return candidate
    raise FileNotFoundError("room_temp_sc organized root")


def build_data():
    root = source_root()
    paths = {
        "hydrides_overview": root / "12-资料收集-氢化物与验证进展.md",
        "batch_overview": root / "16-资料收集-总览与下一步.md",
        "complete_overview": root / "20-资料收集-总览与完整清单.md",
        "technical_review": root / "21-技术复盘-全领域数据审计.md",
        "htsc_pdf": AUDIT / "sources/htsc-2506.03837v2.pdf",
        "patsnap_excerpts": AUDIT / "sources/patsnap-excerpts.md",
        "boron_prb111_excerpts": AUDIT / "sources/boron-prb111-excerpts.md",
        "main_claims_review": AUDIT.parent / "main-claims/review.json",
        "validation_materials_review": AUDIT.parent / "validation-materials/review.json",
        "isotope_dft_review": AUDIT.parent / "isotope-dft/review.json",
        "dmrg_qec_review": AUDIT.parent / "dmrg-qec/review.json",
        "methods_review": AUDIT.parent / "room-temp-methods/review.json",
    }
    display = {
        "hydrides_overview": "toe-sylva-audit/papers/room_temp_sc/organized/12-资料收集-氢化物与验证进展.md",
        "batch_overview": "toe-sylva-audit/papers/room_temp_sc/organized/16-资料收集-总览与下一步.md",
        "complete_overview": "toe-sylva-audit/papers/room_temp_sc/organized/20-资料收集-总览与完整清单.md",
        "technical_review": "toe-sylva-audit/papers/room_temp_sc/organized/21-技术复盘-全领域数据审计.md",
        "htsc_pdf": "sources/htsc-2506.03837v2.pdf",
        "patsnap_excerpts": "sources/patsnap-excerpts.md",
        "boron_prb111_excerpts": "sources/boron-prb111-excerpts.md",
        "main_claims_review": "main-claims/review.json",
        "validation_materials_review": "validation-materials/review.json",
        "isotope_dft_review": "isotope-dft/review.json",
        "dmrg_qec_review": "dmrg-qec/review.json",
        "methods_review": "room-temp-methods/review.json",
    }
    sources = []
    for source_id, path in paths.items():
        actual = sha256(path)
        if actual != EXPECTED_HASHES[source_id]:
            raise ValueError(f"source hash changed: {source_id}: {actual}")
        sources.append({"id": source_id, "path": display[source_id], "sha256": actual, "read_only": True})
    return {
        "schema": "data-governance-audit-v1",
        "date": "2026-11-10",
        "scope": "第 12、16、20、21 份资料、总览与技术复盘；只审计，不重跑计算或实验。",
        "sources": sources,
        "source_lineage": {
            "research_program_count": 1,
            "decision": "四份文档是同一研究纲领的资料、总览与技术复盘层，不是四个独立新理论。",
        },
        "directions": [
            {
                "id": "claim_lineage",
                "role": "原始证据、单篇审计和多份总览之间的单一事实源与纠错传播",
                "closed": "Song 循环确认、Kruglov 和 QEC 重复错误已定位。",
                "unfinished": "其余总览引文未全审，四份原文尚未同步修订。",
                "next": "以结构化证据卡为唯一事实源，传播勘误并保留修改记录。",
            },
            {
                "id": "benchmark_scope",
                "role": "HTSC 的样本、压力、BCS、去泄漏和外部验证范围治理",
                "closed": "140 个样本、27.3 K 平均值、160 K 上限及排除规则已核实。",
                "unfinished": "Jiang 原始值、外部模型评估、独立 DFT 验证和数据版本差异未闭合。",
                "next": "冻结去泄漏划分，分开常压基准与高压候选并公开失败案例。",
            },
            {
                "id": "data_completeness",
                "role": "从有表格升级为谱函数、结构、输入、日志和不确定度的可复现完整性",
                "closed": "N_F 单位、Kruglov 文章号、方法混用和 SI 模板边界已核清。",
                "unfinished": "完整谱函数、结构、赝势、k/q、收敛日志和不确定度仍缺失。",
                "next": "为每个数据矩阵项绑定原始文件、输入、日志、单位和可复算脚本。",
            },
            {
                "id": "research_update",
                "role": "B–C、Chen、Floquet 和 QEC 等方向的证据分级与动态更新",
                "closed": "B–C 预测、Chen 8-leg、Google 和中性原子角色已分开。",
                "unfinished": "B–C 实验、Chen 更宽系统、Floquet 实验和涡旋量子比特仍未验证。",
                "next": "按预测、作者报告、独立复现和工程实现滚动更新，不复制旧结论。",
            },
        ],
        "evidence": {
            "song": {
                "arxiv": "2510.01273",
                "onset_tc_k": [271, 298],
                "direct_meissner_completed": False,
                "independent_positive_replication": False,
                "first_four_standards_met": False,
                "all_five_standards_met": False,
                "duplicate_overviews_not_independent_evidence": True,
            },
            "htsc": {
                "arxiv": "2506.03837v2",
                "sample_count": 140,
                "average_tc_k": 27.3,
                "maximum_tc_k": 160,
                "high_pressure_excluded": True,
                "unconventional_excluded": True,
                "leakage_exclusion_required": True,
                "open_data_available": True,
                "open_data_url": "https://github.com/xqh19970407/HTSC-2025",
                "li2nah17_document_tc_k": 340,
                "li2nah17_htsc_discussion_tc_k": 297,
                "li2nah17_outside_benchmark": True,
                "li2nah17_requires_jiang_source": True,
            },
            "validation": {
                "patsnap_secondary_blog": True,
                "global_consensus_established": False,
                "blog_threshold_k": 273,
                "project_theorem_threshold_k": 300,
            },
            "boron": {
                "article": "PRB 111, 014510",
                "compound_count": 96,
                "ca_b8c_predicted_tc_k": 77.1,
                "experimental_realization": False,
            },
            "kruglov": {
                "article": "024508",
                "nf_unit": "states/f.u./Ry",
                "nf_unit_states_per_ev": False,
                "full_spectrum_and_inputs_open": False,
            },
            "pressure": {
                "mixed_method_curve": True,
                "experimental_curve_established": False,
            },
            "research_update": {
                "dmrg": {
                    "chen_legs": 8,
                    "thermodynamic_limit_proven": False,
                    "static_all_controversy_only": False,
                    "code_data_available": True,
                },
                "qec": {
                    "google_absolute_first_supported": False,
                    "neutral_48_ldpc_distance7": False,
                    "neutral_48_code": "3D [[8,3,2]]",
                },
            },
            "governance": {
                "completed_status_not_evidence": True,
                "duplicates_not_independent": True,
                "all_overview_claims_checked": False,
            },
        },
        "corrections": [
            {"id": "song_circular", "severity": "P0", "finding": "多份总览把 Song 写成迈斯纳已证实和前四项满足。", "action": "改为作者正向预印本；直接 Meissner、独立复现和同行评议未确立，重复总览不是独立证据。"},
            {"id": "htsc_scope", "severity": "P0", "finding": "常压 HTSC 与 300 GPa 候选混写。", "action": "保留 140／27.3／160 与去泄漏规则；Li₂NaH₁₇ 不纳入，340／297 差异列 Jiang 原文待核。"},
            {"id": "validation_consensus", "severity": "P1", "finding": "Patsnap 五项标准被当成全球共识。", "action": "降为二手博客框架；273 K 与项目 300 K 分开，具体材料逐项回源。"},
            {"id": "boron_experiment", "severity": "P1", "finding": "B–C 预测被写成实验里程碑。", "action": "保留 96 个化合物与 CaB₈C 77.1 K 预测，明确尚无实验实现。"},
            {"id": "kruglov_units", "severity": "P0", "finding": "Kruglov 文章号 224508 和 N_F 的 eV 单位重复错误。", "action": "改为 024508 与 states/f.u./Ry；保留参数表，不冒称全谱和输入开放。"},
            {"id": "pressure_method", "severity": "P1", "finding": "压力斜率被当成同一方法或纯实验曲线。", "action": "按 Eliashberg／SCDFT／实验分轨，方法一致时再求导。"},
            {"id": "dmrg_update", "severity": "P1", "finding": "总览只重复 DMRG 全部争议，未吸收 Chen 新结果。", "action": "更新为 Chen 8-leg 基态进展与二维极限未闭合，复用公开代码数据。"},
            {"id": "qec_copy", "severity": "P0", "finding": "Google 首次与 48×distance-7 LDPC 的复制错误进入总览。", "action": "Google 改为后续里程碑；中性原子改为 48×3D [[8,3,2]]，d=7 Bell 对另列。"},
            {"id": "data_matrix", "severity": "P1", "finding": "有参数表被当成完整谱、完整输入和可复现数据。", "action": "为每个矩阵项绑定原始谱、结构、输入、日志、单位和不确定度。"},
            {"id": "completed_status", "severity": "P1", "finding": "归档和完成状态被当成证据闭合，重复引用被当成独立确认。", "action": "状态只表示文件归档；以原始证据卡和独立复核决定完成度。"},
        ],
        "open_boundaries": {
            "meissner_verified": False,
            "first_four_standards_met": False,
            "htsc_high_pressure_included": False,
            "boron_experimental_realization": False,
            "full_spectrum_open": False,
            "all_overview_claims_checked": False,
            "full_repository_audit": False,
        },
        "figure": {
            "svg": "data-governance-evidence.svg",
            "png": "data-governance-evidence.png",
            "labels": ["140", "27.3 K", "77.1 K", "[[8,3,2]]", "直接 Meissner 未确立"],
            "caption": "图 1　总览宣称必须回到原始证据",
            "insert_after": "证据角色表",
            "insert_before": "结果解释",
            "verification_percentage_plotted": False,
        },
        "verification_scope": {
            "source_documents_modified": False,
            "new_dft_dmrg_decoder_or_experiment": False,
            "jiang_original_value_verified": False,
            "all_overview_claims_checked": False,
            "full_repository_audit": False,
        },
    }


def box(axis, y, text, face, edge="#455A64", height=0.16, size=11):
    patch = FancyBboxPatch((0.08, y), 0.84, height, boxstyle="round,pad=0.012,rounding_size=0.018",
                           transform=axis.transAxes, facecolor=face, edgecolor=edge, linewidth=1.3)
    axis.add_patch(patch)
    axis.text(0.50, y + height / 2, text, transform=axis.transAxes, ha="center", va="center",
              fontsize=size, color="#263238", linespacing=1.45)


def build_figure(data):
    plt.rcParams["font.family"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
    fig, axes = plt.subplots(1, 2, figsize=(12.8, 7.2), gridspec_kw={"wspace": 0.12})
    fig.patch.set_facecolor("#FAFBFC")
    for axis in axes:
        axis.set_axis_off()
        axis.set_xlim(0, 1)
        axis.set_ylim(0, 1)
    axes[0].set_title("总览宣称 → 原始证据", fontsize=16, fontweight="bold", color="#263238", pad=18)
    box(axes[0], 0.74, "多份总览：四探针＋Meissner／前四项\n重复引用形成循环确认", "#F5E8E4", edge="#A65D4E")
    box(axes[0], 0.47, "原始证据：Song onset 271–298 K\n直接 Meissner 未确立；独立正向复现未确立", "#E4EFE9")
    box(axes[0], 0.19, "HTSC：140 个样本；平均 27.3 K；最高 160 K\n高压与非 BCS 明确排除；训练集须去泄漏", "#E8F0F2")
    axes[0].text(0.50, 0.055, "归档 ≠ 验证；重复总览 ≠ 独立证据。", transform=axes[0].transAxes,
                 ha="center", fontsize=11, color="#546E7A")

    axes[1].set_title("可发展方向 → 分级与待办", fontsize=16, fontweight="bold", color="#263238", pad=18)
    box(axes[1], 0.74, "B–C：96 个化合物；CaB₈C 77.1 K\n第一性原理预测，不是实验实现", "#E8F0F2")
    box(axes[1], 0.51, "Chen：8-leg 基态 d 波＋公开代码数据\n进展真实；无限二维仍未证明", "#E4EFE9")
    box(axes[1], 0.28, "Google：63 μs 实时解码\n中性原子：48×3D [[8,3,2]]；不是 48×d7 LDPC", "#E8F0F2")
    box(axes[1], 0.075, "下一步：原始谱／输入／日志／不确定度\nJiang 原文值、B–C 实验与更宽系统仍待完成", "#F3EEE4", height=0.14, size=10.5)
    fig.suptitle("总览宣称必须回到原始证据", fontsize=20, fontweight="bold", color="#263238", y=0.985)
    fig.text(0.5, 0.012, "只显示证据角色和未竟工作，不构造成功率或验证百分比。", ha="center", fontsize=10, color="#607D8B")
    fig.subplots_adjust(left=0.035, right=0.98, top=0.87, bottom=0.08)
    fig.savefig(AUDIT / data["figure"]["svg"], metadata={"Date": None})
    fig.savefig(AUDIT / data["figure"]["png"], dpi=220, metadata={"Software": None})
    plt.close(fig)


def build_markdown(data):
    song = data["evidence"]["song"]
    htsc = data["evidence"]["htsc"]
    validation = data["evidence"]["validation"]
    boron = data["evidence"]["boron"]
    kruglov = data["evidence"]["kruglov"]
    dmrg = data["evidence"]["research_update"]["dmrg"]
    qec = data["evidence"]["research_update"]["qec"]
    lines = [
        "# 总览与技术复盘：事实血缘、基准范围与未竟工作审计",
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
        "## 二、Song 循环确认与 HTSC 真实范围",
        "",
        "| 项目 | 总览中的问题 | 原始证据裁决 |",
        "|:--|:--|:--|",
        "| Song | 四探针＋迈斯纳、前四项满足 | onset 271–298 K；直接 Meissner 和独立正向复现未确立；重复总览不构成独立证据 |",
        f"| HTSC | 常压基准与 300 GPa 候选混写 | {htsc['sample_count']} 个样本；平均 {htsc['average_tc_k']} K；最高 {htsc['maximum_tc_k']} K；高压和非 BCS 排除 |",
        "| Li₂NaH₁₇ | 资料写 340 K，HTSC 讨论写 297 K | 明确不纳入 HTSC；Jiang 原始值待核，本批不擅断哪个值正确 |",
        f"| 五项标准 | 二手博客被当成全球共识 | Patsnap 可作内部清单；{validation['blog_threshold_k']} K 与项目 {validation['project_theorem_threshold_k']} K 不混用 |",
        "",
        "HTSC 的开放数据、去泄漏训练划分和 BCS 快速验证流程值得保留。后续应分开常压基准与高压候选，公开失败案例和外部 DFT 验证。",
        "",
        "## 三、可发展的研究方向及其边界",
        "",
        "| 方向 | 已核实进展 | 未竟工作 |",
        "|:--|:--|:--|",
        f"| B–C 笼状结构 | {boron['compound_count']} 个化合物；CaB₈C 预测 {boron['ca_b8c_predicted_tc_k']} K | 不是实验实现，需要合成与输运验证 |",
        f"| Chen DMRG | {dmrg['chen_legs']}-leg 基态 d 波；公开代码数据 | 更宽系统与无限二维极限未闭合 |",
        "| Kruglov／压力 | 文章号 024508；N_F 为 states/f.u./Ry；斜率算术成立 | 方法混用，不是纯实验曲线；全谱和输入未开放 |",
        "| Google／中性原子 | 63 μs 实时解码；48×3D [[8,3,2]] | 不写绝对首次，不写 48×distance-7 LDPC |",
        "",
        "![图 1：总览宣称必须回到原始证据](data-governance-evidence.svg)",
        "",
        "**图件插入顺序：图 1 位于证据角色表之后、结果解释之前。** 图中没有验证百分比。",
        "",
        "所有研究方向都可以继续，但必须按预测、作者报告、独立复现和工程实现分级更新。B–C 需要实验，Chen 需要更宽系统，Floquet 需要实验验证，涡旋量子比特需要物理实现协议。",
        "",
        "## 四、分档勘误与数据治理任务",
        "",
        "| 级别 | 已观察问题 | 建议动作 |",
        "|:--|:--|:--|",
    ]
    for row in data["corrections"]:
        lines.append(f"| {row['severity']} | {row['finding']} | {row['action']} |")
    lines += [
        "",
        "数据矩阵的完整性不再以“有表格”判断，而以原始谱、结构、输入、日志、单位和不确定度判断。归档只表示文件存在，重复总览只表示同一结论被复制，均不等于验证。",
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
        "本批使用十二项冻结来源、HTSC 原文、Patsnap 与 PRB 摘要及既有审计对象。命令与退出码见 `run.log`；Word 逐页结果见 `word-qa/report.json`。",
        "",
        "本批没有重跑计算或实验，没有核实 Jiang 原始值，没有修改四份原文。**全库审计尚未完成。**",
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
        "htsc_samples": data["evidence"]["htsc"]["sample_count"],
        "htsc_average": data["evidence"]["htsc"]["average_tc_k"],
        "boron_ca_tc": data["evidence"]["boron"]["ca_b8c_predicted_tc_k"],
        "meissner": data["open_boundaries"]["meissner_verified"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
