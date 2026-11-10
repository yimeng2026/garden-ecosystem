"""Build the DMRG/QEC evidence audit from nine frozen sources."""

import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

AUDIT = Path(__file__).resolve().parent
EXPECTED_HASHES = {
    "dmrg_notes": "59e6b00f0cb240b9b0d3417f0f7906ae0fb5cf4a9b7cbcf79a8229181147d392",
    "qec_notes": "59e747f55a96fd8d93885455d7ae7c2579acdeff4139e292023f5a723ec3fce2",
    "stripes_pdf": "d37490cd24da075fd622ef48bc3f212ce35fa09ec8db8bcd737a7fe4b04e1531",
    "finite_temperature_pdf": "e1ce8e1480fcf95156b7fffd23800b2b8dc4d6def9b64afb5835903cca3ae107",
    "extended_hubbard_pdf": "2cbaa6cd2ec3e9b00a61627d23cf3f5e3f5ac022b1cd80d73e495028646a7a55",
    "global_dwave_html": "3c2a77b1550f35e8a8eb8870150872cdc5e7b80c3ddd1d2799f9f455d3a2daca",
    "google_pdf": "9ba05a64dfec13f5d733e0e22484e8f22db2482dc2a5a0d63e6f0766c9c3d368",
    "xzzx_pdf": "918860f120639eb6897faff9d834aa977fbf54f781522276bff17c88c8db0cb7",
    "neutral_atoms_pdf": "0b81702eedfd2525eb6ab74fe82f43a7dbc930a219298f1f21c7ee7698afa8e7",
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
        "dmrg_notes": root / "14-资料收集-DMRG-Hubbard模型.md",
        "qec_notes": root / "18-资料收集-量子纠错码进展.md",
        "stripes_pdf": AUDIT / "sources/stripes-2501.15709.pdf",
        "finite_temperature_pdf": AUDIT / "sources/dwave-2211.06322.pdf",
        "extended_hubbard_pdf": AUDIT / "sources/extended-hubbard-2206.03486.pdf",
        "global_dwave_html": AUDIT / "sources/global-dwave-excerpts.md",
        "google_pdf": AUDIT / "sources/google-2408.13687.pdf",
        "xzzx_pdf": AUDIT / "sources/xzzx-surface-code.pdf",
        "neutral_atoms_pdf": AUDIT / "sources/neutral-atoms-s41586-023-06927-3.pdf",
    }
    display = {
        "dmrg_notes": "toe-sylva-audit/papers/room_temp_sc/organized/14-资料收集-DMRG-Hubbard模型.md",
        "qec_notes": "toe-sylva-audit/papers/room_temp_sc/organized/18-资料收集-量子纠错码进展.md",
        "stripes_pdf": "sources/stripes-2501.15709.pdf",
        "finite_temperature_pdf": "sources/dwave-2211.06322.pdf",
        "extended_hubbard_pdf": "sources/extended-hubbard-2206.03486.pdf",
        "global_dwave_html": "sources/global-dwave-excerpts.md",
        "google_pdf": "sources/google-2408.13687.pdf",
        "xzzx_pdf": "sources/xzzx-surface-code.pdf",
        "neutral_atoms_pdf": "sources/neutral-atoms-s41586-023-06927-3.pdf",
    }
    sources = []
    for source_id, path in paths.items():
        actual = sha256(path)
        if actual != EXPECTED_HASHES[source_id]:
            raise ValueError(f"source hash changed: {source_id}: {actual}")
        sources.append({"id": source_id, "path": display[source_id], "sha256": actual, "read_only": True})

    return {
        "schema": "dmrg-qec-audit-v1",
        "date": "2026-11-10",
        "scope": "DMRG 与量子纠错两份资料文档；只审计，不重跑模型、解码器或硬件实验。",
        "sources": sources,
        "source_lineage": {
            "research_program_count": 1,
            "decision": "两份文档属于同一研究纲领的模型证据与跨学科资料层，不是两个独立新理论。",
        },
        "directions": [
            {
                "id": "dmrg_evidence_ladder",
                "role": "短程关联、有限温度、有限宽度基态和二维极限分层",
                "closed": "Qu、Chen 与条纹综述的证据层级和编号映射已核清。",
                "unfinished": "更宽系统、热力学极限、系综一致性和键维数收敛未闭合。",
                "next": "复现公开代码数据，分别报告有限温度、基态、有限宽度和外推边界。",
            },
            {
                "id": "extended_model_completion",
                "role": "近邻吸引、声子候选和系综／键维数对模型结论的影响",
                "closed": "Peng 四腿 d 波增强与前作一维 p 波通道已分开。",
                "unfinished": "真实材料吸引强度、声子来源、二维极限和多方法交叉验证。",
                "next": "以扩展模型为参数化研究对象，不把单个配对通道当完整机制。",
            },
            {
                "id": "qec_benchmark_roles",
                "role": "噪声模型、解码器、阈值、延迟和硬件证据的同口径基准",
                "closed": "XZZX、Google 和中性原子数值及码族角色已核实。",
                "unfinished": "跨解码器比较、码族开销、真实噪声和长期逻辑性能基准未统一。",
                "next": "按噪声、码、解码器和硬件建立四维证据卡，禁止只比阈值。",
            },
            {
                "id": "cross_domain_governance",
                "role": "书目、码族、硬件平台与高温超导跨学科假说的血缘治理",
                "closed": "Chen 时间、Google 首次、中性原子拼接和涡旋越级已定位。",
                "unfinished": "其余引文未全审，涡旋量子比特和双重容错没有实验链。",
                "next": "逐条补齐 DOI 与原文定位；跨学科内容按已验证、可行假说和待证定义分层。",
            },
        ],
        "evidence": {
            "dmrg": {
                "finite_temperature": {
                    "arxiv": "2211.06322",
                    "max_width": 6,
                    "min_temperature_t_over_j": 0.06,
                    "positive_t_prime_dome": True,
                    "negative_t_prime_weaker": True,
                    "infinite_2d_ground_state_proof": False,
                },
                "global_ground_state": {
                    "arxiv": "2311.15092",
                    "legs": 8,
                    "uniform_abs_t2_over_t1": 0.15,
                    "pure_tj_dwave": True,
                    "gce_natural_ground_state": True,
                    "code_data_available": True,
                    "thermodynamic_limit_proven": False,
                    "pnas_year": 2025,
                    "document_year": 2024,
                    "code_url": "https://github.com/DongNingSheng/Grand_SQL_tJ/tree/main",
                },
            },
            "stripes": {
                "arxiv": "2501.15709",
                "dwave_reference_ids": [43, 44],
                "cdw_reference_ids": [41, 42],
                "document_mapping_reversed": True,
                "energy_difference_t": 0.01,
                "width8_conflict": True,
            },
            "extended_hubbard": {
                "arxiv": "2206.03486",
                "article": "L201102",
                "journal": "Physical Review B 107",
                "legs": 4,
                "current_dwave_enhancement": True,
                "current_pwave_result": False,
                "previous_1d_pwave": True,
            },
            "qec": {
                "xzzx": {
                    "depolarizing_threshold": 0.187,
                    "pure_pauli_threshold": 0.5,
                    "decoder": "approximate maximum likelihood",
                    "cross_decoder_threshold_comparison_valid": False,
                },
                "google": {
                    "arxiv": "2408.13687",
                    "distances": [5, 7],
                    "lambda": 2.14,
                    "lambda_uncertainty": 0.02,
                    "latency_us": 63,
                    "first_below_threshold_claim_supported": False,
                    "prior_surface_code_2023": True,
                },
                "neutral_atoms": {
                    "year": 2024,
                    "journal": "Nature 626",
                    "logical_48_code": "3D [[8,3,2]]",
                    "distance7_surface_bell_pairs": True,
                    "logical_48_ldpc_distance7": False,
                },
            },
            "cross_domain": {
                "ldpc_universal_overhead_and_decoding": False,
                "vortex_qubit_experimental_evidence": False,
                "double_fault_tolerance_proven": False,
            },
        },
        "corrections": [
            {"id": "finite_ground", "severity": "P0", "finding": "有限温度、有限宽度基态和二维极限被混写。", "action": "Qu 与 Chen 分轨；保留 8-leg 结果，不升级为无限二维证明。"},
            {"id": "stripe_reference_swap", "severity": "P1", "finding": "width-8 的 [41,42] 与 [43,44] 证据编号写反。", "action": "改为 [43,44] 报告 d 波，[41,42] 更接近 CDW；保留冲突和亚稳态边界。"},
            {"id": "extended_channel", "severity": "P1", "finding": "前作一维 p 波与 Peng 四腿 d 波增强容易混淆。", "action": "引用 PRB 107, L201102，并区分前作和当前模型。"},
            {"id": "chen_metadata", "severity": "P1", "finding": "Chen 全局相图被标为 2024-12-10，书目元数据不精确。", "action": "使用 PNAS 2025／arXiv:2311.15092 的真实身份，保留其科学结果。"},
            {"id": "xzzx_scope", "severity": "P0", "finding": "XZZX 阈值被用于跨噪声和解码器的直接比较。", "action": "18.7% 与约 50% 分别绑定噪声模型；不得与电路级约 1% 直接横比。"},
            {"id": "google_first", "severity": "P1", "finding": "Google 被写成首次低于阈值，忽略已有表面码标度工作。", "action": "保留距离 5/7、Λ=2.14 和 63 μs，改为后续里程碑而非绝对首次。"},
            {"id": "neutral_conflation", "severity": "P0", "finding": "48 个逻辑量子比特与 distance-7、LDPC、2025 被拼成一项结果。", "action": "改为 2024 年 48 个 3D [[8,3,2]] 逻辑量子比特；d=7 表面码 Bell 对另列。"},
            {"id": "ldpc_generalization", "severity": "P1", "finding": "LDPC 的更高阈值、O(d) 开销和线性解码被泛化为全码族性质。", "action": "逐码列参数、连接度、解码器和硬件条件，不做统一渐近承诺。"},
            {"id": "vortex_overreach", "severity": "P0", "finding": "YBCO 涡旋量子比特和双重容错被写成已有技术路线。", "action": "降为待验证假说，先提供相干时间、耦合、读出和实验协议。"},
        ],
        "open_boundaries": {
            "dmrg_2d_limit_proven": False,
            "qec_threshold_cross_model_comparable": False,
            "neutral_48_ldpc_d7_verified": False,
            "vortex_qubit_verified": False,
            "all_citations_checked": False,
            "full_repository_audit": False,
        },
        "figure": {
            "svg": "dmrg-qec-evidence.svg",
            "png": "dmrg-qec-evidence.png",
            "labels": ["8-leg", "18.7%", "63 μs", "[[8,3,2]]", "distance-7 LDPC"],
            "caption": "图 1　模型证据与硬件证据必须分层",
            "insert_after": "证据角色表",
            "insert_before": "结果解释",
            "success_percentage_plotted": False,
        },
        "verification_scope": {
            "source_documents_modified": False,
            "dmrg_or_tensor_network_rerun": False,
            "decoder_or_hardware_rerun": False,
            "all_citations_checked": False,
            "full_repository_audit": False,
        },
    }


