"""Build the validation/material-prediction evidence audit from frozen sources."""

import hashlib
import importlib.util
import json
from pathlib import Path

AUDIT = Path(__file__).resolve().parent
EXPECTED_HASHES = {
    "validation_report": "51a4709522000dca521dcecd071f20766763821eca94cb9e279335ea91f47e90",
    "material_predictions": "050b52aa56bb633fd1db95e198f9804085de26080f4b18f135f44e3c8ef326ef",
    "numeric_spotcheck": "c11de34cb4f238e9c837effb735ebc9629921ea9494af28d474d75fddcee95d9",
    "primary_excerpts": "62cf61470cc7be0d17ee5e53a7e9f01b8cf8013c009698526aeafdcf5c281528",
}
DOC_PATHS = {
    "validation_report": "organized/05-实验验证/01-实验验证.md",
    "material_predictions": "organized/04-材料预测/01-材料预测.md",
}
URLS = {
    "grockowiak": "https://www.frontiersin.org/journals/electronic-materials/articles/10.3389/femat.2022.837651/full",
    "lanio2": "https://pmc.ncbi.nlm.nih.gov/articles/PMC8856608/",
    "cl_doping": "https://arxiv.org/html/1804.08224v3",
}


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def find_source_root():
    for parent in AUDIT.parents:
        candidate = parent / "toe-sylva-audit/papers/room_temp_sc"
        if candidate.is_dir():
            return candidate
    raise FileNotFoundError("toe-sylva-audit room_temp_sc root")


