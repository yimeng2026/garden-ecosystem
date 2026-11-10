"""Build the manuscript/handbook evidence audit from frozen primary assets."""

import hashlib
import json
from pathlib import Path

AUDIT = Path(__file__).resolve().parent
EXPECTED_HASHES = {
    "main_master": "862e3232520ee961bc307a8e97cfd0b32a869a97197b159281596be3437d227f",
    "nature_version": "fc5505cff6e3f65ee080ae4ec7a8f51f8ea2b4404e33a0d59146122bf91c568c",
    "science_version": "598de079d503596b9c9a5d43ba5027fafc5d9a13a12c4b3b03a3ba3e36d2e809",
    "arxiv_version": "7893cc30f25baca9aef27a3a3f9fc1a232e86fafdde109753885487f9268fc3b",
    "handbook_materials": "2816948242751325c7d3d28995f1ce836fb064e426f7d2bc941df3b14c8d5acd",
    "handbook_future": "43e7826fac1fd4260e1cf0c01bf2ba6c1ffd6616652bb9b8825ea4fa006443bd",
    "critical_results": "f9438c770c1125c68b42a67778458d551f3694d1954b112bdf61d6942bac970b",
    "prior_methods_review": "cc73b74ad9951d6b0d25dee50ac06babd8f8ea2ffdde8a4823923d506cc466f7",
    "song_pdf": "b820d4dac9162c0f8b914282afbbbe85e7005bce68c7b217abff070a715debdf",
    "semenok_pdf": "a1dc4c13ecf800baf422e97aa51ba004b85ec7e6e32ecc7bf9f850df39a09bef",
}
DOC_PATHS = {
    "main_master": "organized/02-主论文/01-主论文.md",
    "nature_version": "organized/02-主论文/02-Nature版本.md",
    "science_version": "organized/02-主论文/03-Science版本.md",
    "arxiv_version": "organized/02-主论文/04-arXiv版本.md",
    "handbook_materials": "organized/08-手册章节/03-第4-5章_材料与实验.md",
    "handbook_future": "organized/08-手册章节/04-第6章_未来展望.md",
}
URLS = {
    "pnas": "https://www.pnas.org/doi/10.1073/pnas.2401840121",
    "song": "https://arxiv.org/abs/2510.01273",
    "semenok": "https://arxiv.org/abs/2605.29985",
    "nature_crossref": "https://api.crossref.org/works/10.1038/s41586-024-07036-5",
    "review_2026": "https://iopscience.iop.org/article/10.1088/1361-648X/ae7ccd",
}


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def find_source_root():
    for parent in AUDIT.parents:
        candidate = parent / "toe-sylva-audit/papers/room_temp_sc"
        if candidate.is_dir():
            return candidate
    raise FileNotFoundError("toe-sylva-audit room_temp_sc source root")


def find_critical_results():
    for parent in AUDIT.parents:
        candidate = parent / ".worktrees/critical-manifold/papers/room_temp_sc/critical_manifold/results.json"
        if candidate.is_file():
            return candidate
    raise FileNotFoundError("critical-manifold results.json")


