"""Build traceable Floquet evidence records without editing the original sources."""

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RESEARCH = ROOT.parent
ORIGINAL = Path(
    "C:/Users/一梦/Documents/kimi/workspace/toe-sylva-audit/"
    "papers/room_temp_sc/room_temp_sc_Formalization.lean"
)
XIE = (
    RESEARCH
    / "paper-direction-audit-2026-11-10"
    / "room-temp-methods"
    / "sources"
    / "xie-floquet-fulltext.txt"
)


def normalized(text):
    return re.sub(r"\s+", " ", text).strip()


def main():
    # Keep the audit's LF line numbering; splitlines() also counts PDF form feeds.
    source_lines = XIE.read_text(encoding="utf-8").split("\n")
    original_lines = ORIGINAL.read_text(encoding="utf-8").split("\n")
    assert original_lines[170].strip().startswith("theorem floquet_enhanced_tc")
    assert original_lines[184].strip() == "sorry"
    anchors = [
        {"id": "diagonal_floquet_blocks", "lines": [194, 203], "quote": "We analyze the non -thermal steady-state electronic"},
        {"id": "off_resonant_400mev", "lines": [204, 212], "quote": "chosen as the mid-IR laser (ℏΩ = 400 meV)"},
        {"id": "off_resonant_approximation", "lines": [204, 212], "quote": "allowing the off-resonance approximations in the Floquet-DFPT calcula-"},
        {"id": "fixed_phonons", "lines": [263, 280], "quote": "unchanged in the non-thermal state, since the equilibrium states are"},
        {"id": "allen_dynes_estimator", "lines": [420, 428], "quote": "Here, we estimate the nonequilibriumTc using the Allen-Dynes formula61"},
        {"id": "tc_220gpa", "lines": [420, 428], "quote": "Tc from 258 K at equilibrium to 320 K"},
        {"id": "tc_250gpa", "lines": [420, 428], "quote": "Tc rises from 237 K to 322 K yielding a"},
        {"id": "dos_scaling", "lines": [438, 465], "quote": "this DOS scaling approximates"},
        {"id": "low_pressure_unreliable", "lines": [547, 559], "quote": "direct simulations become unreliable"},
        {"id": "tc_150_200gpa", "lines": [575, 584], "quote": "the Tc rises from 249 K to 285 K for 150 GPa LaH10 and from 240 K to 301 K"},
        {"id": "dos_not_accurate", "lines": [580, 584], "quote": "should not be regarded as an accurate prediction"},
        {"id": "nonthermal_challenge", "lines": [692, 708], "quote": "achieving non-thermal Floquet states in experiments remains a signiﬁcant"},
        {"id": "finite_order_distribution", "lines": [692, 708], "quote": "electronic state distribution"},
        {"id": "strong_coupling_boundary", "lines": [709, 727], "quote": "c reaches 0.1ω Debye"},
        {"id": "extrapolation_boundary", "lines": [718, 727], "quote": "Extending this method to superconducting materials with either"},
    ]
    for anchor in anchors:
        start, end = anchor["lines"]
        excerpt = normalized(" ".join(source_lines[start - 1 : end]))
        assert normalized(anchor["quote"]) in excerpt, anchor["id"]
        anchor["role"] = "verbatim_whitespace_normalized_excerpt"

    estimates = [
        {"pressure_gpa": 220, "equilibrium_k": 258, "driven_k": 320, "reported_increase_percent": 25, "role": "direct_floquet_dfpt_allen_dynes_estimate", "accurate_prediction": False, "source_lines": [420, 436]},
        {"pressure_gpa": 250, "equilibrium_k": 237, "driven_k": 322, "reported_increase_percent": 35, "role": "direct_floquet_dfpt_allen_dynes_estimate", "accurate_prediction": False, "source_lines": [420, 436]},
        {"pressure_gpa": 150, "equilibrium_k": 249, "driven_k": 285, "reported_increase_percent": None, "role": "dos_scaling_lower_bound_claim_not_general_bound", "accurate_prediction": False, "source_lines": [547, 584]},
        {"pressure_gpa": 200, "equilibrium_k": 240, "driven_k": 301, "reported_increase_percent": None, "role": "dos_scaling_lower_bound_claim_not_general_bound", "accurate_prediction": False, "source_lines": [547, 584]},
    ]
    for row in estimates:
        row["recomputed_increase_percent"] = (row["driven_k"] - row["equilibrium_k"]) / row["equilibrium_k"] * 100
        row["experimental_confirmation"] = False

    data = {
        "schema": "floquet-evidence-boundary-v1",
        "date": "2026-11-11",
        "scope": "Check whether the original two-gap-resonance premise entails a driven critical-temperature increase, and identify the actual assumptions in Xie et al. This is not an experimental falsification or reproduction.",
        "sources": [
            {
                "id": "original_lean",
                "path": "toe-sylva-audit/papers/room_temp_sc/room_temp_sc_Formalization.lean",
                "sha256": hashlib.sha256(ORIGINAL.read_bytes()).hexdigest(),
                "modified": False,
            },
            {
                "id": "xie_2025",
                "path": "research/paper-direction-audit-2026-11-10/room-temp-methods/sources/xie-floquet-fulltext.txt",
                "sha256": hashlib.sha256(XIE.read_bytes()).hexdigest(),
                "doi": "10.1038/s41524-025-01725-z",
                "title": "Dynamical approach to realize room-temperature superconductivity in LaH10",
                "publication": "npj Computational Materials 11, 227 (2025)",
                "modified": False,
            },
        ],
        "source_anchors": anchors,
        "original_theorem": {
            "name": "floquet_enhanced_tc",
            "source_lines": [171, 185],
            "status": "proof_debt_not_a_physical_theorem",
            "bare_existential_trivially_inhabitable": True,
            "trivial_witness": "T_c_eq + 1",
            "trivial_witness_accepted_as_physics": False,
            "intended_physical_claim_follows_from_premise": False,
            "countermodel_is_physical_evidence": False,
            "missing_premises": [
                "Tc_as_a_function_of_drive_and_material",
                "positive_planck_constant",
                "pairing_and_distribution_response",
                "nonthermal_steady_state_domain",
                "pumping_heating_and_damage_domain",
                "estimator_validity_domain",
            ],
            "countermodel": {
                "scope": "stronger_material_response_relation_not_formalized_in_original",
                "delta": 1,
                "hbar": 1,
                "omega_drive": 2,
                "resonance_exact": True,
                "t_c_eq_k": 250,
                "t_c_f_k": 200,
                "enhancement": False,
                "interpretation": "A mathematical assignment satisfying resonance but not enhancement. It shows that a material-response relation is missing; it does not prove that nature suppresses superconductivity.",
            },
        },
        "xie_model_assumptions": {
            "photon_energy_mev": 400,
            "laser_wavelength_um": 3,
            "drive_regime": "off_resonant_lowest_order_floquet",
            "tc_estimator": "Allen-Dynes",
            "two_gap_resonance_used_to_derive_tc": False,
            "nonthermal_distribution_scope": "checked_finite_order_assumption_not_general_proof",
            "phonon_assumption": "equilibrium_energies_and_eigenmodes_retained",
            "source_scope": "the_checked_article_only_not_all_possible_floquet_mechanisms",
        },
        "xie_tc_estimates": estimates,
        "limitations": {
            "nonthermal_steady_state_experimental_challenge": "Explicitly acknowledged by the source; no generic steady-state existence theorem is supplied here.",
            "fixed_equilibrium_phonons": "Assumption tied to pulse duration and structural stability, not an unconditional driven-lattice calculation.",
            "finite_order_electronic_distribution": "Finite-order Fermi-sea-like distribution is an approximation; its overlap with real-time dynamics is not an exact self-consistent non-equilibrium solution.",
            "multireference_dft": "Kohn-Sham multi-reference limitations and perturbative Coulomb pseudopotential remain.",
            "strong_coupling_quantum_fluctuations": "The source describes an approximate Tc ~ 0.1 omega_Debye ~ 330 K caution for hydrides, not a sharp universal phase boundary.",
            "experimental_confirmation": "Not established by this article or this audit.",
            "independent_reproduction": "Not performed; this package audits evidence, not DFPT outputs.",
        },
        "other_materials": {
            "xie_checked_scope": ["YH10", "CeH9", "CaH6"],
            "all_above_room_temperature": False,
            "original_yh10_350_400_k_claim_supported_by_checked_xie_article": False,
            "qualification": "This does not prove that no other source supports a YH10 estimate. It requires a separate primary calculation and pressure/pump domain.",
        },
        "conclusion": {
            "resonance_enhancement": "not_derived",
            "resonance_enhancement_disproved_experimentally": False,
            "xie_material_estimates_experimentally_confirmed": False,
            "physics_proof_complete": False,
            "next_permitted_formal_step": "Define an explicit driven material-response model and its parameter domain before stating any comparison of driven and equilibrium Tc.",
            "next_empirical_step": "Obtain original Floquet-DFPT inputs, distribution and phonon corrections, then independently reproduce before proposing a material prediction.",
        },
        "build_validation": {
            "source_anchor_count": len(anchors),
            "all_source_anchors_checked": True,
            "original_sorry_line": 185,
            "original_source_modified": False,
        },
    }
    (ROOT / "evidence.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    report = """# Floquet 共振条件与临界温度：证据边界

## 结论

原 Lean 草案中的 `floquet_enhanced_tc` 仍是证明债务，**不是 Floquet 增强证明**。其结论是“存在一个实数大于 `T_c_eq`”，可以空泛地取 `T_c_eq + 1`；即使写成可编译证明，也没有建立驱动、材料响应与临界温度之间的关系。本包拒绝用这种方式把证明位填绿。

已核的 Xie 等论文走的是 **400 meV、3 μm、非共振、最低阶 Floquet** 路线，并使用 Floquet 稳态量配合 Allen–Dynes 公式估算 `Tc`。它没有从 `ω_drive ≈ 2Δ/ℏ` 推出增强。因此，现有证据**不能推出**原草案想表达的物理增强命题；这也不等于否定一切 Floquet 超导机制。

## 材料估算的角色

| 压力 | 平衡态估算 | 驱动态估算 | 方法与边界 |
|---:|---:|---:|---|
| 220 GPa | 258 K | 320 K | Floquet-DFPT + Allen–Dynes；论文报告约 25% 增幅 |
| 250 GPa | 237 K | 322 K | Floquet-DFPT + Allen–Dynes；论文报告约 35% 增幅 |
| 150 GPa | 249 K | 285 K | DOS-scaling 近似；作者称为下界估计，不是精确预测 |
| 200 GPa | 240 K | 301 K | DOS-scaling 近似；作者称为下界估计，不是精确预测 |

这里的“下界”是作者在已比较高阶直接计算与 DOS-scaling 的特定语境下的估计角色，不能自动升格为任意压力、任意泵浦、任意材料上的严格数学下界。DOS-scaling 还可高估耦合强度 `λ`，同时因未计 `ω_log` 上升而低估相应估算的 `Tc`。论文明确报告约 25% 和 35% 的估计增幅，但整数温度端点的比值约为 24.03% 和 35.86%，不能由这两个百分比直接作普通四舍五入精确复现；因此只保留为近似报告，不反推或篡改底层未取整数据。

## 逻辑反模型不是物理反证

在纯数学赋值 `ℏ = 1`、`Δ = 1`、`ω_drive = 2` 时，精确共振成立；若另设 `Tc_eq = 250 K`、`Tc_F = 200 K`，就没有增强。这个赋值只说明必须有独立的材料响应关系才能推出增强，**逻辑反模型不是物理反证**，更不能替代真实材料计算或实验。

## 仍未闭合的物理链条

1. 非热 Floquet 稳态的实现仍是论文明确承认的实验挑战。
2. 声子能量与本征模不变是脉冲时标和结构稳定条件下的近似，不是任意驱动下的结论。
3. 有限阶 Floquet 计算与类 Fermi 分布并未构成一般非平衡分布的严格解。
4. Kohn–Sham 多参考限制、微扰 Coulomb 赝势和强耦合量子涨落仍需处理。约 330 K 是论文针对氢化物给出的近似适用性警示，不是普适锐利相界。
5. Xie 检查的其他氢化物并不都超过室温；原文的 YH10 350–400 K 数字没有由本文直接支持，需要另找原始计算，不能沿用类比外推。
6. 本包没有原始 DFPT 输入、独立复算或实验数据；所有材料数值**未完成实验验证**。

## 后续准入条件

先定义含驱动参数、材料参数、分布和配对通道的显式 `Tc` 响应模型，并声明适用域，再讨论 `Tc_F > Tc_eq` 的可证命题。没有这些前提时保持 CLAIM／开放问题，不新增公理、证明位占位或空泛存在性“证明”。实验侧须补齐原始输入、声子和分布修正、热与损伤预算，再独立复算和验证。

## 核验

- `python research/floquet-evidence-boundary/build_evidence.py`
- `python research/floquet-evidence-boundary/test_floquet_evidence_boundary.py -v`
- `python research/floquet-evidence-boundary/verify_floquet_evidence_boundary.py -v`

源文件保持原样；具体哈希、原文行号、归一化逐字摘录和限制见 `evidence.json`。
"""
    (ROOT / "README.md").write_text(report, encoding="utf-8")
    print(f"source anchors checked: {len(anchors)}")
    print(f"original SHA-256: {data['sources'][0]['sha256']}")
    print(f"Xie text SHA-256: {data['sources'][1]['sha256']}")
    print("wrote evidence.json and README.md; no original source modified")


if __name__ == "__main__":
    main()
