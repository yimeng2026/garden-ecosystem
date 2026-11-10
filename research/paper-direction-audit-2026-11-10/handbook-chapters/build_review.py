"""Build the handbook pedagogy and necessity-claim evidence audit."""

import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyBboxPatch

from numeric_checks import mev_to_kelvin, tc, theta_threshold

AUDIT = Path(__file__).resolve().parent
EXPECTED_HASHES = {
    "handbook_intro": "bb67c6d7b57a2dad1f42eed1bd2729697e590c643953e05e19ca0a7016463d23",
    "handbook_theorem": "062b0011cc45b34ed8545a5890769ca71382608b09371641af5a51060c476e97",
    "physics_foundations": "93dd0cc19dc0b72c3103c607ded0a513837f664b3aaa872150e9bcb0a7d1c13e",
    "main_claims_review": "e9ac6ff0bc88f11b1c2c91ae61ce398a05fc077815803f48669b46536d6f2f45",
    "theory_review": "e6acb59a95f4dc159db2692e5db0a6ae40d640f8a8aef04ca1b69da80e3ed8c8",
    "data_governance_review": "e09aeb77dd254d061d980c306e6762c1ef21ad8a5e826be6a08226d581680aa8",
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
        "handbook_intro": root / "08-手册章节/01-第1-2章_超导入门与科普.md",
        "handbook_theorem": root / "08-手册章节/02-第3章_必然性定理.md",
        "physics_foundations": AUDIT / "sources/physics-foundations.md",
        "main_claims_review": AUDIT.parent / "main-claims/review.json",
        "theory_review": AUDIT.parent / "theory-breakthrough/review.json",
        "data_governance_review": AUDIT.parent / "data-governance/review.json",
    }
    display = {
        "handbook_intro": "toe-sylva-audit/papers/room_temp_sc/organized/08-手册章节/01-第1-2章_超导入门与科普.md",
        "handbook_theorem": "toe-sylva-audit/papers/room_temp_sc/organized/08-手册章节/02-第3章_必然性定理.md",
        "physics_foundations": "sources/physics-foundations.md",
        "main_claims_review": "main-claims/review.json",
        "theory_review": "theory-breakthrough/review.json",
        "data_governance_review": "data-governance/review.json",
    }
    sources = []
    for source_id, path in paths.items():
        actual = sha256(path)
        if actual != EXPECTED_HASHES[source_id]:
            raise ValueError(f"source hash changed: {source_id}: {actual}")
        sources.append({"id": source_id, "path": display[source_id], "sha256": actual, "read_only": True})
    formula4_value = tc(2.5, 0.15, 2100)
    example_value = tc(3.6, 0.12, 2100)
    return {
        "schema": "handbook-chapters-audit-v1",
        "date": "2026-11-10",
        "scope": "手册第 1–3 章；只审计，不修改原文，不重跑计算或实验。",
        "sources": sources,
        "source_lineage": {
            "research_program_count": 1,
            "decision": "两章属于同一研究纲领的入门教学与必然性叙事，不是两个独立新理论。",
        },
        "directions": [
            {
                "id": "pedagogical_physics",
                "role": "保留 BCS／Eliashberg 物理图像，修正类比、历史时间线和绝对化措辞",
                "closed": "BCS 相干配对、液氮时间线、H₃S 和 McMillan 极限角色已核清。",
                "unfinished": "其余历史和应用事实未逐项回源，教学类比仍需统一修订。",
                "next": "以正式定义校准类比，保留物理直觉但标注近似与适用范围。",
            },
            {
                "id": "conditional_model",
                "role": "把第 3 章重建为指定简化公式与参数域内的充分条件",
                "closed": "公式 4 的 259.594501 K 与正确示例 326.617108 K 已分开。",
                "unfinished": "原三条件、μ*、准二维和实际参数域的逻辑映射未闭合。",
                "next": "只陈述简化模型的充分条件，删除普遍物理必然性并补齐 f1/f2 和完整理论边界。",
            },
            {
                "id": "experimental_roles",
                "role": "分开 PNAS 预测、Song 预印本、Semenok 负向复现和直接 Meissner 待办",
                "closed": "298 K、直接 Meissner、独立复现和 P6/mmm 的角色已核清。",
                "unfinished": "独立正向复现、直接磁测量、前驱体和同位素验证未完成。",
                "next": "并列保存正负实验，按证据等级更新教学案例，不写完美验证。",
            },
            {
                "id": "unit_provenance",
                "role": "频率—温度换算、参数来源、作者身份、化学式和证据血缘治理",
                "closed": "210／150 meV 换算、Liu／Song 和 H₃S 问题已定位。",
                "unfinished": "Θ_D 与最大声子频率的定义、原始谱和输入参数来源未闭合。",
                "next": "每个参数绑定定义、单位、来源和原始输入，禁止同值异名混用。",
            },
        ],
        "evidence": {
            "formula4": {
                "lambda": 2.5,
                "mu_star": 0.15,
                "theta_d_k": 2100,
                "computed_tc_k": formula4_value,
                "claimed_tc_k": 326,
                "claim_supported": False,
            },
            "correct_example": {
                "lambda": 3.6,
                "mu_star": 0.12,
                "theta_d_k": 2100,
                "computed_tc_k": example_value,
                "claimed_tc_k": 326,
                "rounding_supported": True,
            },
            "threshold_lambda25": {
                "computed_theta_d_k": theta_threshold(2.5, 0.15),
                "claimed_theta_d_k": 2427,
                "arithmetic_supported": True,
            },
            "units": {
                "omega_210_mev_k": mev_to_kelvin(210),
                "omega_150_mev_k": mev_to_kelvin(150),
                "theta_d_2100_is_omega_max_210_mev": False,
                "alternative_effective_theta_requires_source": True,
            },
            "conditions": {
                "original_lambda": ">2",
                "theorem_lambda": ">=2.5",
                "original_phonon_mev": 150,
                "theorem_theta_d_k": 1800,
                "original_quasi_2d": True,
                "theorem_mu_star_max": 0.15,
                "sets_equivalent": False,
                "quasi_2d_used_in_proof": False,
                "simplified_model_sufficient_condition": True,
                "physical_necessity_proven": False,
            },
            "experiment": {
                "song_onset_max_k": 298,
                "direct_meissner_completed": False,
                "independent_positive_replication": False,
                "semenok_negative_replication_exists": True,
                "p6mmm_automatically_quasi_2d": False,
                "liu_and_song_same_author_list": False,
            },
            "intro": {
                "year_1986_tc_k": 35,
                "year_1987_tc_k": 93,
                "liquid_nitrogen_k": 77,
                "correct_chemical_formula": "H₃S",
                "mcmillan_universal_cap": False,
                "cooper_pairs_simple_boson_gas": False,
            },
        },
        "corrections": [
            {"id": "formula4", "severity": "P0", "finding": "公式 4 在 λ=2.5、μ*=0.15、Θ_D=2100 K 时写成 326 K。", "action": "改为约 259.594501 K；另列 λ=3.6、μ*=0.12 的约 326.617108 K 示例，禁止混用参数。"},
            {"id": "condition_sets", "severity": "P0", "finding": "原三条件与定理条件不同，准二维未进入证明，μ* 后补。", "action": "改为简化模型参数充分条件，不称普遍物理必然性。"},
            {"id": "song_298", "severity": "P0", "finding": "298 K 被写成超过 300 K 并完美验证，直接 Meissner 与负向复现被省略。", "action": "分开预测、作者预印本和负向复现；直接 Meissner 与独立正向复现列待办。"},
            {"id": "frequency_units", "severity": "P1", "finding": "210 meV 与 Θ_D=2100 K 的换算不闭合。", "action": "若为同一最大频率，应为约 2436.948806 K；若 Θ_D 是另一有效量，单列定义和来源。"},
            {"id": "bcs_pedagogy", "severity": "P1", "finding": "库珀对被简单等同独立玻色子，McMillan 极限被绝对化。", "action": "使用相干配对组态和特定模型／历史经验背景，不写统一数学上限。"},
            {"id": "liquid_nitrogen_timeline", "severity": "P1", "finding": "1986 年 35 K 被写成突破液氮温区。", "action": "改为 1986 年铜基高温超导，1987 年 YBCO 93 K 才超过 77 K。"},
            {"id": "chemical_formula", "severity": "P1", "finding": "硫化氢写成 H₂S。", "action": "统一为 H₃S，保留其高压实验角色。"},
            {"id": "author_structure", "severity": "P1", "finding": "Liu 与 Song 署名不一致，P6/mmm 自动等同准二维。", "action": "统一作者与来源；准二维需各向异性证据，不能由空间群直接推出。"},
        ],
        "open_boundaries": {
            "formula4_verified": False,
            "three_conditions_proven": False,
            "theta_d_source_closed": False,
            "experimental_necessity_proven": False,
            "all_intro_facts_checked": False,
            "full_repository_audit": False,
        },
        "figure": {
            "svg": "handbook-evidence.svg",
            "png": "handbook-evidence.png",
            "labels": ["259.594501", "326.617108", "298 K", "准二维", "H₃S"],
            "caption": "图 1　参数复算与证据角色：正确示例不等于普遍证明",
            "insert_after": "数值复算表",
            "insert_before": "结果解释",
            "verification_percentage_plotted": False,
        },
        "verification_scope": {
            "source_documents_modified": False,
            "new_dft_or_experiment": False,
            "theta_d_original_spectrum_resolved": False,
            "all_intro_facts_checked": False,
            "full_repository_audit": False,
        },
    }


