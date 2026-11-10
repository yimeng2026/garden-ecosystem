"""Build the physical-intuition audit from frozen source evidence."""

import hashlib
import json
from pathlib import Path

AUDIT = Path(__file__).resolve().parent
EXPECTED_HASHES = {
    "physical-intuition:research/physical-intuition/MATH_PHYSICS_WORLDVIEW_2026.md": "89fc5499acd3f5afd05ffd0b4eacae3f40d33822802679a3c105d34acc0f9eb4",
    "physical-intuition:research/physical-intuition/TOTAL_PROJECT_2026-11-08/TOTAL_REPORT.md": "91f6653c273c3783e9fc71ef8b9b64463a038fecd5763633038e601d93ae862d",
}
UNIT_TEST_COMMAND = 'python -m unittest discover -s "C:/Users/一梦/Documents/kimi/workspace/.worktrees/provider-main-integration/research/physical-intuition/zero-cdm/tests" -p "test*.py" -v'


def provider_dir():
    for parent in AUDIT.parents:
        candidate = parent / ".worktrees/provider-main-integration/research/physical-intuition"
        if candidate.is_dir():
            return candidate
    raise FileNotFoundError("provider physical-intuition directory not found")


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_data():
    provider = provider_dir()
    h0 = read_json(provider / "zero-cdm/planck-h0-scan-summary.json")
    lensing = read_json(provider / "zero-cdm/planck-lensing-cmbmarged-summary.json")
    full_cmb = read_json(provider / "zero-cdm/planck-cmb-unbounded-hyrec-summary.json")
    bbn = read_json(provider / "zero-cdm/bbn-summary.json")
    sources = []
    for source_id, expected in EXPECTED_HASHES.items():
        relative = source_id.split(":", 1)[1].removeprefix(
            "research/physical-intuition/"
        )
        actual = sha256(provider / relative)
        if actual != expected:
            raise ValueError(f"source hash changed: {source_id}: {actual} != {expected}")
        sources.append({"id": source_id, "sha256": actual, "read_only": True})

    lensing_models = lensing["records"]["cmb_marginalized"]["models"]
    lensing_deltas = [
        row["delta_chi_squared_zero_minus_baseline"]
        for row in lensing_models.values()
    ]
    bbn_deltas = [
        abs(row["delta_chi_squared_zero_minus_baseline"])
        for row in bbn["observational"].values()
    ]
    decision = h0["decision"]
    directions = [
        {
            "id": "math_physics_methodology",
            "role": "项目内独立的方法论方向，不是外部新的统一物理理论",
            "status": "active_methodology_not_external_toe",
            "closed": "真理、模型与数据分轨；类型化层级、结构卡和可否证流程已有书面框架。",
            "unfinished": "结构卡覆盖、冻结后评估、跨问题族迁移、常规基线对照与成本审计。",
            "next": "以未见任务和统一成本面板检验结构卡的实际增益。",
        },
        {
            "id": "zero_cdm_observation",
            "role": "明确联合模型的可证伪研究方向，与总报告同一血缘",
            "status": "fixed_model_strongly_disfavored_broader_open",
            "closed": "固定输入零模型被 Planck 透镜和完整 CMB 强烈排除；五点 H0 切片没有挽救；BBN 不能抵消 CMB 排除。",
            "unfinished": "非线性、完整参数空间、独立 Boltzmann 实现、更多数据联合、真实物质部门与替代模型。",
            "next": "把固定点负向结果与全参数后验、非线性和其他无 CDM 机制分开推进。",
        },
        {
            "id": "crosscode_systematics",
            "role": "可独立发展的跨代码与数值验证基础设施方向",
            "status": "partially_closed_open_convergence",
            "closed": "TT 透镜口径、若干插值与共动映射错误已纠正；k800 输出加密被证明无收益。",
            "unfinished": "极端相位与深谷未收敛，复合实现差异仍在；AccuracyBoost=8 多次触及 300 秒前台时限且无结果。",
            "next": "以单变量精度和独立实现研究剩余系统误差，不把 ultra 当最佳估计。",
        },
        {
            "id": "physical_intuition_engine",
            "role": "候选工程与评价方向，不是已经验证有效的系统",
            "status": "design_only_unvalidated",
            "closed": "混合工作流、双方法评委、任务包和证据卡已有设计。",
            "unfinished": "真实引擎实现、未见任务盲测、常规模型对照、消融、许可清单、失败分布和教师依赖评估。",
            "next": "先实现最小引擎，再用隔离数据、消融和常规基线检验相对增益。",
        },
    ]
    return {
        "schema": "physical-intuition-direction-audit-v1",
        "sources": sources,
        "source_lineage": {
            "research_program_count": 1,
            "decision": "两份文档属于同一研究纲领，合订本不是独立新理论。",
        },
        "directions": directions,
        "evidence": {
            "unit_tests": {"passed": 41, "total": 41, "command": UNIT_TEST_COMMAND},
            "h0_scan": {
                "case_count": len(h0["rows"]) * 2,
                "rows": h0["rows"],
                "minimum_h0": decision["minimum_h0"],
                "minimum_delta_chi_squared": decision["minimum_delta_chi_squared"],
                "expanded_scan_triggered": decision["expanded_scan_triggered"],
                "follow_up_threshold": decision["follow_up_threshold"],
                "posterior_sampling_performed": h0["validation"]["posterior_sampling_performed"],
            },
            "planck_lensing": {
                "minimum_delta_chi_squared": min(lensing_deltas),
                "maximum_delta_chi_squared": max(lensing_deltas),
                "scope": "固定输入的 Planck 2018 边缘化透镜诊断，不是全参数拟合。",
            },
            "full_cmb_hyrec": {
                "delta_chi_squared_total": full_cmb["comparison"]["delta_chi_squared_total"],
                "posterior_sampling_performed": full_cmb["validation"]["posterior_sampling_performed"],
                "scope": "局部 nuisance profile，不是全参数后验或全局最优证明。",
            },
            "bbn": {
                "maximum_absolute_delta_chi_squared": max(bbn_deltas),
                "scope": "BBN 近似一致，不能抵消 CMB 排除；不是联合后验。",
            },
            "crosscode_systematics": {
                "k800_shared_nodes": 5878,
                "k800_bandpower_log_change": 0.0,
                "accuracy_boost_8": "多次触及 300 秒前台时限，没有数值结果。",
                "phase_sequence": "零交叉数和完整相位序列未收敛。",
            },
        },
        "open_boundaries": {
            "global_cosmological_fit_completed": False,
            "nonlinear_matter_spectrum_completed": False,
            "extreme_phase_sequence_converged": False,
            "accuracy_boost_8_completed": False,
            "physical_intuition_engine_validated": False,
        },
        "figure": {
            "svg": "h0-scan-comparison.svg",
            "png": "h0-scan-comparison.png",
            "scope": "五点 H0 单变量切片，不是全参数拟合。",
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
    plt.rcParams["svg.hashsalt"] = "physical-intuition-h0-audit-v1"
    rows = data["evidence"]["h0_scan"]["rows"]
    h0 = [row["h0"] for row in rows]
    zero = [row["zero_chi_squared_total"] for row in rows]
    baseline = [row["baseline_chi_squared_total"] for row in rows]
    delta = [row["delta_chi_squared_total"] for row in rows]
    fig, axes = plt.subplots(1, 2, figsize=(12.4, 5.5), dpi=180)
    axes[0].plot(h0, zero, "o-", color="#8c4a52", label="零模型")
    axes[0].plot(h0, baseline, "s-", color="#397a76", label="ΛCDM 对照")
    axes[0].set_yscale("log")
    axes[0].set_xlabel("H0（km/s/Mpc）")
    axes[0].set_ylabel("总 χ²（对数轴）")
    axes[0].set_title("十个病例的总 CMB 似然")
    axes[0].legend(frameon=False)
    axes[0].grid(alpha=0.2)
    axes[1].plot(h0, delta, "o-", color="#8c6d3f", label="零模型 − 基线")
    axes[1].axhline(10, color="#555555", linestyle="--", label="计算跟进阈值 10（非 σ）")
    axes[1].set_yscale("log")
    axes[1].set_xlabel("H0（km/s/Mpc）")
    axes[1].set_ylabel("配对 Δχ²（对数轴）")
    axes[1].set_title("五点切片没有挽救零模型")
    axes[1].legend(frameon=False)
    axes[1].grid(alpha=0.2)
    minimum = min(range(len(delta)), key=delta.__getitem__)
    axes[1].annotate(
        f"最小值 {delta[minimum]:,.3f}",
        (h0[minimum], delta[minimum]),
        xytext=(-100, 24),
        textcoords="offset points",
        arrowprops={"arrowstyle": "->", "color": "#555555"},
    )
    fig.suptitle("五点 H0 单变量切片：不是全参数拟合", fontsize=15)
    fig.tight_layout(rect=(0, 0.02, 1, 0.94))
    fig.savefig(AUDIT / "h0-scan-comparison.svg", metadata={"Date": None})
    fig.savefig(AUDIT / "h0-scan-comparison.png", dpi=220, metadata={"Software": "physical-intuition-audit"})
    plt.close(fig)


def build_markdown(data):
    lines = [
        "# 物理直觉两份文档：方向、血缘与未竟工作审计",
        "",
        "> 日期：2026-11-10。范围：两份 integrated research report 及其冻结数值证据。本文不修改提供方工作树，不重跑全参数空间，不把局部 profile 写成宇宙学后验。",
        "",
        "## 一、来源与血缘裁决",
        "",
        "两份文档属于**同一研究纲领**，合订本不是独立新理论。以下哈希在生成时重新计算并与清单一致：",
        "",
    ]
    for source in data["sources"]:
        lines.append(f"- `{source['id']}`：`{source['sha256']}`（只读）。")
    lines += [
        "",
        "主文档当前含未提交修改，审计只读其当前内容；提供方的其他修改保持原状。36 节不机械拆成 36 个方向，而归为四个候选问题族。",
        "",
        "## 二、四个候选问题族",
        "",
        "| 问题族 | 当前角色 | 已闭合的局部工作 | 未竟工作与下一步 |\n|------|------|------|------|",
    ]
    for row in data["directions"]:
        lines.append(f"| {row['id']} | {row['role']} | {row['closed']} | {row['unfinished']}下一步：{row['next']} |")
    lines += [
        "",
        "这些候选方向不自动意味着外部首创，也不表示四条路线均已完成。",
        "",
        "## 三、固定零模型的负向证据",
        "",
        "固定输入零模型的比较定义为：",
        "",
        "$$\\Delta\\chi^2=\\chi^2_{\\mathrm{zero}}-\\chi^2_{\\Lambda\\mathrm{CDM}}.$$",
        "",
        f"Planck 2018 边缘化透镜的三条实现给出 Δχ² 为 {data['evidence']['planck_lensing']['minimum_delta_chi_squared']:.6f} 至 {data['evidence']['planck_lensing']['maximum_delta_chi_squared']:.6f}，固定零模型受到强烈排除。完整 CMB 的 HyRec 扩展搜索结果为 Δχ²＝{data['evidence']['full_cmb_hyrec']['delta_chi_squared_total']:.6f}，但这里只允许报告已找到并复验的局部 nuisance profile。",
        "",
        "### H0 单变量切片",
        "",
        "| H0（km/s/Mpc） | 零模型总 χ² | ΛCDM 总 χ² | 零模型−基线 Δχ² |",
        "|---:|---:|---:|---:|",
    ]
    for row in data["evidence"]["h0_scan"]["rows"]:
        lines.append(
            f"| {row['h0']:g} | {row['zero_chi_squared_total']:.3f} "
            f"| {row['baseline_chi_squared_total']:.3f} | {row['delta_chi_squared_total']:.3f} |"
        )
    lines += [
        "",
        "![图 1：H0 单变量切片](h0-scan-comparison.svg)",
        "",
        "**图件插入顺序：图 1 位于五点数据表之后、结果解释之前。** 图 1 与表中数据来自同一 `planck-h0-scan-summary.json`，不是全参数拟合。",
        "",
        f"最小配对差出现在 H0＝{data['evidence']['h0_scan']['minimum_h0']:g}，为 {data['evidence']['h0_scan']['minimum_delta_chi_squared']}。该值仍远高于计算跟进阈值 10，未触发扩展扫描；阈值不是 p 值或 σ 显著性。",
        "",
        f"BBN 的三组观测选择中，零模型与基线的最大绝对 Δχ² 仅为 {data['evidence']['bbn']['maximum_absolute_delta_chi_squared']:.12f}，近似一致，不能抵消 CMB 排除。",
        "",
        "**边界：以上结果不是整个无 CDM 模型族的排除，也不是全参数后验或全局最优证明。**",
        "",
        "## 四、跨代码系统误差：哪些闭合，哪些没有",
        "",
        "TT 透镜口径、若干插值与共动映射错误已经纠正；k800 与 ultra 的全部 5878 个共享 q 节点和共动密度逐位一致，最高带对数变化为 0，说明输出加密没有求解精度收益。AccuracyBoost=8 多次触及 300 秒前台时限且没有数值结果，不能写成已完成。",
        "",
        "极端相位序列、深谷点值、复合实现差异和非线性仍未闭合。相邻精度稳定、规范修正或单变量零差异不能升级为全谱、观测或跨代码闭合。",
        "",
        "## 五、物理直觉工程化尚未验收",
        "",
        "**物理直觉引擎尚未验证有效。** 当前只有混合工作流、双方法评委、任务包和证据卡设计，不能据此证明程序存在、模型有效或跨领域直觉可靠。下一步必须先实现最小引擎，再使用未见任务、常规模型对照、消融、许可清单和失败分布评估相对增益。",
        "",
        "数学—物理观与 AI 研究治理同样需要以实际任务覆盖、成本面板和冻结后评估检验，不能将结构化文档等同于已完成的制度。",
        "",
        "## 六、验证命令与范围",
        "",
        "基线测试：",
        "",
        f"`{data['evidence']['unit_tests']['command']}`",
        "",
        "实际为 41/41 通过。审计合同运行 `python test_physical_intuition_audit.py -v`；Word 使用 `docx.py build`／`validate` 与 doc-k 最终视图逐页验收，命令和退出码见 `run.log` 与 `word-qa/report.json`。",
        "",
        "本审计只覆盖这两份文档，不代表全库审计完成，也不替代非线性、全参数、独立实现和物理直觉引擎的后续验证。",
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
        "unit_tests": data["evidence"]["unit_tests"]["passed"],
        "minimum_delta_chi_squared": data["evidence"]["h0_scan"]["minimum_delta_chi_squared"],
        "expanded_scan_triggered": data["evidence"]["h0_scan"]["expanded_scan_triggered"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
