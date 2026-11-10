"""Build the room-temperature-SC methods audit from frozen read-only sources."""

import hashlib
import json
import re
from pathlib import Path

AUDIT = Path(__file__).resolve().parent
EXPECTED_HASHES = {
    "latest_digest": "41aea15ed19c68375f29877f7e22deba22394757df178cb67ca827a458a0aa75",
    "floquet_notes": "37b5436dc39bada84c3a520943ea94515d5d08e75c27e808aba5070059d48ab9",
    "eliashberg_notes": "841c1954c7fea9c41e3179476602c64b47eca936643f383e24215284324d0a20",
    "lean_markdown": "c171f6e5d5e5b6547bddc88d94138b9dc0a87d8c3a6ec59ff696e35746f59141",
    "si_template": "9d54064ba6089c82de39ddef90afeb82e47d511f95b35dd0490ee50aef63d97f",
    "lean_standalone": "1971e95d7b375c24778d3adae8a1ab3be4c5abeb1ee8b79a2b1f347b7aa00439",
}
SOURCE_PATHS = {
    "latest_digest": "latest_research_digest.md",
    "floquet_notes": "organized/13-资料收集-Floquet工程LaH10.md",
    "eliashberg_notes": "organized/15-资料收集-Eliashberg理论边界.md",
    "lean_markdown": "organized/07-形式化代码/01-Lean形式化代码.md",
    "si_template": "organized/10-技术文档/06-补充信息.md",
    "lean_standalone": "room_temp_sc_Formalization.lean",
}
SOURCE_URLS = {
    "xie": "https://www.nature.com/articles/s41524-025-01725-z",
    "dmrg": "https://journals.aps.org/prl/abstract/10.1103/PhysRevLett.133.256003",
    "lasc2h24": "https://www.pnas.org/doi/10.1073/pnas.2401840121",
    "kiessling": "https://arxiv.org/html/2409.00532",
}


def find_source_root(start=AUDIT):
    for parent in start.parents:
        candidate = parent / "toe-sylva-audit/papers/room_temp_sc"
        if candidate.is_dir():
            return candidate
    raise FileNotFoundError("toe-sylva-audit/papers/room_temp_sc not found")


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def theorem_sorry_names(text):
    names = []
    blocks = re.findall(r"(?ms)^theorem\s+(\w+).*?(?=^theorem\s+|\Z)", text)
    # Capture the name separately so the proof-hole decision stays local to each theorem.
    for match in re.finditer(r"(?ms)^theorem\s+(\w+).*?(?=^theorem\s+|\Z)", text):
        if re.search(r"(?m)^\s*sorry\s*$", match.group(0)):
            names.append(match.group(1))
    if len(names) != len(blocks):
        raise AssertionError("theorem block extraction mismatch")
    return names


def placeholder_counts(text):
    patterns = {
        "to_be_imported": r"to be imported",
        "to_be_specified": r"to be specified",
        "pending_chinese": r"待补充",
        "placeholder": r"placeholder",
        "software_marker": r"\[software\]",
        "repository_marker": r"\[repository URL\]",
    }
    return {
        name: len(re.findall(pattern, text, flags=re.IGNORECASE))
        for name, pattern in patterns.items()
    }