def box(axis, y, text, face, edge="#455A64", height=0.17, size=11):
    patch = FancyBboxPatch((0.08, y), 0.84, height, boxstyle="round,pad=0.012,rounding_size=0.018",
                           transform=axis.transAxes, facecolor=face, edgecolor=edge, linewidth=1.3)
    axis.add_patch(patch)
    axis.text(0.50, y + height / 2, text, transform=axis.transAxes, ha="center", va="center",
              fontsize=size, color="#263238", linespacing=1.45)


def build_figure(data):
    plt.rcParams["font.family"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
    fig, (left, right) = plt.subplots(1, 2, figsize=(12.8, 7.2), gridspec_kw={"width_ratios": [1.0, 1.1]})
    fig.patch.set_facecolor("#FAFBFC")
    bad = data["evidence"]["formula4"]
    good = data["evidence"]["correct_example"]
    x = np.arange(2)
    computed = [bad["computed_tc_k"], good["computed_tc_k"]]
    claimed = [bad["claimed_tc_k"], good["claimed_tc_k"]]
    width = 0.32
    left.bar(x - width / 2, computed, width, label="独立复算", color="#3E7772")
    left.bar(x + width / 2, claimed, width, label="文中值", color="#8C7651")
    for index, (actual, printed) in enumerate(zip(computed, claimed)):
        left.text(index - width / 2, actual + 7, f"{actual:.6f}", ha="center", fontsize=10)
        left.text(index + width / 2, printed + 7, f"{printed:g}", ha="center", fontsize=10)
    left.axhline(300, color="#A65D4E", linestyle="--", linewidth=1.3)
    left.text(1.42, 305, "300 K", color="#A65D4E", fontsize=10)
    left.set_xticks(x, ["公式 4 参数\nλ=2.5；μ*=0.15", "正确示例参数\nλ=3.6；μ*=0.12"])
    left.set_ylim(0, 370)
    left.set_ylabel("Tc（K）")
    left.set_title("同一公式，不同参数：结果不能混用", fontsize=15, fontweight="bold")
    left.legend(frameon=False, loc="upper left")
    left.grid(axis="y", alpha=0.18)
    left.spines[["top", "right"]].set_visible(False)
    left.text(0.5, -0.19, "公式 4 应约为 259.594501 K；正确示例约为 326.617108 K。",
              transform=left.transAxes, ha="center", fontsize=10.5, color="#8C4A3E")

    right.set_axis_off()
    right.set_xlim(0, 1)
    right.set_ylim(0, 1)
    right.set_title("条件与证据并不重合", fontsize=15, fontweight="bold", color="#263238", pad=18)
    box(right, 0.73, "原“三条件”\nλ>2；准二维；ℏω>150 meV", "#E8F0F2")
    box(right, 0.45, "定理实际条件\nλ≥2.5；Θ_D≥1800 K；μ*≤0.15\n准二维没有进入证明", "#F3EEE4")
    box(right, 0.16, "实验角色\nSong 298 K < 300 K；直接 Meissner 未确立\nSemenok 负向复现不能省略", "#F5E8E4", edge="#A65D4E")
    right.text(0.50, 0.045, "只能保留为简化模型的参数充分条件，不能称为普遍物理必然性。",
               transform=right.transAxes, ha="center", fontsize=10.5, color="#546E7A")
    fig.suptitle("参数复算与证据角色：正确示例不等于普遍证明", fontsize=20, fontweight="bold", color="#263238", y=0.985)
    fig.text(0.5, 0.012, "只显示数值与证据边界，不构造验证百分比。", ha="center", fontsize=10, color="#607D8B")
    fig.subplots_adjust(left=0.07, right=0.98, top=0.84, bottom=0.18, wspace=0.24)
    fig.savefig(AUDIT / data["figure"]["svg"], metadata={"Date": None})
    fig.savefig(AUDIT / data["figure"]["png"], dpi=220, metadata={"Software": None})
    plt.close(fig)


def build_markdown(data):
    bad = data["evidence"]["formula4"]
    good = data["evidence"]["correct_example"]
    threshold = data["evidence"]["threshold_lambda25"]
    units = data["evidence"]["units"]
    conditions = data["evidence"]["conditions"]
    experiment = data["evidence"]["experiment"]
    intro = data["evidence"]["intro"]
    lines = [
        "# 手册第 1–3 章：教学边界、参数复算与未竟工作审计",
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
        "## 二、公式 4 与正确示例：同一公式不能混用参数",
        "",
        "| 参数组 | 文中值（K） | 独立复算（K） | 裁决 |",
        "|:--|--:|--:|:--|",
        f"| 公式 4：λ=2.5、μ*=0.15、Θ_D=2100 K | {bad['claimed_tc_k']} | {bad['computed_tc_k']:.12f} | 文中值错误 |",
        f"| 正确示例：λ=3.6、μ*=0.12、Θ_D=2100 K | {good['claimed_tc_k']} | {good['computed_tc_k']:.12f} | 近似值可保留 |",
        f"| λ=2.5、μ*=0.15 的 Θ_D 阈值 | {threshold['claimed_theta_d_k']} | {threshold['computed_theta_d_k']:.12f} | 约 2427 K 的算术正确 |",
        "",
        "![图 1：参数复算与证据角色](handbook-evidence.svg)",
        "",
        "**图件插入顺序：图 1 位于数值复算表之后、结果解释之前。** 图中没有验证百分比。",
        "",
        "这些结果只适用于指定简化公式和参数域。原“三条件”与定理条件并不等价，准二维也没有进入证明，因此不能称为普遍物理必然性。",
        "",
        "## 三、实验角色与频率单位",
        "",
        "| 项目 | 已核实结果 | 证据边界 |",
        "|:--|:--|:--|",
        f"| Song | onset 上限 {experiment['song_onset_max_k']} K，低于 300 K | 直接 Meissner、独立正向复现未确立；Semenok 负向复现不能省略 |",
        f"| 210 meV | {units['omega_210_mev_k']:.6f} K | 若与 Θ_D 是同一最大频率，不是 2100 K；若 Θ_D 是另一有效量，单列定义和来源 |",
        f"| 150 meV | {units['omega_150_mev_k']:.6f} K | 不与项目 300 K 必然性阈值混用 |",
        "| 作者与结构 | Liu 与 Song 署名不统一；P6/mmm 不自动等于准二维 | 统一来源，准二维需各向异性证据 |",
        "",
        "## 四、入门教学与分档勘误",
        "",
        f"1986 年镧钡铜氧为 {intro['year_1986_tc_k']} K，仍低于液氮 {intro['liquid_nitrogen_k']} K；1987 年 YBCO 为 {intro['year_1987_tc_k']} K 才超过液氮。H₂S 应统一为 {intro['correct_chemical_formula']}。",
        "",
        "BCS 是由正常态和虚拟配对组态构成的相干基态，不是简单的独立玻色子气体。McMillan 的“最大 Tc”属于特定模型与历史经验背景，不是所有材料统一的 30–40 K 数学上限。",
        "",
        "| 级别 | 已观察问题 | 建议动作 |",
        "|:--|:--|:--|",
    ]
    for row in data["corrections"]:
        lines.append(f"| {row['severity']} | {row['finding']} | {row['action']} |")
    lines += [
        "",
        "可发展的方向不是删除教学，而是把类比、近似、公式和实验各归其位：入门章提供物理直觉，条件章只证明简化模型内的结论，实验章同时呈现正负证据。",
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
        "本批使用六项冻结来源、原始理论文献和独立数值复算。命令与退出码见 `run.log`；Word 逐页结果见 `word-qa/report.json`。其余入门事实未全审。",
        "",
        "本批没有重跑计算或实验，没有闭合 Θ_D 原始谱，没有修改两章原文。**全库审计尚未完成。**",
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
        "formula4": data["evidence"]["formula4"]["computed_tc_k"],
        "correct_example": data["evidence"]["correct_example"]["computed_tc_k"],
        "threshold": data["evidence"]["threshold_lambda25"]["computed_theta_d_k"],
        "omega_210": data["evidence"]["units"]["omega_210_mev_k"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
