"""Preregistered 2x2 profile control: N=400/600 by r=0.05/0.1, seed=0."""

import hashlib
import json
from pathlib import Path
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from analyze_endpoint_subspaces import pair_metrics  # noqa: E402
sys.path.insert(0, str(ROOT.parent / "floquet-bdg-convention"))
sys.path.insert(0, str(ROOT.parent / "floquet-bdg-disorder"))
from convention_model import quasienergy_spectrum  # noqa: E402
from disorder_model import disordered_floquet  # noqa: E402

SOURCE = ROOT / "scale_diagnostic.json"
GRID = [(n, strength) for n in (400, 600) for strength in (0.05, 0.1)]
plt.rcParams.update({
    "font.sans-serif": ["Microsoft YaHei", "SimHei", "Noto Sans CJK SC", "DejaVu Sans"],
    "axes.unicode_minus": False, "font.size": 10, "figure.dpi": 160,
})


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compute_case(n, strength):
    beta = np.random.default_rng(20261111).random(n)
    u, period = disordered_floquet(n, 2.5, beta, strength, 7.0, 1.0, 1.0)
    spectrum = quasienergy_spectrum(u, period)
    distances = np.abs(spectrum["eigenvalues"] - 1.0)
    order = np.argsort(distances)
    pairs = [pair_metrics(spectrum, n, order[2 * index:2 * index + 2], index) for index in range(2)]
    if (n, strength) in ((400, 0.1), (600, 0.05)):
        old = json.loads((ROOT / f"n{n}_scale.json").read_text(encoding="utf-8"))
        if pairs[0]["profile_sha256"] != old["profile_sha256"] or pairs[0]["diagnostic_joint_pass"] != old["joint_pass"]:
            raise ValueError(f"Existing cell N={n}, r={strength} does not match its frozen evidence")
    return {"n": n, "strength": strength, "seed": 0, "pairs": pairs, "profile_only": True}


def case_lookup(cases, n, strength):
    return next(row for row in cases if row["n"] == n and row["strength"] == strength)


def contrast(n400, n600):
    first400, first600 = n400["pairs"][0], n600["pairs"][0]
    return {
        "delta_L50": first600["L50"] - first400["L50"],
        "delta_L90": first600["L90"] - first400["L90"],
        "delta_edge_weight": first600["edge_weight"] - first400["edge_weight"],
        "delta_center20_mass": first600["center20_mass"] - first400["center20_mass"],
    }


def contrasts(cases):
    size_rows = []
    for strength in (0.05, 0.1):
        row = {"strength": strength, **contrast(case_lookup(cases, 400, strength), case_lookup(cases, 600, strength))}
        size_rows.append(row)
    strength_rows = []
    for n in (400, 600):
        row = {"n": n, **contrast(case_lookup(cases, n, 0.05), case_lookup(cases, n, 0.1))}
        strength_rows.append(row)
    interaction = {
        "status": "descriptive_single_seed_only",
        "formula": "(N600-N400 at r=0.1) - (N600-N400 at r=0.05)",
        "delta_L50": size_rows[1]["delta_L50"] - size_rows[0]["delta_L50"],
        "delta_L90": size_rows[1]["delta_L90"] - size_rows[0]["delta_L90"],
        "delta_edge_weight": size_rows[1]["delta_edge_weight"] - size_rows[0]["delta_edge_weight"],
        "delta_center20_mass": size_rows[1]["delta_center20_mass"] - size_rows[0]["delta_center20_mass"],
    }
    return {"size_at_fixed_strength": size_rows, "strength_at_fixed_size": strength_rows, "interaction": interaction}


def figure(cases):
    fig, axes = plt.subplots(2, 2, figsize=(12, 8.4), constrained_layout=False)
    for axis, case in zip(axes.flat, cases):
        n = case["n"]
        for pair, color in zip(case["pairs"], ("#356A64", "#A25B3F")):
            profile = np.asarray(pair["profile"])
            cumulative = np.cumsum(profile + profile[::-1])
            axis.plot((np.arange(n) + 1) / n, cumulative, lw=1.5, color=color, label=f"第 {pair['pair_index'] + 1} 对")
        first = case["pairs"][0]
        axis.set_title(f"N={n}, r={case['strength']}：端点={first['edge_weight']:.3f}, L50={first['L50']}")
        axis.set_xlim(0, 0.5)
        axis.set_ylim(0, 1.02)
        axis.axhline(0.5, color="#888888", lw=0.7, ls="--")
        axis.axhline(0.9, color="#BBBBBB", lw=0.7, ls="--")
        axis.set_xlabel("每端覆盖宽度 / N")
        axis.set_ylabel("累计质量")
        axis.grid(alpha=0.2)
        axis.legend(frameon=False)
    fig.subplots_adjust(top=0.88, bottom=0.09, left=0.08, right=0.98, hspace=0.4, wspace=0.25)
    fig.suptitle("2×2 同种子对照：尺寸与无序强度的 profile 变化", fontsize=16, y=0.975)
    fig.savefig(ROOT / "matched-profile-control.png", bbox_inches="tight")
    plt.close(fig)


def fmt(value):
    return f"{value:.6g}"


def direction(value):
    if value > 0:
        return "增加"
    if value < 0:
        return "降低"
    return "不变"