def load_spotcheck():
    path = AUDIT / "numeric_spotcheck.py"
    spec = importlib.util.spec_from_file_location("validation_numeric_spotcheck", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def build_data():
    root = find_source_root()
    paths = {key: root / relative for key, relative in DOC_PATHS.items()}
    paths.update({
        "numeric_spotcheck": AUDIT / "numeric_spotcheck.py",
        "primary_excerpts": AUDIT / "sources/primary-source-excerpts.md",
    })
    display = {key: f"toe-sylva-audit/papers/room_temp_sc/{DOC_PATHS[key]}" for key in DOC_PATHS}
    display.update({
        "numeric_spotcheck": "validation-materials/numeric_spotcheck.py",
        "primary_excerpts": "validation-materials/sources/primary-source-excerpts.md",
    })
    sources = []
    for source_id, path in paths.items():
        actual = sha256(path)
        expected = EXPECTED_HASHES[source_id]
        if actual != expected:
            raise ValueError(f"source hash changed: {source_id}: {actual} != {expected}")
        sources.append({"id": source_id, "path": display[source_id], "sha256": actual, "read_only": True})

    numeric = load_spotcheck()
    h3s_value, h3s_exponent = numeric.simplified_tc(1200.0, 2.0, 0.13)
    hscl_value, hscl_exponent = numeric.simplified_tc(1500.0, 2.5, 0.12)
    directions = [
        {
            "id": "formula_evidence",
            "role": "文内公式、参数、单位和修正因子的可复核证据链",
            "closed": "两组表内参数与结果不一致已由独立脚本复算。",
            "unfinished": "f1/f2、ω2/ωlog、参数来源、压力和掺杂结构未闭合。",
            "next": "补齐推导与原始输入输出，不以复算值替代预测。",
        },
        {
            "id": "sample_doping",
            "role": "化学式、掺杂范围与样品证据角色审计",
            "closed": "未掺杂 LaNiO₂ 绝缘与 Ca 掺杂超导穹顶已分清。",
            "unfinished": "不同掺杂、应变、薄膜厚度和输运证据仍需逐项对应。",
            "next": "每条材料结论绑定化学式、掺杂、形态和原始图号。",
        },
        {
            "id": "higher_order_hydride",
            "role": "高阶／取代氢化物的实验争议与独立验证",
            "closed": "556 K 原文存在，但其不可逆高阶角色与二元 LaH₁₀ 不同。",
            "unfinished": "独立复现、成分相确定、Meissner、热力学平衡和原始数据。",
            "next": "把高阶实验宣称与二元材料常规验证分轨。",
        },
        {
            "id": "validation_governance",
            "role": "验证评分、研发排序与证据治理",
            "closed": "百分比和星级缺少可复算规则，已降为治理标签。",
            "unfinished": "评分卡、权重、样本集、误差模型和独立复核未建立。",
            "next": "若保留评分，公开可复算规则与不确定性。",
        },
    ]
    corrections = [
        {
            "id": "formula_chain",
            "severity": "P0",
            "finding": "表内参数—公式—Tc 结果不一致，且 Cl 第一性原理方向与 320 K 推断相反。",
            "action": "标为推导链未闭合，补齐修正因子和参数来源，禁止直接替换为复算值。",
        },
        {
            "id": "lanio2_sample",
            "severity": "P0",
            "finding": "未掺杂 LaNiO₂ 被写成 20–40 K 已验证超导体。",
            "action": "改为未掺杂薄膜绝缘，超导只用于明确掺杂的 La1−xCaxNiO2 范围。",
        },
        {
            "id": "grockowiak_role",
            "severity": "P0",
            "finding": "556 K 被并入二元 LaH₁₀ 的常规验证叙事。",
            "action": "保留真实论文，改为不可逆高阶／取代氢化物的待独立验证证据。",
        },
        {
            "id": "scoring_rubric",
            "severity": "P1",
            "finding": "验证百分比和星级没有公开计算规则。",
            "action": "删除定量验证口吻或改为主观治理标签，建立评分卡后再量化。",
        },
    ]
    return {
        "schema": "validation-materials-audit-v1",
        "date": "2026-11-10",
        "scope": "两份实验验证与材料预测文档；只审计，不修改原文，不新增材料预测。",
        "sources": sources,
        "source_lineage": {
            "research_program_count": 1,
            "decision": "两份文档属于同一研究纲领的验证与预测环节，不是两个独立新理论。",
        },
        "directions": directions,
        "corrections": corrections,
        "evidence": {
            "formula_spotcheck": {
                "h3s": {
                    "omega_log_k": 1200.0,
                    "lambda": 2.0,
                    "mu_star": 0.13,
                    "claimed_tc_k": 203.0,
                    "computed_tc_k": h3s_value,
                    "exponent": h3s_exponent,
                    "is_first_principles_result": False,
                },
                "h_s_cl": {
                    "omega_log_k": 1500.0,
                    "lambda": 2.5,
                    "mu_star": 0.12,
                    "claimed_tc_k": 320.0,
                    "computed_tc_k": hscl_value,
                    "exponent": hscl_exponent,
                    "is_first_principles_result": False,
                },
                "script": "numeric_spotcheck.py",
            },
            "lanio2": {
                "source_url": URLS["lanio2"],
                "superconducting_dome": [0.15, 0.3],
                "undoped_insulating": True,
                "undoped_tc_20_40_verified": False,
                "dopant": "Ca",
                "scope": "La1−xCaxNiO2 thin films",
            },
            "grockowiak": {
                "source_url": URLS["grockowiak"],
                "doi": "10.3389/femat.2022.837651",
                "initial_tc_k": 294,
                "maximum_onset_tc_k": 556,
                "irreversible_higher_order": True,
                "meissner_completed": False,
                "reliable_high_temperature_ht_diagram": False,
                "binary_lah10_routine_validation": False,
                "nonzero_resistance_background": True,
            },
            "cl_doping": {
                "source_url": URLS["cl_doping"],
                "results": [
                    {"cl_fraction": 0.0625, "tc_k": 161, "pressure_gpa": 200},
                    {"cl_fraction": 0.125, "tc_k": 136, "pressure_gpa": 200},
                ],
                "lowers_stabilization_pressure": True,
                "supports_320k_prediction": False,
            },
            "scoring": {
                "rubric_available": False,
                "role": "无复算规则的研究治理标签，不是定量科学验证结果",
            },
        },
        "open_boundaries": {
            "global_fit": False,
            "first_principles_recomputed": False,
            "prediction_replaced": False,
            "experimental_verification": False,
            "full_document_source_audit": False,
            "full_repository_audit": False,
        },
        "figure": {
            "svg": "formula-spotcheck.svg",
            "png": "formula-spotcheck.png",
            "x_labels": ["H3S", "H-S-Cl"],
            "caption": "图 1　文中值与文中公式复算值：不是材料预测",
            "insert_after": "公式复算表",
            "insert_before": "结果解释",
        },
        "verification_scope": {
            "source_documents_modified": False,
            "new_material_prediction": False,
            "new_experiment_or_independent_replication": False,
            "new_first_principles_calculation": False,
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
    plt.rcParams["svg.hashsalt"] = "validation-materials-spotcheck-v1"
    rows = data["evidence"]["formula_spotcheck"]
    labels = data["figure"]["x_labels"]
    claimed = [rows["h3s"]["claimed_tc_k"], rows["h_s_cl"]["claimed_tc_k"]]
    computed = [rows["h3s"]["computed_tc_k"], rows["h_s_cl"]["computed_tc_k"]]
    x = [0, 1]
    width = 0.34
    fig, ax = plt.subplots(figsize=(9.4, 5.2), dpi=180)
    bars1 = ax.bar([v - width / 2 for v in x], claimed, width, label="文中值", color="#8c6d3f")
    bars2 = ax.bar([v + width / 2 for v in x], computed, width, label="文中公式复算值", color="#397a76")
    for bars in (bars1, bars2):
        for bar in bars:
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 7, f"{bar.get_height():.2f}", ha="center", fontsize=10)
    ax.set_xticks(x, labels)
    ax.set_ylabel("Tc（K）")
    ax.set_ylim(0, 365)
    ax.set_title("文中值与文中公式复算值：不是材料预测", fontsize=15, pad=16)
    ax.legend(frameon=False, loc="upper left")
    ax.grid(axis="y", alpha=0.2)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(AUDIT / "formula-spotcheck.svg", metadata={"Date": None})
    fig.savefig(AUDIT / "formula-spotcheck.png", dpi=220, metadata={"Software": "validation-materials-audit"})
    plt.close(fig)


def build_markdown(data):
    f = data["evidence"]["formula_spotcheck"]
    l = data["evidence"]["lanio2"]
    g = data["evidence"]["grockowiak"]
    c = data["evidence"]["cl_doping"]
    lines = [
        "# 实验验证与材料预测：证据角色、公式链与未竟工作审计",
        "",
        "> 日期：2026-11-10。只审计，不修改原文，不新增材料预测，不把文内公式复算称为第一性原理结果。",
        "",
        "## 一、血缘裁决与四个问题族",
        "",
        "两份文档属于同一研究纲领的验证与预测环节，不是两个新理论。审计分为公式链、样品与掺杂、高阶氢化物、验证治理四个方法问题族。",
        "",
        "| 来源 ID | 只读路径 | SHA-256 |",
        "|:--|:--|:--|",
    ]
    for row in data["sources"]:
        lines.append(f"| `{row['id']}` | `{row['path']}` | `{row['sha256']}` |")
    lines += [
        "",
        "| 问题族 | 已闭合的局部审计 | 未竟工作与下一步 |",
        "|:--|:--|:--|",
    ]
    for row in data["directions"]:
        lines.append(f"| `{row['id']}`：{row['role']} | {row['closed']} | {row['unfinished']}**下一步：**{row['next']} |")
    lines += [
        "",
        "## 二、公式链：文中值与文中公式复算值",
        "",
        "文中简化公式为：",
        "",
        "$$T_c=\\frac{\\omega_{\\log}}{1.2}\\exp(E),\\qquad E=-\\frac{1.04(1+\\lambda)}{\\lambda-\\mu^*(1+0.62\\lambda)}.$$",
        "",
        "| 条目 | ωlog（K） | λ | μ* | 文中 Tc（K） | 文中公式复算（K） |",
        "|:--|--:|--:|--:|--:|--:|",
        f"| H₃S | {f['h3s']['omega_log_k']:g} | {f['h3s']['lambda']:g} | {f['h3s']['mu_star']:g} | {f['h3s']['claimed_tc_k']:g} | {f['h3s']['computed_tc_k']:.15f} |",
        f"| H-S-Cl | {f['h_s_cl']['omega_log_k']:g} | {f['h_s_cl']['lambda']:g} | {f['h_s_cl']['mu_star']:g} | {f['h_s_cl']['claimed_tc_k']:g} | {f['h_s_cl']['computed_tc_k']:.15f} |",
        "",
        "![图 1：文中值与文中公式复算值对照](formula-spotcheck.svg)",
        "",
        "**图件插入顺序：图 1 位于公式复算表之后、结果解释之前。** 图 1 是文内算术检查，不是材料预测图。",
        "",
        "复算只证明“参数—公式—结果不一致”，不能替代 Allen–Dynes 修正、Eliashberg 求解或第一性原理计算。必须补齐 f1/f2、ω2/ωlog、参数来源、压力、掺杂结构和原始输入输出。",
        "",
        f"独立第一性原理研究还给出：200 GPa 下 6.25% Cl→{c['results'][0]['tc_k']} K、12.5% Cl→{c['results'][1]['tc_k']} K。Cl 掺杂削弱超导但降低稳定压力，与 20% Cl→320 K 的提升推断不相容。[原始来源]({c['source_url']})。",
        "",
        "## 三、LaNiO₂：未掺杂薄膜绝缘，掺杂后才讨论超导",
        "",
        f"原文摘要明确：未掺杂和低掺杂 La1−xCaxNiO2 薄膜从 300 K 到 2 K 均绝缘，超导穹顶位于 `{l['superconducting_dome'][0]} < x < {l['superconducting_dome'][1]}`。因此**未掺杂薄膜绝缘**，不能把 LaNiO₂ 写成 20–40 K 已验证超导体。[PMC 原始全文]({l['source_url']})。",
        "",
        "后续每个材料结论必须绑定化学式、掺杂元素、掺杂范围、薄膜形态、输运证据和原始图号；不能将掺杂样品的结论继承给未掺杂母体。",
        "",
        "## 四、556 K：真实论文，但不是二元 LaH₁₀ 的常规验证",
        "",
        f"Grockowiak 等原文报告初始 {g['initial_tc_k']} K，后续热循环使 onset 不可逆达到 {g['maximum_onset_tc_k']} K。原文描述扭曲 LaH₁₀ 骨架及取代形成高阶化合物，并明确缺少 Meissner 和可靠高温 H–T 相图，还存在非零电阻和混合相。[Frontiers 原始全文]({g['source_url']})。",
        "",
        "因此这篇论文不能被删除或称为虚构，但也不能并入二元 LaH₁₀ 的常规验证百分比。后续需要独立复现、成分与相确定、直接磁测量、热力学平衡和原始样品路径核对。",
        "",
        "## 五、验证百分比与星级：治理标签，不是定量结果",
        "",
        data["evidence"]["scoring"]["role"] + "。92%、88%、45%、9.5/10 和星级没有公开指标定义、权重、样本集、误差模型或复算公式。若保留，只能标为主观研究治理标签；建立公开评分卡后才可以量化。",
        "",
        "## 六、分档勘误与未竟工作",
        "",
        "| 级别 | 已观察问题 | 建议动作 |",
        "|:--|:--|:--|",
    ]
    for row in data["corrections"]:
        lines.append(f"| {row['severity']} | {row['finding']} | {row['action']} |")
    lines += [
        "",
        "真正的未竟工作不是再写一组更高 Tc，而是建立原始输入、参数、修正因子、样品身份、独立复现和可复算评分卡之间的闭环。",
        "",
        "## 七、验证范围",
        "",
        "本批使用冻结哈希、原始出版商/PMC/arXiv 来源和独立公式复算。命令、退出码见 `run.log`；Word 逐页结果见 `word-qa/report.json`。",
        "",
        "本批没有重跑第一性原理、没有替换材料预测、没有新做实验或独立复现、没有修改两份原文。**全库审计尚未完成。**",
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
        "h3s_computed": data["evidence"]["formula_spotcheck"]["h3s"]["computed_tc_k"],
        "h_s_cl_computed": data["evidence"]["formula_spotcheck"]["h_s_cl"]["computed_tc_k"],
        "lanio2_dome": data["evidence"]["lanio2"]["superconducting_dome"],
        "grockowiak_onset": data["evidence"]["grockowiak"]["maximum_onset_tc_k"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