def box(axis, y, text, face, edge="#455A64", height=0.16, size=11):
    patch = FancyBboxPatch((0.09, y), 0.82, height, boxstyle="round,pad=0.012,rounding_size=0.018",
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
    axes[0].set_title("DMRG：模型、温度与宽度分层", fontsize=16, fontweight="bold", color="#263238", pad=18)
    box(axes[0], 0.73, "Qu：有限温度热张量网络\nW≤6；T/J≥0.06；正 t′ 穹顶、负 t′ 更弱", "#E8F0F2")
    box(axes[0], 0.45, "Chen：8-leg 基态 DMRG\n纯 t-J d 波；|t₂/t₁|≳0.15 均匀 SC", "#E4EFE9")
    box(axes[0], 0.16, "仍未闭合：无限二维热力学极限\n系综一致性、键维数收敛与更宽系统", "#F5E8E4", edge="#A65D4E")
    axes[0].text(0.50, 0.055, "三层证据相关，但不能互相替代。", transform=axes[0].transAxes,
                 ha="center", fontsize=11, color="#546E7A")

    axes[1].set_title("QEC：真实硬件结果 ≠ 拼接结论", fontsize=16, fontweight="bold", color="#263238", pad=18)
    box(axes[1], 0.73, "Google：d=5／7；Λ=2.14±0.02\n63 μs 实时解码；不是稳妥的绝对首次", "#E4EFE9")
    box(axes[1], 0.45, "中性原子（2024）\n48×3D [[8,3,2]]；另有 d=7 表面码 Bell 对", "#E8F0F2")
    box(axes[1], 0.16, "不能拼接为：48 个 distance-7 LDPC\nYBCO 涡旋量子比特与双重容错仍未验证", "#F5E8E4", edge="#A65D4E")
    axes[1].text(0.50, 0.055, "XZZX：18.7% 去极化；约 50% 纯 Pauli 噪声\n不与电路级约 1% 直接横比。", transform=axes[1].transAxes,
                 ha="center", fontsize=10.5, color="#546E7A", linespacing=1.4)
    fig.suptitle("模型证据与硬件证据必须分层", fontsize=20, fontweight="bold", color="#263238", y=0.985)
    fig.text(0.5, 0.012, "只显示证据角色，不构造成功率、验证百分比或跨领域证明。", ha="center", fontsize=10, color="#607D8B")
    fig.subplots_adjust(left=0.035, right=0.98, top=0.87, bottom=0.08)
    fig.savefig(AUDIT / data["figure"]["svg"], metadata={"Date": None})
    fig.savefig(AUDIT / data["figure"]["png"], dpi=220, metadata={"Software": None})
    plt.close(fig)


def build_markdown(data):
    finite = data["evidence"]["dmrg"]["finite_temperature"]
    global_row = data["evidence"]["dmrg"]["global_ground_state"]
    stripes = data["evidence"]["stripes"]
    extended = data["evidence"]["extended_hubbard"]
    qec = data["evidence"]["qec"]
    lines = [
        "# DMRG 与量子纠错：证据阶梯、硬件角色与未竟工作审计",
        "",
        "> 日期：2026-11-10。只审计，不修改原文，不重跑模型、解码器或硬件实验。",
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
        "## 二、DMRG：有限温度、有限宽度基态和二维极限",
        "",
        "| 证据 | 实际结果 | 不能升级为 |",
        "|:--|:--|:--|",
        f"| Qu：arXiv:2211.06322 | 有限温度；W≤{finite['max_width']}；T/J≥{finite['min_temperature_t_over_j']}；正 t′ 穹顶、负 t′ 更弱 | 无限二维零温基态证明 |",
        f"| Chen：arXiv:2311.15092 | {global_row['legs']}-leg 基态；纯 t-J d 波；|t₂/t₁|≳{global_row['uniform_abs_t2_over_t1']} 均匀 SC；有代码数据 | 无限二维热力学极限已证明 |",
        f"| 条纹综述：arXiv:2501.15709 | [43,44] 报告 d 波，[41,42] 更接近 CDW；能量差约 {stripes['energy_difference_t']}t | 所有 DMRG 已得到同一基态 |",
        f"| Peng：PRB 107, {extended['article']} | 长四腿圆柱中近邻吸引增强 d 波关联 | 把前作一维 p 波当成本文直接结论 |",
        "",
        "Chen 的结果真实且重要，应发展为公开代码复现和更宽系统研究，而不是删除。其 GCE 自然基态、有限键维数和有限宽度仍需显式披露。",
        "",
        "## 三、QEC：阈值、解码器和硬件不能跨层拼接",
        "",
        "| 证据 | 实际结果 | 证据边界 |",
        "|:--|:--|:--|",
        f"| XZZX | 去极化 {qec['xzzx']['depolarizing_threshold']*100:.1f}%；纯 Pauli 约 {qec['xzzx']['pure_pauli_threshold']*100:.0f}% | 不与电路级约 1% 直接横比 |",
        f"| Google | d=5/7；Λ={qec['google']['lambda']}±{qec['google']['lambda_uncertainty']}；{qec['google']['latency_us']} μs | 后续里程碑，不写成无条件的绝对首次 |",
        f"| 中性原子 | {qec['neutral_atoms']['year']} 年；48×{qec['neutral_atoms']['logical_48_code']}；另有 d=7 表面码 Bell 对 | 不能写成 48 个 distance-7 LDPC |",
        "",
        "![图 1：模型证据与硬件证据必须分层](dmrg-qec-evidence.svg)",
        "",
        "**图件插入顺序：图 1 位于证据角色表之后、结果解释之前。** 图中没有成功率或验证百分比。",
        "",
        "LDPC 的更高阈值、O(d) 开销和线性解码不是全码族统一性质。YBCO 涡旋量子比特与“拓扑保护＋QEC 双重容错”仍是待验证假说，需要相干时间、耦合、读出和实验协议。",
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
        "优先顺序：先修正证据编号与码族身份，再复现 Chen 的公开代码数据、建立 QEC 四维证据卡；跨学科部分先完成物理可实现性定义，不以类比替代实验。",
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
        "本批使用九项冻结来源、原始 PDF／HTML 和独立文本合同。命令与退出码见 `run.log`；Word 逐页结果见 `word-qa/report.json`。其余引文未全审。",
        "",
        "本批没有重跑模型、解码器或硬件实验，没有修改两份原文。**全库审计尚未完成。**",
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
        "chen_legs": data["evidence"]["dmrg"]["global_ground_state"]["legs"],
        "xzzx_depolarizing": data["evidence"]["qec"]["xzzx"]["depolarizing_threshold"],
        "google_lambda": data["evidence"]["qec"]["google"]["lambda"],
        "neutral_48_code": data["evidence"]["qec"]["neutral_atoms"]["logical_48_code"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
