"""Build the isotope/pressure/multilayer-DFT evidence audit from frozen sources."""

import csv
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from numeric_checks import isotope_alpha, slope

AUDIT = Path(__file__).resolve().parent
SOURCES = AUDIT / "sources"
EXPECTED_HASHES = {
    "isotope_pressure": "6199a3f71c53ffe6dfe9505f942d713cdb8b8c8da87d35913898163c04366c07",
    "multilayer_dft": "ef31a1048fe415dfff433effc7fd7caefc4b124b320b104eb5e595e6d0752c5c",
    "kruglov_pdf": "25632b30de626a14d2607f9c4ae1c0c57e78b4af2e0723985a6558e00c1555a4",
    "isotope_pdf": "b5c69550005f7b4e926b12a60078a649d9939cbf6af51e07f42eec4063cfb6a6",
    "jarvis_pdf": "de1d282d5924f1a695e47a52f4e6bb8d696aea3e423ae894ca165452b47a03ab",
    "nickelate_search": "c82c8d735270ac6a154682dfcac6507e3d59224520fd15c5478be93b9e371fa4",
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
        "isotope_pressure": root / "17-资料收集-同位素效应与压力导数.md",
        "multilayer_dft": root / "19-资料收集-多层结构DFT参数.md",
        "kruglov_pdf": SOURCES / "kruglov-1810.01113.pdf",
        "isotope_pdf": SOURCES / "isotope-1912.09663.pdf",
        "jarvis_pdf": SOURCES / "jarvis-2312.12694.pdf",
        "nickelate_search": SOURCES / "nickelate-dome-scholar.csv",
    }
    display = {
        "isotope_pressure": "toe-sylva-audit/papers/room_temp_sc/organized/17-资料收集-同位素效应与压力导数.md",
        "multilayer_dft": "toe-sylva-audit/papers/room_temp_sc/organized/19-资料收集-多层结构DFT参数.md",
        "kruglov_pdf": "sources/kruglov-1810.01113.pdf",
        "isotope_pdf": "sources/isotope-1912.09663.pdf",
        "jarvis_pdf": "sources/jarvis-2312.12694.pdf",
        "nickelate_search": "sources/nickelate-dome-scholar.csv",
    }
    sources = []
    for source_id, path in paths.items():
        actual = sha256(path)
        if actual != EXPECTED_HASHES[source_id]:
            raise ValueError(f"source hash changed: {source_id}: {actual}")
        sources.append({"id": source_id, "path": display[source_id], "sha256": actual, "read_only": True})

    with paths["nickelate_search"].open(encoding="utf-8-sig", newline="") as handle:
        nickelate_rows = list(csv.DictReader(handle))
    exact_support = []
    for row in nickelate_rows:
        text = f"{row.get('title', '')} {row.get('abstract', '')}".lower()
        if "ndnio2" in text and "ktao3" in text and "superconduct" in text and "4-8" in text:
            exact_support.append(row.get("title", ""))
    if len(nickelate_rows) != 10 or exact_support:
        raise ValueError("nickelate search scope changed; review before generating")

    pressure_specs = [
        (170, 259, "Eliashberg", 200, 271, "SCDFT"),
        (200, 271, "SCDFT", 210, 249, "Eliashberg"),
        (210, 249, "Eliashberg", 250, 246, "Eliashberg"),
    ]
    pressure_rows = [
        {
            "pressure_interval_gpa": [p1, p2],
            "tc_interval_k": [t1, t2],
            "methods": [m1, m2],
            "slope": slope(p1, t1, p2, t2),
            "arithmetic_matches": True,
            "crosses_method_boundary": m1 != m2,
        }
        for p1, t1, m1, p2, t2, m2 in pressure_specs
    ]
    data = {
        "schema": "isotope-dft-audit-v1",
        "date": "2026-11-10",
        "scope": "同位素压力与多层 DFT 两份资料文档；只审计，不重跑计算或实验。",
        "sources": sources,
        "source_lineage": {
            "research_program_count": 1,
            "decision": "两份文档属于同一研究纲领的实验参数与计算方法资料层，不是两个独立新理论。",
        },
        "directions": [
            {
                "id": "isotope_lineage",
                "role": "同位素公式、温度对、压力、样品与来源的一一绑定",
                "closed": "标准分式和三组表内复算已完成，LaH10 的温度对错配已定位。",
                "unfinished": "不同样品、非谐修正、结构相和原始测量点仍需统一血缘。",
                "next": "每个 α 绑定同压力 H/D 温度、结构、样品和原始图号，禁止跨来源拼接。",
            },
            {
                "id": "method_aware_pressure",
                "role": "Eliashberg、SCDFT 与实验曲线分轨",
                "closed": "三段斜率算术正确，前两段跨方法及整组非纯实验角色已分清。",
                "unfinished": "同一方法的完整压力曲线、实验点、相边界和不确定度未闭合。",
                "next": "分别输出 Eliashberg、SCDFT 和实验 Tc(P)，仅在方法一致时求导。",
            },
            {
                "id": "reproducible_dft",
                "role": "以倒空间间距、赝势和收敛日志为核心的多层计算输入契约",
                "closed": "大超胞 k 点规则和通用参数保证的边界已定位。",
                "unfinished": "六层结构、化学式、界面、赝势、k/q、截断能、声子和收敛日志均缺失。",
                "next": "先定义最小结构并做收敛切片，再讨论多层材料预测。",
            },
            {
                "id": "ml_benchmark_governance",
                "role": "既有／新增数据集、训练／推理成本、误差和外部测试的基准治理",
                "closed": "JARVIS 两类数据角色已确认，1000 倍加速缺乏同口径基准。",
                "unfinished": "推理成本、硬件、任务定义、误差分布、外部压力和材料测试未建立。",
                "next": "发布固定划分和端到端成本表，比较 DFT、训练、推理与失败案例。",
            },
        ],
        "evidence": {
            "isotope": {
                "printed_lah10": {"tc_h": 240, "tc_d": 168, "pressure_gpa": 170, "alpha": isotope_alpha(240, 168), "claimed_alpha": 0.46},
                "durajski_lah10": {"tc_h": 249, "tc_d": 180, "pressure_gpa": 150, "alpha": isotope_alpha(249, 180), "reported_alpha": 0.46},
                "h3s": {"tc_h": 203, "tc_d": 155, "pressure_gpa": 155, "alpha": isotope_alpha(203, 155), "claimed_range": [0.3, 0.6]},
                "mechanism_uniquely_proven": False,
                "formula": "α = -(ln(TcD)-ln(TcH))/(ln(MD)-ln(MH))",
            },
            "pressure": {
                "rows": pressure_rows,
                "mixed_method_curve": any(row["crosses_method_boundary"] for row in pressure_rows),
                "experimental_curve_established": False,
                "source": "Kruglov Table 1; 271 K starred as SCDFT, other tabulated points Eliashberg",
            },
            "bibliography": {
                "kruglov_article": "024508",
                "printed_article": "224508",
                "doi": "10.1103/PhysRevB.101.024508",
                "url": "https://journals.aps.org/prb/abstract/10.1103/PhysRevB.101.024508",
            },
            "jarvis": {
                "arxiv": "2312.12694",
                "url": "https://arxiv.org/abs/2312.12694",
                "previous_zero_pressure_bulk": 1000,
                "previous_zero_pressure_2d": 150,
                "new_hydride_count_label": "over 900",
                "new_pressure_range_gpa": [0, 500],
                "stable_candidates": 122,
                "dft_core_hours": 11500,
                "training_gpu_hours": [4, 7],
                "previous_datasets_confirmed": True,
                "speedup_1000_directly_supported": False,
                "prediction_examples": {"H3S_tc_k_at_200_gpa": 154, "LaH10_range_k": [160, 187], "LaH10_pressure_range_gpa": [200, 250]},
            },
            "dft": {
                "large_supercell_always_requires_denser_k": False,
                "r2scan_error_universal": False,
                "six_layer_ring_ready_for_input": False,
                "required_convergence_dimensions": ["reciprocal_space_spacing", "pseudopotential", "cutoff", "k_grid", "q_grid", "phonon", "interface"],
            },
            "nickelate": {
                "query": "NdNiO2 KTaO3 dome shaped",
                "search_result_count": len(nickelate_rows),
                "exact_dome_source_found": bool(exact_support),
                "negative_result_scope_limited": True,
            },
        },
        "corrections": [
            {"id": "isotope_formula_pair", "severity": "P0", "finding": "同位素公式缺少比值，240/168 K 与 α=0.46 不相容。", "action": "使用标准分式；原文表内复算约 0.514573，249/180 K 来源对约 0.468149，禁止跨来源拼接。"},
            {"id": "pressure_method_mix", "severity": "P0", "finding": "压力斜率跨 Eliashberg 与 SCDFT，且被叙述为实验 dome。", "action": "保留斜率算术，按方法分轨重画曲线并附实验点和不确定度。"},
            {"id": "kruglov_article", "severity": "P0", "finding": "Kruglov 文章号写成 224508。", "action": "更正为 Phys. Rev. B 101, 024508，DOI 10.1103/PhysRevB.101.024508。"},
            {"id": "supercell_k_rule", "severity": "P1", "finding": "大超胞被一概写成需要更密集 k 点。", "action": "改为固定倒空间间距与收敛规则；大超胞通常减少相应方向 k 点数量。"},
            {"id": "ml_speedup", "severity": "P1", "finding": "1000 倍加速没有同口径端到端基准。", "action": "分开 11500 core hours DFT、4/7 GPU hours 训练与推理成本，禁止自行换算加速比。"},
            {"id": "nickelate_source", "severity": "P1", "finding": "NdNiO₂/KTaO₃ 4–8 层超导穹顶缺精确出处。", "action": "本次 10 条检索未闭合来源；标未解析并补 DOI／原始图号，不判其为假。"},
            {"id": "mechanism_exclusive", "severity": "P1", "finding": "α≈0.5 被写成电子-声子机制的排他性最强证明。", "action": "改为支持性证据，联合同位素、谱函数、结构和替代机制对照。"},
            {"id": "universal_parameters", "severity": "P2", "finding": "截断能、r2SCAN<1% 和收敛阈值被通用化。", "action": "降为初始设置，逐材料提供赝势、k/q、能量、力和声子收敛证据。"},
        ],
        "open_boundaries": {
            "dft_rerun": False,
            "phonon_convergence": False,
            "ml_speed_benchmark": False,
            "nickelate_dome_verified": False,
            "six_layer_ring_defined": False,
            "full_repository_audit": False,
        },
        "figure": {
            "svg": "isotope-pressure-evidence.svg",
            "png": "isotope-pressure-evidence.png",
            "labels": ["Eliashberg", "SCDFT", "0.514573", "0.468149", "跨方法"],
            "caption": "图 1　同位素与压力斜率：算术正确不等于证据同轨",
            "insert_after": "压力斜率表",
            "insert_before": "结果解释",
            "experimental_percentage_plotted": False,
        },
        "verification_scope": {
            "source_documents_modified": False,
            "dft_dfpt_scdft_rerun": False,
            "alignn_training_or_inference_rerun": False,
            "new_experiment_or_independent_replication": False,
            "full_repository_audit": False,
        },
    }
    return data