def build_data():
    root = find_source_root()
    texts = {}
    sources = []
    for source_id, relative in SOURCE_PATHS.items():
        path = root / relative
        actual = sha256(path)
        expected = EXPECTED_HASHES[source_id]
        if actual != expected:
            raise ValueError(f"source hash changed: {source_id}: {actual} != {expected}")
        texts[source_id] = path.read_text(encoding="utf-8")
        sources.append({
            "id": source_id,
            "path": f"toe-sylva-audit/papers/room_temp_sc/{relative}",
            "sha256": actual,
            "read_only": True,
        })

    sharp = 0.1827262477
    multiplier = 2.034
    proof_holes = len(re.findall(r"(?m)^\s*(?:admit|sorry)\b", texts["lean_markdown"]))
    proof_tokens = len(re.findall(r"\b(?:admit|sorry)\b", texts["lean_markdown"]))
    sorry_names = theorem_sorry_names(texts["lean_standalone"])
    si_counts = placeholder_counts(texts["si_template"])

    directions = [
        {
            "id": "floquet_evidence",
            "role": "非平衡第一性原理估计与 DOS-scaling 下界的分层研究",
            "status": "verified_corrections_open_physics",
            "closed": "已回源纠正高压压力—Tc 顺序，并区分直接估计与低压下界。",
            "unfinished": "热效应、非平衡分布、泵浦损伤、样品可实现性、独立复算和实验验证。",
            "next": "建立按压力、泵浦、方法、近似和证据等级索引的原始数据包。",
        },
        {
            "id": "eliashberg_bounds",
            "role": "严格数学界与经验 Tc 估算之间的接口",
            "status": "source_roles_clarified_formalization_open",
            "closed": "sharp constant、非最优上界和经验公式角色已分开。",
            "unfinished": "归一化、定理假设、变分命题链和材料级适用域尚未形式化闭合。",
            "next": "先建立统一定义，再逐项形式化严格界，禁止从经验公式升格必然性。",
        },
        {
            "id": "lean_formalization",
            "role": "形式化草案与证明债务清偿方向",
            "status": "draft_not_machine_verified",
            "closed": "已定位 Markdown 草案和独立 Lean 文件的显式证明债务。",
            "unfinished": "命题类型、物理假设、全部证明体、公理审计和真实构建均未完成。",
            "next": "先修复弱耦合与 Floquet 命题，再逐定理清偿并执行 #print axioms。",
        },
        {
            "id": "literature_digest",
            "role": "研究情报综述，不是独立新理论",
            "status": "selected_corrections_verified_rest_not_fully_audited",
            "closed": "DMRG 与 LaSc₂H₂₄ 的卷期和证据角色已回源。",
            "unfinished": "其他实验段落和外部 Lean 指标未逐项回源，不能整体背书。",
            "next": "给每条综述记录 DOI、原文定位、证据等级和最后核验日期。",
        },
        {
            "id": "reproducible_si",
            "role": "可复现材料计算的待建基础设施",
            "status": "template_only",
            "closed": "已识别 SI 的占位符和缺失资产，不将模板当成结果。",
            "unfinished": "DFT 输入、结构、赝势、收敛日志、声子、Eliashberg 输出和重跑脚本。",
            "next": "选一个材料做最小可复现垂直切片，再扩展材料表。",
        },
    ]

    corrections = [
        {
            "id": "xie_pressure_order",
            "severity": "P0",
            "source_id": "floquet_notes",
            "observed": "220 GPa→322 K；250 GPa→320 K",
            "corrected": "220 GPa→320 K；250 GPa→322 K",
            "reason": "Xie 正式论文 lines 421-428 的直接文本核对。",
        },
        {
            "id": "dmrg_bibliography",
            "severity": "P1",
            "source_id": "latest_digest",
            "observed": "PRL 132, 066002",
            "corrected": "PRL 133, 256003（2024-12-19）",
            "reason": "APS 官方页面与 DOI 10.1103/PhysRevLett.133.256003。",
        },
        {
            "id": "lasc_issue",
            "severity": "P1",
            "source_id": "latest_digest",
            "observed": "PNAS 121(25)",
            "corrected": "PNAS 121(26), e2401840121",
            "reason": "PNAS 官方卷期信息。",
        },
        {
            "id": "lean_limit_statement",
            "severity": "P0",
            "source_id": "lean_standalone",
            "observed": "把 λ → 0 与逻辑箭头用于极限定理陈述，且证明位为 sorry。",
            "corrected": "降级为待修正命题与证明债务，不称为极限定理或机器证明。",
            "reason": "独立 Lean 文件 lines 82-93；本批未运行编译。",
        },
    ]

    return {
        "schema": "room-temp-methods-direction-audit-v1",
        "date": "2026-11-10",
        "scope": "五份 room_temp_sc 方法与形式化文档，附查一份独立 Lean 文件；只审计，不改原文。",
        "sources": sources,
        "source_lineage": {
            "research_program_count": 1,
            "decision": "五份文档属于同一 room_temp_sc 研究纲领的五种方法角色，不是五个独立新理论。",
        },
        "directions": directions,
        "corrections": corrections,
        "evidence": {
            "floquet": {
                "title": "Dynamical approach to realize room-temperature superconductivity in LaH10",
                "doi": "10.1038/s41524-025-01725-z",
                "journal": "npj Computational Materials 11, 227 (2025)",
                "source_url": SOURCE_URLS["xie"],
                "local_text": "sources/xie-floquet-fulltext.txt",
                "dfpt_estimates": [
                    {
                        "pressure_gpa": 220,
                        "equilibrium_tc_k": 258,
                        "driven_tc_k": 320,
                        "field_mv_per_angstrom": 80,
                        "role": "direct_floquet_dfpt_allen_dynes_estimate",
                        "source_lines": "421-428",
                    },
                    {
                        "pressure_gpa": 250,
                        "equilibrium_tc_k": 237,
                        "driven_tc_k": 322,
                        "field_mv_per_angstrom": 80,
                        "role": "direct_floquet_dfpt_allen_dynes_estimate",
                        "source_lines": "421-428",
                    },
                ],
                "dos_scaling_estimates": [
                    {
                        "pressure_gpa": 150,
                        "equilibrium_tc_k": 249,
                        "driven_tc_k": 285,
                        "field_mv_per_angstrom": 80,
                        "role": "lower_bound_not_accurate_prediction",
                        "source_lines": "556-584",
                    },
                    {
                        "pressure_gpa": 200,
                        "equilibrium_tc_k": 240,
                        "driven_tc_k": 301,
                        "field_mv_per_angstrom": 80,
                        "role": "lower_bound_not_accurate_prediction",
                        "source_lines": "556-584",
                    },
                ],
                "not_all_hydrides_above_room_temperature": True,
                "hydrides_scope_lines": "591-594",
                "experimental_confirmation": False,
            },
            "dmrg": {
                "title": "Phase Diagram, d-Wave Superconductivity, and Pseudogap of the t-t′-J Model at Finite Temperature",
                "journal": "Physical Review Letters",
                "volume": 133,
                "article": "256003",
                "published": "2024-12-19",
                "doi": "10.1103/PhysRevLett.133.256003",
                "arxiv": "2211.06322",
                "source_url": SOURCE_URLS["dmrg"],
                "max_cylinder_width": 6,
                "minimum_temperature_t_over_j": 0.06,
                "max_characteristic_tc_star_over_j": 0.15,
                "positive_t_prime_behavior": "穹顶状 SC 区与发散 d 波配对磁化率",
                "negative_t_prime_behavior": "配对关联明显更弱",
                "complete_cuprate_explanation": False,
            },
            "lasc2h24": {
                "title": "Predicted hot superconductivity in LaSc2H24 under pressure",
                "journal": "Proceedings of the National Academy of Sciences",
                "volume": 121,
                "issue": 26,
                "article": "e2401840121",
                "doi": "10.1073/pnas.2401840121",
                "source_url": SOURCE_URLS["lasc2h24"],
                "predictions": [
                    {"pressure_gpa": 167, "maximum_tc_k": 316},
                    {"pressure_gpa": 250, "maximum_tc_k": 331},
                ],
                "anharmonic_dynamic_stability_down_to_gpa": 150,
                "theoretical_prediction": True,
                "experimental_confirmation": False,
            },
            "eliashberg": {
                "source": "Kiessling, Altshuler, Yuzbashyan, arXiv:2409.00532v3",
                "source_url": SOURCE_URLS["kiessling"],
                "sharp_constant": sharp,
                "upper_bound_multiplier": multiplier,
                "upper_bound_coefficient": sharp * multiplier,
                "upper_bound_is_sharp": False,
                "allen_dynes_role": "经验公式，不替代严格界或其假设",
                "room_temp_necessity_proven": False,
            },
            "lean": {
                "status": "draft_not_machine_verified",
                "markdown_proof_hole_count": proof_holes,
                "markdown_admit_sorry_token_count": proof_tokens,
                "standalone_sorry_theorems": sorry_names,
                "standalone_sorry_count": len(sorry_names),
                "weak_coupling_limit_statement_valid": False,
                "floquet_confidence_annotation": 0.05,
                "build_attempted": False,
                "build_passed": False,
                "note": "未运行 Lean 编译；字符串计数只用于定位债务，不代表证明困难度。",
            },
            "external_lean_metrics": {
                "status": "unverified",
                "claimed_line_count": 15000,
                "claimed_proof_terms": 845,
                "claimed_instances": 127,
                "claimed_seconds": 43,
                "reason": "当前条目没有可精确复核的实现版本和构建记录，不据此判定真假。",
            },
            "si": {
                "status": "template_only",
                "placeholder_count": sum(si_counts.values()),
                "placeholder_pattern_counts": si_counts,
                "dft_inputs_provided": False,
                "phonon_spectra_provided": False,
                "convergence_logs_provided": False,
                "material_results_provided": False,
                "note": "文件列表是模板声明，不证明对应资产存在。",
            },
        },
        "out_of_scope_findings": [
            {
                "path": "papers/room_temp_sc/organized/08-手册章节/04-第6章_未来展望.md",
                "lines": "222,372,384-385",
                "severity": "P0_candidate",
                "status": "high_risk_unverified",
                "finding": "将 LaSc₂H₂₄ 写成实验实现并附 Nature 文献，与已核 PNAS 理论预测角色冲突。",
                "next": "在手册批次独立回源并修正，不在本批直接改原文或判定虚构。",
            },
            {
                "path": "papers/room_temp_sc/organized/02-主论文/02-Nature版本.md；03-Science版本.md；04-arXiv版本.md",
                "lines": "摘要与材料预测段",
                "severity": "P0_candidate",
                "status": "claim_evidence_mismatch",
                "finding": "必然性、严格导出和材料预测措辞与当前 Lean 草案、SI 模板不匹配。",
                "next": "主论文批次逐条对照 proof_status 与计算资产后降级或补证。",
            },
            {
                "path": "papers/room_temp_sc/organized/02-主论文/01-主论文.md",
                "lines": "60,220-222,296",
                "severity": "P1",
                "status": "placeholder_confirmed",
                "finding": "仍有 [To be imported]，不是完整主论文。",
                "next": "主论文批次先移除交付完整性误判，再填充真实证明和数据。",
            },
        ],
        "open_boundaries": {
            "global_fit": False,
            "material_prediction": False,
            "lean_proof_verified": False,
            "dft_inputs_available": False,
            "phonon_spectra_available": False,
            "full_repository_audit_completed": False,
        },
        "verification_scope": {
            "source_documents_modified": False,
            "lean_compilation_run": False,
            "new_material_prediction": False,
            "new_global_fit": False,
            "primary_sources_checked": ["Xie", "APS DMRG", "PNAS LaSc2H24", "Kiessling"],
        },
    }