def build_data():
    source_root = find_source_root()
    critical_path = find_critical_results()
    prior_path = AUDIT.parent / "room-temp-methods/review.json"
    paths = {key: source_root / relative for key, relative in DOC_PATHS.items()}
    paths.update({
        "critical_results": critical_path,
        "prior_methods_review": prior_path,
        "song_pdf": AUDIT / "sources/song-2510.01273.pdf",
        "semenok_pdf": AUDIT / "sources/semenok-2605.29985.pdf",
    })
    display_paths = {key: f"toe-sylva-audit/papers/room_temp_sc/{DOC_PATHS[key]}" for key in DOC_PATHS}
    display_paths.update({
        "critical_results": ".worktrees/critical-manifold/papers/room_temp_sc/critical_manifold/results.json",
        "prior_methods_review": "research/paper-direction-audit-2026-11-10/room-temp-methods/review.json",
        "song_pdf": "sources/song-2510.01273.pdf",
        "semenok_pdf": "sources/semenok-2605.29985.pdf",
    })
    sources = []
    for source_id, path in paths.items():
        actual = sha256(path)
        expected = EXPECTED_HASHES[source_id]
        if actual != expected:
            raise ValueError(f"source hash changed: {source_id}: {actual} != {expected}")
        sources.append({
            "id": source_id,
            "path": display_paths[source_id],
            "sha256": actual,
            "read_only": True,
        })

    critical = read_json(critical_path)
    prior = read_json(prior_path)
    lean = prior["evidence"]["lean"]
    si = prior["evidence"]["si"]
    directions = [
        {
            "id": "necessity_proof",
            "role": "简化公式、严格数学界与必然性措辞的边界研究",
            "closed": "三组数值反例与证明债务已定位，普遍必然性不能按现稿成立。",
            "unfinished": "完整命题、假设、严格下界、Lean 命题类型和证明体均未闭合。",
            "next": "先收缩标题与摘要，再建立可检验的充分条件或条件化命题。",
        },
        {
            "id": "reproducible_computation",
            "role": "材料计算与 SI 可复现基础设施",
            "closed": "SI 仍是模板，主论文中的 DFT 完成式措辞没有对应资产。",
            "unfinished": "结构、输入、赝势、k/q/截断能收敛、声子和 Eliashberg 输出。",
            "next": "先做一个材料的垂直复现切片，再恢复计算验证章节。",
        },
        {
            "id": "experimental_controversy",
            "role": "LaSc₂H₂₄ 的正向实验报告与独立负向复现研究",
            "closed": "Song 与 Semenok 预印本均存在，证据角色和相反结果已核清。",
            "unfinished": "独立正向复现、同行评议、直接 Meissner、前驱体有序化和同位素验证。",
            "next": "并列保存两组原始数据，优先解决前驱体和跨实验室复现。",
        },
        {
            "id": "publication_governance",
            "role": "版本、引文、叙事和证据等级治理",
            "closed": "Nature 卷页错配已确认；成功率、日期和终极证明措辞已分档。",
            "unfinished": "六份原文修订、勘误留痕、未核实叙事处理和版本同步。",
            "next": "先修 P0 引文和证明措辞，再同步 P1 时间线与证据卡。",
        },
    ]
    corrections = [
        {
            "id": "nature_reference",
            "severity": "P0",
            "target": "handbook_future [C1]",
            "finding": "Nature 626, 779–784 被错配为 LaSc₂H₂₄ 论文。",
            "action": "删除错误引文并留痕，改引 PNAS、Song、Semenok 各自真实身份。",
        },
        {
            "id": "necessity_claim",
            "severity": "P0",
            "target": "四份主论文标题、摘要、证明和结论",
            "finding": "形式证明／严格验证措辞与证明占位、SI 模板及数值反例不相容。",
            "action": "降级为条件化研究框架；完成命题与反例处置前不得恢复必然性措辞。",
        },
        {
            "id": "success_and_ultimate_proof",
            "severity": "P0",
            "target": "handbook_materials 5.5–5.6、本章小结",
            "finding": "成功率 100%、铁证、独立确认和终极证明超出当前证据。",
            "action": "改为作者报告 13 次可重复运行，同时披露独立负向复现与未决问题。",
        },
        {
            "id": "date_and_preprint_status",
            "severity": "P1",
            "target": "handbook_future 结语、术语和核心文献",
            "finding": "2024 年 320 K 实验叙述混淆 PNAS 预测与 Song 2025 预印本。",
            "action": "分开 2024 预测与 2025 报告，不倒填 Nature 或同行评议状态。",
        },
        {
            "id": "meissner_and_anecdote",
            "severity": "P1",
            "target": "handbook_materials 证据链与未公开故事",
            "finding": "直接 Meissner 未完成；成本与第 42/43 次故事未核实。",
            "action": "直接磁测量列为待办；叙事标未核实或删除并留痕，不判虚构。",
        },
        {
            "id": "prior_audit_time_addendum",
            "severity": "P1",
            "target": "room-temp-methods 前批范围外登记",
            "finding": "前批未纳入 Song 与 Semenok，不能继续简写为只有预测。",
            "action": "保留 PNAS 判断，补充正负预印本及本批链接。",
        },
    ]
    return {
        "schema": "room-temp-main-claims-audit-v1",
        "date": "2026-11-10",
        "scope": "四份主论文版本、两章手册及两份既有数值/方法证据；只审计，不修改原文。",
        "sources": sources,
        "source_lineage": {
            "research_program_count": 1,
            "decision": "六份文档是同一研究纲领的版本与叙事，不是六个独立新理论。",
        },
        "directions": directions,
        "corrections": corrections,
        "evidence": {
            "pnas_prediction": {
                "citation": "PNAS 121(26), e2401840121",
                "url": URLS["pnas"],
                "role": "2024 理论预测",
                "predictions": [
                    {"pressure_gpa": 167, "maximum_tc_k": 316},
                    {"pressure_gpa": 250, "maximum_tc_k": 331},
                ],
            },
            "song": {
                "arxiv": "2510.01273",
                "version": "v2 (2025-10-06)",
                "url": URLS["song"],
                "exists": True,
                "reports_experimental_synthesis": True,
                "onset_tc_k": [271, 298],
                "pressure_gpa": [195, 266],
                "synthesis_pressure_gpa": [250, 260],
                "reported_methods": ["零电阻", "外加磁场抑制 Tc", "同步辐射 XRD"],
                "reproducible_runs_reported": 13,
                "peer_review_established": False,
                "independent_positive_replication": False,
                "direct_meissner_completed": False,
                "evidence_role": "作者正向实验预印本，不等于独立确认或必然性证明",
            },
            "semenok": {
                "arxiv": "2605.29985",
                "version": "v2 (2026-08-20)",
                "url": URLS["semenok"],
                "exists": True,
                "unsuccessful_attempts": 7,
                "synthesis_pressure_gpa": [250, 280],
                "no_superconductivity_range_k": [245, 300],
                "theoretical_tc_above_300_at_300_gpa": True,
                "precursor_engineering_possible_key": True,
                "evidence_role": "独立负向复现预印本，不是对 Song 或整个材料族的最终否证",
            },
            "controversy": {
                "contested_evidence": True,
                "independent_negative_replication_exists": True,
                "independent_positive_replication_established": False,
                "resolution": "open_precursor_and_replication_required",
                "review_2026_url": URLS["review_2026"],
            },
            "nature_citation": {
                "claimed_title": "Superconductivity above 320 K in lanthanum-scandium polyhydride at megabar pressures",
                "claimed_authors": "Chen, X., et al. (2024)",
                "claimed_journal": "Nature 626, 779-784",
                "actual_title": "Twisted-layer boron nitride ceramic with high deformability and strength",
                "actual_doi": "10.1038/s41586-024-07036-5",
                "actual_pages": "779-784",
                "crossref_url": URLS["nature_crossref"],
                "citation_mismatch": True,
            },
            "critical_manifold": {
                "path": ".worktrees/critical-manifold/papers/room_temp_sc/critical_manifold/results.json",
                "scope": critical["scope"],
                "K_per_meV": critical["constants"]["K_per_meV"],
                "denominator_temperature": critical["constants"]["denominator_temperature"],
                "root_count": critical["domain"]["root_count"],
                "grid_point_count": critical["domain"]["grid_point_count"],
                "grid_class_disagreements": critical["summary"]["grid_class_disagreements"],
                "temperature_anchors": critical["temperature_anchors"],
                "full_eliashberg_theory_refuted": False,
                "material_prediction": False,
            },
            "formalization": {
                "markdown_proof_hole_count": lean["markdown_proof_hole_count"],
                "standalone_sorry_count": lean["standalone_sorry_count"],
                "standalone_sorry_theorems": lean["standalone_sorry_theorems"],
                "build_attempted": lean["build_attempted"],
                "build_passed": lean["build_passed"],
                "status": lean["status"],
            },
            "si": {
                "placeholder_count": si["placeholder_count"],
                "status": si["status"],
                "dft_inputs_provided": si["dft_inputs_provided"],
                "phonon_spectra_provided": si["phonon_spectra_provided"],
                "convergence_logs_provided": si["convergence_logs_provided"],
            },
            "handbook_narrative": {
                "success_rate_100_supported": False,
                "anecdote_status": "unverified",
                "cost_status": "unverified",
                "direct_meissner_completed": False,
                "independent_cross_lab_confirmation": False,
                "ultimate_necessity_proven": False,
            },
        },
        "prior_audit_addendum": {
            "required": True,
            "pnas_prediction_role_unchanged": True,
            "song_was_missing": True,
            "semenok_was_missing": True,
            "decision": "保留前批 PNAS 预测角色；补充正负实验预印本，不再将总体状态简写为只有预测。",
        },
        "open_boundaries": {
            "formal_proof_completed": False,
            "lean_proof_verified": False,
            "si_complete": False,
            "peer_review_established": False,
            "independent_positive_replication": False,
            "direct_meissner_completed": False,
            "success_rate_100_supported": False,
            "ultimate_necessity_proven": False,
            "full_repository_audit_completed": False,
        },
        "figure": {
            "svg": "claims-timeline.svg",
            "png": "claims-timeline.png",
            "caption": "图 1　理论预测、实验宣称与独立负向复现：不是真伪投票",
            "insert_after": "证据比较表",
            "insert_before": "争议解释",
        },
        "verification_scope": {
            "source_documents_modified": False,
            "lean_compilation_run": False,
            "new_material_prediction": False,
            "new_experiment_or_independent_replication": False,
        },
    }