def build_figure(data):
    plt.rcParams["font.family"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False
    fig, (left, right) = plt.subplots(1, 2, figsize=(12.8, 7.2), gridspec_kw={"width_ratios": [1, 1.25]})
    fig.patch.set_facecolor("#FAFBFC")
    iso = data["evidence"]["isotope"]
    pairs = [iso["printed_lah10"], iso["durajski_lah10"]]
    x = np.arange(2)
    width = 0.32
    h_values = [row["tc_h"] for row in pairs]
    d_values = [row["tc_d"] for row in pairs]
    left.bar(x - width / 2, h_values, width, label="Tc(H)", color="#8C7651")
    left.bar(x + width / 2, d_values, width, label="Tc(D)", color="#3E7772")
    for index, row in enumerate(pairs):
        left.text(index - width / 2, row["tc_h"] + 5, f"{row['tc_h']} K", ha="center", fontsize=10)
        left.text(index + width / 2, row["tc_d"] + 5, f"{row['tc_d']} K", ha="center", fontsize=10)
        left.text(index, max(row["tc_h"], row["tc_d"]) + 25, f"α={row['alpha']:.6f}", ha="center", fontsize=11, color="#8C4A3E", fontweight="bold")
    left.set_xticks(x, ["原文表内对\n240/168 K", "Durajski 来源对\n249/180 K"])
    left.set_ylim(0, 310)
    left.set_ylabel("Tc（K）")
    left.set_title("同位素：温度对必须绑定来源", fontsize=15, fontweight="bold")
    left.legend(frameon=False, loc="upper right")
    left.grid(axis="y", alpha=0.18)
    left.text(0.5, -0.19, f"H₃S 203/155 K → α={iso['h3s']['alpha']:.6f}（落在原表范围内）",
              transform=left.transAxes, ha="center", fontsize=10.5, color="#546E7A")
    left.spines[["top", "right"]].set_visible(False)

    rows = data["evidence"]["pressure"]["rows"]
    points = {170: (259, "Eliashberg"), 200: (271, "SCDFT"), 210: (249, "Eliashberg"), 250: (246, "Eliashberg")}
    for row in rows:
        p1, p2 = row["pressure_interval_gpa"]
        t1, t2 = row["tc_interval_k"]
        cross = row["crosses_method_boundary"]
        right.plot([p1, p2], [t1, t2], linestyle="--" if cross else "-", color="#A65D4E" if cross else "#455A64", linewidth=1.8)
        mid_p, mid_t = (p1 + p2) / 2, (t1 + t2) / 2
        right.annotate(f"{row['slope']:+.3f} K/GPa" + ("\n跨方法" if cross else "\n同方法"),
                       (mid_p, mid_t), textcoords="offset points", xytext=(0, 12 if row["slope"] > -1 else -32),
                       ha="center", fontsize=10, color="#8C4A3E" if cross else "#455A64")
    eli_x = [p for p, (_, method) in points.items() if method == "Eliashberg"]
    scdft_x = [p for p, (_, method) in points.items() if method == "SCDFT"]
    right.scatter(eli_x, [points[p][0] for p in eli_x], s=85, marker="o", color="#3E7772", label="Eliashberg", zorder=3)
    right.scatter(scdft_x, [points[p][0] for p in scdft_x], s=110, marker="D", color="#8C7651", label="SCDFT", zorder=3)
    for p, (tc, method) in points.items():
        right.annotate(f"{tc} K\n{method}", (p, tc), textcoords="offset points", xytext=(0, 9), ha="center", fontsize=9)
    right.set_xlim(160, 260)
    right.set_ylim(230, 286)
    right.set_xlabel("压力（GPa）")
    right.set_ylabel("Tc（K）")
    right.set_title("压力：斜率算术正确，但方法不完全同轨", fontsize=15, fontweight="bold")
    right.grid(alpha=0.18)
    right.legend(frameon=False, loc="lower left")
    right.spines[["top", "right"]].set_visible(False)
    right.text(0.5, -0.19, "这些点是理论结果，不是完整实验 Tc(P) 曲线；跨方法段不宜直接作物理解释。",
               transform=right.transAxes, ha="center", fontsize=10.5, color="#8C4A3E")
    fig.suptitle("同位素与压力斜率：算术正确不等于证据同轨", fontsize=20, fontweight="bold", color="#263238", y=0.985)
    fig.subplots_adjust(left=0.07, right=0.98, top=0.84, bottom=0.20, wspace=0.28)
    fig.savefig(AUDIT / data["figure"]["svg"], metadata={"Date": None})
    fig.savefig(AUDIT / data["figure"]["png"], dpi=220, metadata={"Software": None})
    plt.close(fig)


def build_markdown(data):
    iso = data["evidence"]["isotope"]
    pressure = data["evidence"]["pressure"]
    jarvis = data["evidence"]["jarvis"]
    nickelate = data["evidence"]["nickelate"]
    lines = [
        "# 同位素压力与多层 DFT：参数血缘、方法分轨与未竟工作审计",
        "",
        "> 日期：2026-11-10。只审计，不修改原文，不重跑 DFT／DFPT／SCDFT／ALIGNN，不新做实验。",
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
        "## 二、同位素：公式、温度对和来源必须一一对应",
        "",
        "标准公式为：",
        "",
        "$$\\alpha=-\\frac{\\ln T_{c,D}-\\ln T_{c,H}}{\\ln M_D-\\ln M_H}.$$",
        "",
        "| 温度对 | 压力 | 复算 α | 证据裁决 |",
        "|:--|--:|--:|:--|",
        f"| 原文 LaH₁₀：{iso['printed_lah10']['tc_h']}/{iso['printed_lah10']['tc_d']} K | {iso['printed_lah10']['pressure_gpa']} GPa | {iso['printed_lah10']['alpha']:.15f} | 不是文中 0.46，需核对温度对来源 |",
        f"| Durajski LaH₁₀：{iso['durajski_lah10']['tc_h']}/{iso['durajski_lah10']['tc_d']} K | 约 {iso['durajski_lah10']['pressure_gpa']} GPa | {iso['durajski_lah10']['alpha']:.15f} | 与原文报告约 0.46 对应 |",
        f"| H₃S：{iso['h3s']['tc_h']}/{iso['h3s']['tc_d']} K | {iso['h3s']['pressure_gpa']} GPa | {iso['h3s']['alpha']:.15f} | 落在原表 0.3–0.6 范围 |",
        "",
        "同位素系数支持电子-声子机制，但不能单独排他证明全部微观机制。后续必须绑定同压力 H/D 温度、结构相、样品和原始图号。",
        "",
        "## 三、压力：斜率算术正确，但跨方法且不是纯实验曲线",
        "",
        "Kruglov 正确书目为 **Phys. Rev. B 101, 024508**，原文写成 224508。表 1 的 271 K 星号明确标为 SCDFT，其余表内点为 Eliashberg。",
        "",
        "| 压力段（GPa） | 方法 | 复算斜率（K/GPa） | 证据边界 |",
        "|:--|:--|--:|:--|",
    ]
    for row in pressure["rows"]:
        lines.append(f"| {row['pressure_interval_gpa'][0]}→{row['pressure_interval_gpa'][1]} | {'→'.join(row['methods'])} | {row['slope']:+.3f} | {'跨方法' if row['crosses_method_boundary'] else '同方法，但仍是理论点'} |")
    lines += [
        "",
        "![图 1：同位素与压力斜率证据分轨](isotope-pressure-evidence.svg)",
        "",
        "**图件插入顺序：图 1 位于压力斜率表之后、结果解释之前。** 图中没有实验验证百分比。",
        "",
        "三个斜率的算术均正确；问题是前两段跨方法，整组不是完整实验 Tc(P) 曲线。后续应分别输出 Eliashberg、SCDFT 与实验曲线，只在方法一致时求导。",
        "",
        "## 四、DFT 与机器学习：从参数清单转为可复现契约",
        "",
        "| 项目 | 已核实角色 | 未竟工作 |",
        "|:--|:--|:--|",
        "| 大超胞与 k 点 | 大超胞不自动需要更密集 k 点 | 用倒空间间距和收敛曲线决定网格 |",
        "| 通用参数 | r2SCAN<1%、截断能和阈值不是跨材料保证 | 绑定赝势、k/q、能量、力与声子收敛日志 |",
        f"| JARVIS 数据 | 既有 {jarvis['previous_zero_pressure_bulk']}+ 块体和 {jarvis['previous_zero_pressure_2d']}+ 2D 零压数据真实；新增 {jarvis['new_hydride_count_label']}、{jarvis['new_pressure_range_gpa'][0]}–{jarvis['new_pressure_range_gpa'][1]} GPa、{jarvis['stable_candidates']} 个候选 | 两类数据不得混成同一训练或评价口径 |",
        f"| 1000 倍加速 | DFT {jarvis['dft_core_hours']} core hours；训练 {jarvis['training_gpu_hours'][0]}/{jarvis['training_gpu_hours'][1]} GPU hours；无端到端 1000 倍基准 | 补推理成本、硬件、任务定义和外部测试 |",
        f"| NdNiO₂/KTaO₃ | 本次 {nickelate['search_result_count']} 条检索未找到精确支持 4–8 层穹顶的来源 | 标未解析并补 DOI／图号，不判其为假 |",
        "| 六层环体 | 尚无可计算定义 | 先定义结构、层间耦合、边界条件和化学式，再生成输入 |",
        "",
        "## 五、分档勘误与发展任务",
        "",
        "| 级别 | 已观察问题 | 建议动作 |",
        "|:--|:--|:--|",
    ]
    for row in data["corrections"]:
        lines.append(f"| {row['severity']} | {row['finding']} | {row['action']} |")
    lines += [
        "",
        "优先发展顺序：先清偿同位素和书目血缘，再建立方法一致的压力曲线；随后完成最小多层结构的收敛切片与 ML 成本基准。四个方向是同一研究纲领的方法任务，不是四个新理论。",
        "",
        "## 六、验证范围与开放边界",
        "",
        "| 边界 | 状态 |",
        "|:--|:--|",
    ]
    for key, value in data["open_boundaries"].items():
        lines.append(f"| `{key}` | `{str(value).lower()}` |")
    lines += [
        "",
        "本批使用冻结哈希、原始 PDF、Scholar 检索和独立数值复算。命令与退出码见 `run.log`；Word 逐页结果见 `word-qa/report.json`。",
        "",
        "本批没有重跑计算、训练或实验，没有修改两份原文。**全库审计尚未完成。**",
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
        "printed_lah10_alpha": data["evidence"]["isotope"]["printed_lah10"]["alpha"],
        "durajski_alpha": data["evidence"]["isotope"]["durajski_lah10"]["alpha"],
        "slopes": [row["slope"] for row in data["evidence"]["pressure"]["rows"]],
        "nickelate_results": data["evidence"]["nickelate"]["search_result_count"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