def floquet_rows(data):
    f = data["evidence"]["floquet"]
    return [("Floquet-DFPT + Allen–Dynes 估计", row) for row in f["dfpt_estimates"]] + [
        ("DOS-scaling 下界", row) for row in f["dos_scaling_estimates"]
    ]


def build_markdown(data):
    lines = [
        "# room_temp_sc 方法与形式化小组：证据角色与未竟工作审计",
        "",
        "> 日期：2026-11-10。对象：五份文档及一份独立 Lean 文件。只生成审计报告，不修改原文，不新增材料预测、全参数拟合或 Lean 证明。",
        "",
        "## 一、血缘裁决与总判断",
        "",
        "这五份文档属于**同一 room_temp_sc 研究纲领**，分别承担 Floquet 证据、Eliashberg 边界、Lean 形式化、研究综述和 SI 基础设施五种角色。它们不是五个独立新理论，书目修正也不等于新的科学突破。",
        "",
        "当前最重要的结论不是“理论已经被证明”，而是：两组书目/数值错误可以明确纠正；严格数学界与经验公式必须分工；Lean 和 SI 都仍有实质未竟工作。",
        "",
        "| 来源 ID | 只读路径 | SHA-256 |",
        "|:--|:--|:--|",
    ]
    for row in data["sources"]:
        lines.append(f"| `{row['id']}` | `{row['path']}` | `{row['sha256']}` |")

    lines += [
        "",
        "## 二、五个方法方向，而非五个新理论",
        "",
        "| 方向 | 当前角色 | 已闭合的局部审计 | 未竟工作与下一步 |",
        "|:--|:--|:--|:--|",
    ]
    for row in data["directions"]:
        lines.append(
            f"| `{row['id']}` | {row['role']} | {row['closed']} | {row['unfinished']}**下一步：**{row['next']} |"
        )

    lines += [
        "",
        "## 三、可复核的更正与证据边界",
        "",
        "| 编号 | 级别 | 原记录 | 审计裁决 | 依据 |",
        "|:--|:--|:--|:--|:--|",
    ]
    for row in data["corrections"]:
        lines.append(
            f"| `{row['id']}` | {row['severity']} | {row['observed']} | {row['corrected']} | {row['reason']} |"
        )

    f = data["evidence"]["floquet"]
    lines += [
        "",
        "### 3.1 Floquet-LaH₁₀：压力顺序与近似角色",
        "",
        "**220 GPa → 320 K；250 GPa → 322 K。** 资料表原先把这两个结果对调；以下同时保留平衡态、驱动态、方法和原文行号。",
        "",
        "| 压力（GPa） | 平衡态 Tc（K） | 驱动态 Tc（K） | 场强（mV/Å） | 方法与证据角色 | 原文行 |",
        "|---:|---:|---:|---:|:--|:--|",
    ]
    for method, row in floquet_rows(data):
        role = "直接估计" if row in f["dfpt_estimates"] else "下界，不是准确点预测"
        lines.append(
            f"| {row['pressure_gpa']} | {row['equilibrium_tc_k']} | {row['driven_tc_k']} "
            f"| {row['field_mv_per_angstrom']} | {method}；{role} | {row['source_lines']} |"
        )
    lines += [
        "",
        "150 GPa 的 285 K 和 200 GPa 的 301 K 来自 DOS-scaling。Xie 原文明确说它们不应被视为准确预测，而是 Floquet-DFPT 结果的下界；不能和 320/322 K 混成同等级、无条件精确预测。原文还明确并非所有被考察氢化物都超过室温。上述均为理论计算，不是实验确认。",
        "",
        f"原始来源：[Xie et al., npj Computational Materials 11, 227 (2025)]({f['source_url']})；本地提取 `{f['local_text']}`。",
        "",
        "### 3.2 DMRG／t-t′-J：正确书目与有限尺寸边界",
        "",
    ]
    d = data["evidence"]["dmrg"]
    lines += [
        f"正确书目是 **{d['journal']} {d['volume']}, {d['article']}**，发表于 {d['published']}，DOI `{d['doi']}`，不是 PRL 132, 066002。",
        "",
        f"官方摘要限定圆柱宽度最多 W={d['max_cylinder_width']}，最低到 T/J≈{d['minimum_temperature_t_over_j']}。t′/t>0 时出现{d['positive_t_prime_behavior']}，特征温度最高约 {d['max_characteristic_tc_star_over_j']}J；t′/t<0 时{d['negative_t_prime_behavior']}。这些结果支持模型研究，但不等于铜氧化物高温超导已被完整解释。",
        "",
        f"原始来源：[APS 官方摘要]({d['source_url']})。",
        "",
        "### 3.3 LaSc₂H₂₄：预测不是实验纪录",
        "",
    ]
    m = data["evidence"]["lasc2h24"]
    lines += [
        f"正确书目是 **PNAS {m['volume']}({m['issue']}), {m['article']}**。167 GPa 下预测最高 316 K，250 GPa 下预测最高 331 K；非谐效应使动力学稳定延伸到 {m['anharmonic_dynamic_stability_down_to_gpa']} GPa。",
        "",
        "这些值来自结构搜索、第一性原理、SSCHA 与各向同性 Eliashberg 计算，是**理论预测，不是实验证实**，不能升级为当前最高实验纪录。",
        "",
        f"原始来源：[PNAS 官方全文与摘要]({m['source_url']})。",
        "",
        "## 四、Eliashberg：严格界、非最优上界与经验公式",
        "",
    ]
    e = data["evidence"]["eliashberg"]
    lines += [
        f"Kiessling 等给出的 sharp constant 为 `{e['sharp_constant']}…`；另一个非最优上界的渐近系数约为其 {e['upper_bound_multiplier']} 倍：",
        "",
        f"$$C_{{\\mathrm{{upper}}}}\\approx {e['upper_bound_multiplier']}C_{{\\mathrm{{sharp}}}}\\approx {e['upper_bound_coefficient']:.6f}.$$",
        "",
        "两者不是同一个常数，也不承担同一个证明角色。Kiessling 的严格下界、非最优上界与 Allen–Dynes 经验公式必须分别写明假设、归一化和适用域；经验公式不能替代严格证明，非最优上界不能改名为 sharp constant，更不能由此直接推出“室温超导必然性”。",
        "",
        f"原始来源：[Kiessling, Altshuler, Yuzbashyan, arXiv:2409.00532v3]({e['source_url']})。",
        "",
        "## 五、Lean：草案，不是机器证明",
        "",
    ]
    lean = data["evidence"]["lean"]
    lines += [
        f"Markdown 形式化文档有 {lean['markdown_proof_hole_count']} 处行首 `admit`/`sorry` 标记；独立 Lean 文件中定位到 {lean['standalone_sorry_count']} 个带显式证明位 `sorry` 的定理：",
        "",
    ]
    for name in lean["standalone_sorry_theorems"]:
        lines.append(f"- `{name}`。")
    lines += [
        "",
        "弱耦合条目把 `λ → 0` 和逻辑箭头用于命题陈述，不是正确的极限或等式表达；Floquet 条目自身注释仅给 `CONFIDENCE: 0.05`。因此这里只能登记为**草案，不是机器证明**。本批没有运行 Lean 编译，也不声称构建通过。",
        "",
        "综述中的 15,000 行、845 证明项、127 实例、43 秒及“完整陈数基础设施”缺少精确实现版本与构建记录，本批标为**未核实**，不据此判真或判假。",
        "",
        "下一步应先修正命题类型和物理假设，再逐定理清偿证明，记录真实构建与 `#print axioms`；禁止用新公理、证明位占位或空真定理制造绿色状态。",
        "",
        "## 六、SI：模板，不是已完成的补充信息",
        "",
    ]
    si = data["evidence"]["si"]
    lines += [
        f"当前 SI 含有 {si['placeholder_count']} 处按既定模式计数的导入、待指定、待补充或占位标记。DFT 参数、声子网格、Eliashberg 函数、材料预测表、灵敏度表、数据仓库和代码清单均未形成可审计资产。",
        "",
        "因此它是**模板，不是已完成的补充信息**。模板列出 `phonon_spectra/` 等目录不证明这些文件存在。下一步应选一个材料做最小可复现垂直切片：冻结结构和输入，记录软件版本与赝势，完成 k/q/截断能收敛，保存声子和 Eliashberg 输出，并提供独立重跑脚本与哈希清单。",
        "",
        "## 七、范围外缺陷登记（不在本批改原文）",
        "",
        "| 路径与行号 | 级别/状态 | 已观察问题 | 后续动作 |",
        "|:--|:--|:--|:--|",
    ]
    for row in data["out_of_scope_findings"]:
        lines.append(
            f"| `{row['path']}`；{row['lines']} | {row['severity']}／{row['status']} | {row['finding']} | {row['next']} |"
        )
    lines += [
        "",
        "这些条目只登记实际读到的高风险内容。未回源的文献不判为虚构，范围外文件不计入本批五份文档的完成量。",
        "",
        "## 八、优先级与未竟事业",
        "",
        "1. **P0 数据与声明止损**：另开原文修订分支，先修正 Floquet 压力映射，再处理主论文/手册的实验—预测和证明—草案错位。",
        "2. **可复现垂直切片**：不要先填满 SI 表格；先完成一个材料的输入—收敛—声子—Tc—日志闭环。",
        "3. **形式化命题先行**：先修命题，再谈证明；Kiessling 严格界与 Allen–Dynes 经验公式分轨。",
        "4. **综述证据卡**：为每条文献记录 DOI、原文定位、证据等级、最后核验日期和未核实状态。",
        "5. **实验与独立复算**：Floquet 的热、损伤和非平衡分布问题不解决，不能把 Tc 估计写成实验路线图中的既定结果。",
        "",
        "## 九、验证范围与禁止升格",
        "",
        "本报告使用冻结哈希、原始论文/官方摘要和机器合同。最终命令、实际退出码和关键输出见 `run.log`；Word 结构验证及最终视图结果见 `word-qa/report.json`。",
        "",
        "`global_fit=false`，`material_prediction=false`，`lean_proof_verified=false`，`dft_inputs_available=false`，`phonon_spectra_available=false`。本批没有重跑 Floquet-DFPT、DMRG、DFT、SSCHA 或 Lean，也没有新增材料预测或证明。",
        "",
        "**全库审计尚未完成。** 本批只闭合五份方法/形式化文档的选定问题；room_temp_sc 其他文档和全库未竟工作仍需分批推进。",
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
    (AUDIT / "REVIEW.md").write_text(
        build_markdown(data), encoding="utf-8", newline="\n"
    )
    print(json.dumps({
        "sources": len(data["sources"]),
        "research_program_count": data["source_lineage"]["research_program_count"],
        "directions": len(data["directions"]),
        "corrections": len(data["corrections"]),
        "markdown_proof_holes": data["evidence"]["lean"]["markdown_proof_hole_count"],
        "standalone_sorry_count": data["evidence"]["lean"]["standalone_sorry_count"],
        "si_placeholders": data["evidence"]["si"]["placeholder_count"],
        "out_of_scope_findings": len(data["out_of_scope_findings"]),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