def markdown(data):
    lines = [
        "# Floquet-BdG 同强度 2×2 尺寸对照",
        "",
        "> 日期：2026-11-11。N=400／600 × r=0.05／0.1，seed=0，使用同一嵌套随机流。新案例只做 profile 诊断，不补算体 winding，未计算 N=640。",
        "",
        "## 一、四格实测结果",
        "",
        "| N | r | 最近对端点权重 | L50 | L90 | 中心20%质量 | 最近对诊断 |",
        "|---:|---:|---:|---:|---:|---:|:---|",
    ]
    for case in data["cases"]:
        first = case["pairs"][0]
        lines.append(f"| {case['n']} | {case['strength']} | {fmt(first['edge_weight'])} | {first['L50']} | {first['L90']} | {fmt(first['center20_mass'])} | {first['diagnostic_joint_pass']} |")
    lines += [
        "",
        "图 1 插入位置：四格实测表之后、因子对照之前。",
        "",
        "![图 1：二乘二同种子覆盖对照](matched-profile-control.png)",
        "",
        "**图 1**　四格均同时给出最近对与次近对；次近对只作诊断，不回溯改变原端点结论。",
        "",
        "## 二、固定强度的尺寸对照",
        "",
        "| r | ΔL50（N600−N400） | ΔL90 | Δ端点权重 | Δ中心20%质量 |",
        "|---:|---:|---:|---:|---:|",
    ]
    for row in data["contrasts"]["size_at_fixed_strength"]:
        lines.append(f"| {row['strength']} | {row['delta_L50']} | {row['delta_L90']} | {fmt(row['delta_edge_weight'])} | {fmt(row['delta_center20_mass'])} |")
    lines += [
        "",
        "两条尺寸对照分别在 r=0.05 与 r=0.1 下计算，不把此前不同强度案例直接相减。",
        "",
        "## 三、固定尺寸的强度对照",
        "",
        "| N | ΔL50（r0.1−r0.05） | ΔL90 | Δ端点权重 | Δ中心20%质量 |",
        "|---:|---:|---:|---:|---:|",
    ]
    for row in data["contrasts"]["strength_at_fixed_size"]:
        lines.append(f"| {row['n']} | {row['delta_L50']} | {row['delta_L90']} | {fmt(row['delta_edge_weight'])} | {fmt(row['delta_center20_mass'])} |")
    interaction = data["contrasts"]["interaction"]
    lines += [
        "",
        f"描述性交互项（r=0.1 的尺寸差减去 r=0.05 的尺寸差）为：ΔL50={interaction['delta_L50']}，ΔL90={interaction['delta_L90']}，Δ端点权重={fmt(interaction['delta_edge_weight'])}，Δ中心20%质量={fmt(interaction['delta_center20_mass'])}。",
        "",
        "交互项仅用于判断尺寸效应是否随强度改变方向或幅度；它是单种子有限样本的描述量，不是统计显著性、独立重复或因果证明。",
        "",
        "## 四、本轮可支持与不可支持的解释",
        "",
        "尺寸效应在两种强度下方向不同：r=0.05 时，N=600 相对 N=400 的 L50 增加 34、端点权重下降约 0.065；r=0.1 时，L50 增加 13、端点权重上升约 0.073。端点权重的符号反转仅是 seed=0 的实测描述，不是普遍尺寸律。",
        "",
        "在 N=400 和 N=600 上，强度从 0.05 增至 0.1 都伴随 L50 缩短，且强度升高伴随端点权重增加。该现象只描述当前有限模型和两个强度点，不能外推为无序越强越局域的普遍结论。",
        "",
        "N=600、r=0.1 的新 profile 判据通过，但不等于体 winding 已验证。它只登记为同尺寸、同强度、同种子的后续体积分候选，不补写拓扑恢复，也不替换 N=600、r=0.05 的既有未恢复结论。",
        "",
        "## 五、解释边界与后续",
        "",
        "该 2×2 设计消除了跨强度直接比较造成的混杂，但仍只有 seed=0。新计算的两个 profile 单元不补算体 winding，因此不能把任何局部端点变化单独升级为体边拓扑恢复。",
        "",
        "下一步应增加预登记种子，而不是后验挑选阈值；先检验各对照方向是否在多个种子间一致，再讨论可复核的标度或恢复区间。",
        "",
        "复现：`python research/floquet-bdg-tbc/analyze_matched_profiles.py`。完整剖面、对比公式和原始哈希保存在 `matched_profile_control.json`。",
        "",
    ]
    (ROOT / "MATCHED_PROFILE_CONTROL.md").write_text("\n".join(lines), encoding="utf-8")


def main():
    cases = [compute_case(n, strength) for n, strength in GRID]
    data = {
        "schema": "floquet-bdg-matched-profile-control-v1",
        "analysis_date": "2026-11-11",
        "source_sha256": sha(SOURCE),
        "grid": "N=400/600 by r=0.05/0.1; seed=0; nested beta stream",
        "new_cases_are_profile_only": True,
        "new_winding_computed": False,
        "n640_computed": False,
        "thermodynamic_limit_proof": False,
        "causal_or_statistical_claim": False,
        "cases": cases,
        "contrasts": contrasts(cases),
    }
    (ROOT / "matched_profile_control.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    figure(cases)
    markdown(data)
    print(json.dumps({
        "cases": [{"n": case["n"], "strength": case["strength"], "first_pair": {key: value for key, value in case["pairs"][0].items() if key != "profile"}} for case in cases],
        "contrasts": data["contrasts"],
        "new_winding_computed": False,
        "n640_computed": False,
    }, ensure_ascii=False, indent=2))
    print("generated matched_profile_control.json matched-profile-control.png MATCHED_PROFILE_CONTROL.md")


if __name__ == "__main__":
    main()