def build_figure(data):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib import font_manager

    candidates = ["Microsoft YaHei", "Noto Sans CJK SC", "SimHei", "Arial Unicode MS"]
    available = {font.name for font in font_manager.fontManager.ttflist}
    for name in candidates:
        if name in available:
            plt.rcParams["font.family"] = name
            break
    plt.rcParams["axes.unicode_minus"] = False
    plt.rcParams["svg.hashsalt"] = "main-claims-timeline-v1"
    events = [
        (2024.45, "2024 PNAS\n理论预测 316/331 K", "#397a76"),
        (2024.63, "2024 Nature 卷页\n实为氮化硼陶瓷", "#8c4a52"),
        (2025.76, "2025 Song 预印本\n作者报告 271–298 K", "#4f6f8f"),
        (2026.63, "2026 Semenok 预印本\n7 次独立复现未成功", "#8c6d3f"),
    ]
    fig, ax = plt.subplots(figsize=(11.0, 4.8), dpi=180)
    ax.axhline(0, color="#607078", linewidth=1.4)
    for index, (year, label, color) in enumerate(events):
        y = 0.52 if index % 2 == 0 else -0.58
        ax.scatter([year], [0], s=82, color=color, zorder=3)
        ax.vlines(year, 0, y * 0.72, color=color, linewidth=1.1, alpha=0.8)
        ax.text(year, y, label, ha="center", va="center", fontsize=10, color=color)
    ax.set_xlim(2023.85, 2027.05)
    ax.set_ylim(-1.05, 1.05)
    ax.set_xticks([2024, 2025, 2026, 2027])
    ax.set_yticks([])
    for side in ("left", "right", "top"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color("#90a0a6")
    ax.set_title("理论预测、实验宣称与独立负向复现：不是真伪投票", fontsize=15, pad=18)
    ax.text(2024.0, -0.98, "时间点表示文献角色；实验争议仍需独立正向复现、同行评议和直接磁测量", fontsize=9, color="#52646b")
    fig.tight_layout()
    fig.savefig(AUDIT / "claims-timeline.svg", metadata={"Date": None})
    fig.savefig(AUDIT / "claims-timeline.png", dpi=220, metadata={"Software": "main-claims-audit"})
    plt.close(fig)


def build_markdown(data):
    song = data["evidence"]["song"]
    semenok = data["evidence"]["semenok"]
    nature = data["evidence"]["nature_citation"]
    critical = data["evidence"]["critical_manifold"]
    lean = data["evidence"]["formalization"]
    si = data["evidence"]["si"]
    lines = [
        "# 主论文四版本与手册两章：证据角色、实验争议与未竟工作审计",
        "",
        "> 日期：2026-11-10。只审计，不修改六份原文。预印本存在、作者报告、独立复现、同行评议和数学证明分别记录。",
        "",
        "## 一、总裁决",
        "",
        "当前不是“只有理论预测”，也不是“实验已经铁证完成”，而是**正向实验预印本与独立负向复现并存**。Song 的实验报告必须保留，Semenok 的负向结果同样必须保留；独立正向复现和同行评议尚未确立。",
        "",
        "四份主论文版本和两章手册属于同一研究纲领，不是六个新理论。本批形成必然性命题、可复现计算、实验争议和出版治理四个方法方向。",
        "",
        "| 来源 ID | 只读路径 | SHA-256 |",
        "|:--|:--|:--|",
    ]
    for row in data["sources"]:
        lines.append(f"| `{row['id']}` | `{row['path']}` | `{row['sha256']}` |")
    lines += [
        "",
        "## 二、四个方法方向",
        "",
        "| 方向 | 已闭合的局部审计 | 未竟工作与下一步 |",
        "|:--|:--|:--|",
    ]
    for row in data["directions"]:
        lines.append(f"| `{row['id']}`：{row['role']} | {row['closed']} | {row['unfinished']}**下一步：**{row['next']} |")
    lines += [
        "",
        "## 三、LaSc₂H₂₄：证据时间线与争议结构",
        "",
        "| 来源 | 文献角色 | 关键结果 | 不能升级为 |",
        "|:--|:--|:--|:--|",
        "| PNAS 121(26) | 2024 理论预测 | 167 GPa 最高 316 K；250 GPa 最高 331 K | 实验确认或后续实验的替代品 |",
        f"| Song，arXiv:2510.01273 | 2025 正向实验预印本 | 作者报告 {song['onset_tc_k'][0]}–{song['onset_tc_k'][1]} K／{song['pressure_gpa'][0]}–{song['pressure_gpa'][1]} GPa；{song['reproducible_runs_reported']} 次可重复运行 | 独立正向复现、同行评议、直接 Meissner 或必然性证明 |",
        f"| Semenok，arXiv:2605.29985 | 2026 独立负向复现预印本 | {semenok['unsuccessful_attempts']} 次合成未成功；{semenok['synthesis_pressure_gpa'][0]}–{semenok['synthesis_pressure_gpa'][1]} GPa 下未见 {semenok['no_superconductivity_range_k'][0]}–{semenok['no_superconductivity_range_k'][1]} K 超导 | 对 Song 或整个材料族的最终逻辑否证 |",
        "",
        f"![{data['figure']['caption']}](claims-timeline.svg)",
        "",
        "**图件插入顺序：图 1 位于证据比较表之后、争议解释之前。** 图中时间点表示文献角色，不是真伪投票，也不表示社区共识。",
        "",
        "Song 原文报告零电阻、磁场抑制和 XRD，并把高于 200 GPa 的直接 Meissner 磁测量列为后续工作。Semenok 原文报告七次未成功，同时仍讨论 300 GPa 下理论 Tc>300 K 和前驱体工程。两者并不支持简单投票式结论；下一步应核对前驱体有序化、原始数据和跨实验室正向复现。",
        "",
        f"来源：[PNAS]({data['evidence']['pnas_prediction']['url']})、[Song]({song['url']})、[Semenok]({semenok['url']})。",
        "",
        "## 四、Nature 引文错配：这是确定错误",
        "",
        f"手册 [C1] 把 Nature 626, 779–784 写成 `{nature['claimed_title']}`。Crossref 的权威元数据表明该卷页实际是 **{nature['actual_title']}**，DOI `{nature['actual_doi']}`，主题是氮化硼陶瓷，**不是 2024 年 Nature 论文**所声称的 LaSc₂H₂₄ 工作。",
        "",
        "后续原文修订应删除该错误引文并留痕，分别引用 PNAS 预测、Song 正向预印本和 Semenok 负向预印本。不得把 Song 的 2025 预印本倒填成 2024 Nature 论文，也不得写成已有独立实验室交叉验证。",
        "",
        f"核验：[Crossref 元数据]({nature['crossref_url']})。",
        "",
        "## 五、必然性命题：数值反例和证明债务",
        "",
        "临界流形使用同一简化 Allen–Dynes/McMillan 公式且 f₁=f₂=1：",
        "",
        "$$T_c^{\\mathrm{simple}}=\\frac{11.6\\,\\omega_{\\log}}{1.20}\\exp(-E).$$",
        "",
        "| λ | μ* | 输入 ωlog（meV） | Tc（K） |",
        "|---:|---:|---:|---:|",
    ]
    for row in critical["temperature_anchors"]:
        lines.append(f"| {row['lambda']} | {row['mu_star']} | {row['omega_log_meV']} | {row['tc_K']} |")
    lines += [
        "",
        f"三个锚点均低于 300 K。全量复核为 {critical['root_count']} 组根、{critical['grid_point_count']:,} 个直接点，分类不一致为 {critical['grid_class_disagreements']}。这反驳的是使用同一简化公式时的普适必然性措辞，**不否定完整 Eliashberg 理论、特定材料或 Song 的实验报告**。",
        "",
        f"前批方法审计还记录 Lean Markdown {lean['markdown_proof_hole_count']} 处行首证明债务、独立文件 {lean['standalone_sorry_count']} 个显式 sorry，未运行编译；SI 有 {si['placeholder_count']} 处既定模式占位，未提供 DFT 输入、声子谱或收敛日志。主论文的“形式证明”“完整 DFT 验证”不能按现稿成立。",
        "",
        "## 六、手册叙事：哪些可以说，哪些不能说",
        "",
        "- **可以说**：Song 作者报告 13 次可重复实验运行、零电阻、磁场抑制和 XRD。",
        "- **必须同时说**：Semenok 等报告七次未成功，独立正向复现与同行评议未确立，直接 Meissner 仍是待办。",
        "- **成功率 100% 不受支持**：13 次可重复运行没有提供总尝试分母，不能改写为“13 次全部成功”。",
        "- **未核实而非判假**：第 42/43 次故事、300 万元成本等在当前全文的针对性检索中未找到支持，标记未核实或删除并留痕。",
        "- **不能写**：“铁证”“独立实验室交叉验证”“必然性的终极证明”“2024 年 Nature 320 K 突破”。",
        "",
        "## 七、前批审计补充",
        "",
        data["prior_audit_addendum"]["decision"] + "这是一项时间边界补充，不是删除前批结果，也不意味着 PNAS 数值判断错误。",
        "",
        "## 八、分档勘误与后续优先级",
        "",
        "| 级别 | 对象 | 已观察问题 | 建议动作 |",
        "|:--|:--|:--|:--|",
    ]
    for row in data["corrections"]:
        lines.append(f"| {row['severity']} | {row['target']} | {row['finding']} | {row['action']} |")
    lines += [
        "",
        "P2 的实质研究任务包括：一个材料的完整计算复现切片、Lean 命题和证明清偿、前驱体有序化对照、独立正向复现、直接 Meissner 和同位素验证。书目纠错本身不等于科学突破。",
        "",
        "## 九、验证范围",
        "",
        "本批使用冻结哈希、原始 PDF、Crossref 元数据、前批方法审计和临界流形数值证据。独立来源复核见 `verify_primary_sources.py`；最终命令、退出码见 `run.log`；Word 逐页结果见 `word-qa/report.json`。",
        "",
        "本批没有运行 Lean、没有新做实验或独立复现、没有新增材料预测，也没有修改六份原文。**全库审计尚未完成。**",
        "",
    ]
    return "\n".join(lines)


def main():
    data = build_data()
    (AUDIT / "review.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    build_figure(data)
    (AUDIT / "REVIEW.md").write_text(build_markdown(data), encoding="utf-8", newline="\n")
    print(json.dumps({
        "sources": len(data["sources"]),
        "research_program_count": data["source_lineage"]["research_program_count"],
        "directions": len(data["directions"]),
        "corrections": len(data["corrections"]),
        "song_runs": data["evidence"]["song"]["reproducible_runs_reported"],
        "semenok_unsuccessful": data["evidence"]["semenok"]["unsuccessful_attempts"],
        "nature_citation_mismatch": data["evidence"]["nature_citation"]["citation_mismatch"],
        "critical_anchors_below_300": all(row["tc_K"] < 300 for row in data["evidence"]["critical_manifold"]["temperature_anchors"]),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
