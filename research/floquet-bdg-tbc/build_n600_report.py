"""Compute N=600 profile metrics and build the tail-growth diagnostic report."""

import hashlib
import json
from pathlib import Path
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / "floquet-bdg-convention"))
sys.path.insert(0, str(ROOT.parent / "floquet-bdg-disorder"))
sys.path.insert(0, str(ROOT.parent / "floquet-bdg-localization"))
sys.path.insert(0, str(ROOT.parent / "floquet-bdg-localization-scale"))
from convention_model import quasienergy_spectrum  # noqa: E402
from disorder_model import disordered_floquet, observe_candidate  # noqa: E402
from localization_analysis import fit_envelope  # noqa: E402
from scale_analysis import center_mass, coverage_lengths, fixed_width_masses  # noqa: E402

DATA = json.loads((ROOT / "scale_diagnostic.json").read_text(encoding="utf-8"))
INDEPENDENT = json.loads((ROOT / "scale_independent_n600.json").read_text(encoding="utf-8"))
OLD = json.loads((ROOT.parent / "floquet-bdg-localization-scale" / "localization_scale.json").read_text(encoding="utf-8"))
N400 = json.loads((ROOT / "n400_scale.json").read_text(encoding="utf-8"))
plt.rcParams.update({
    "font.sans-serif": ["Microsoft YaHei", "SimHei", "Noto Sans CJK SC", "DejaVu Sans"],
    "axes.unicode_minus": False, "font.size": 10, "figure.dpi": 160,
})


def compute_metrics():
    row = next(row for row in DATA["rows"] if row["n"] == 600)
    n, strength, seed = row["n"], row["strength"], row["seed"]
    beta = np.random.default_rng(20261111 + seed).random(n)
    u, period = disordered_floquet(n, 2.5, beta, strength, 7.0, 1.0, 1.0)
    spectrum = quasienergy_spectrum(u, period)
    observed = observe_candidate(spectrum, n, 1.0)
    profile = observed.pop("profile")
    lengths = coverage_lengths(profile)
    masses = fixed_width_masses(profile)
    metrics = {
        "n": n, "strength": strength, "seed": seed,
        **lengths, "L50_fraction": lengths["L50"] / n,
        "mass5": masses["5"], "mass10": masses["10"], "mass20": masses["20"], "mass40": masses["40"],
        "center20_mass": center_mass(profile, fraction=0.2),
        "subspace_ipr": float(np.sum(profile**2)), "n_subspace_ipr": float(n * np.sum(profile**2)),
        "edge_weight": observed["edge_weight"], "separation": float(max(observed["separation_ratios"])),
        "joint_pass": bool(observed["joint_pass"]), "envelope": fit_envelope(profile),
        "profile_sha256": hashlib.sha256(profile.tobytes()).hexdigest(),
    }
    if metrics["edge_weight"] != row["endpoint"]["zero"]["edge_weight"] or metrics["joint_pass"] != row["endpoint"]["zero"]["joint_pass"]:
        raise ValueError("N=600 profile does not match the stored endpoint observation")
    return metrics


def old_case(strength, seed):
    return next(case for case in OLD["cases"] if case["strength"] == strength and case["seed"] == seed)


def figure_result(row):
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.8), constrained_layout=False)
    axes[0].bar(["主积分 W0", "独立行列式 W0"], [row["zero"]["value"], INDEPENDENT["independent"]["value"]], color=["#A25B3F", "#356A64"], width=0.55)
    axes[0].set_ylim(0.9997, 1.00003)
    axes[0].set_ylabel("winding 原始值")
    axes[0].grid(axis="y", alpha=0.2)
    axes[1].bar(["N=320", "N=600"], [0.3444370991575432, row["endpoint"]["zero"]["edge_weight"]], color=["#A25B3F", "#805500"], width=0.55)
    axes[1].axhline(0.5, color="#777777", ls="--", lw=1)
    axes[1].set_ylim(0, 0.65)
    axes[1].set_ylabel("端点权重")
    axes[1].grid(axis="y", alpha=0.2)
    fig.subplots_adjust(top=0.78, bottom=0.16, wspace=0.3)
    fig.suptitle("N=600：体 W0=1，端点仍未恢复", fontsize=16, y=0.97)
    fig.savefig(ROOT / "n600-result.png", bbox_inches="tight")
    plt.close(fig)


def figure_scale(metrics):
    fig, axes = plt.subplots(1, 2, figsize=(12, 5.2), constrained_layout=False)
    for strength, seed, color, label in ((0.05, 0, "#8B3A3A", "N.05s0"), (0.1, 0, "#A25B3F", "N.1s0")):
        case = old_case(strength, seed)
        for ax, metric in zip(axes, ("L50", "L90")):
            values = [row[metric] for row in case["rows"]]
            if strength == 0.05:
                values.append(metrics[metric])
                sizes = [80, 160, 320, 600]
            else:
                values.append(N400[metric])
                sizes = [80, 160, 320, 400]
            ax.plot(sizes, values, marker="o", ms=7, lw=1.5, color=color, label=label)
    for ax, metric in zip(axes, ("L50", "L90")):
        ax.set_xticks([80, 160, 320, 400, 600])
        ax.set_xlabel("链长 N")
        ax.set_ylabel(metric)
        ax.grid(alpha=0.2)
        ax.legend(frameon=False)
    fig.subplots_adjust(top=0.80, bottom=0.15, wspace=0.25)
    fig.suptitle("N=600：L50/L90 必须继续与阈值穿越分开", fontsize=16, y=0.97)
    fig.savefig(ROOT / "n600-coverage.png", bbox_inches="tight")
    plt.close(fig)


def fmt(value, digits=6):
    if value is None:
        return "—"
    if isinstance(value, str):
        return value
    return f"{value:.{digits}g}"


def markdown(metrics):
    row = next(row for row in DATA["rows"] if row["n"] == 600)
    old = old_case(0.05, 0)
    lines = [
        "# N=600 Floquet-BdG 尾长增长诊断",
        "",
        "> 日期：2026-11-11。N=600、r=0.05、seed=0。主双网格 dθ=0.05/0.025，独立原始 expm＋Schur 行列式 dθ=0.25。N=600 不是自动恢复尺寸。",
        "",
        "## 一、体 winding 与端点状态",
        "",
        "| 项目 | N=320 | N=600 |",
        "|:---|---:|---:|",
        f"| 主 W0 原始值 | 0.999895392848 | {fmt(row['zero']['value'], 12)} |",
        f"| 最小 0 体隙 | 0.00187302 | {fmt(row['zero']['min_bulk_gap'])} |",
        f"| 端点权重 | 0.344437 | {fmt(row['endpoint']['zero']['edge_weight'])} |",
        f"| 最大分离比 | 0.0245131 | {fmt(max(row['endpoint']['zero']['separation_ratios']))} |",
        f"| 端点联合判据 | False | {row['endpoint']['zero']['joint_pass']} |",
        "",
        f"独立原始 expm＋Schur 行列式为 {fmt(INDEPENDENT['independent']['value'], 12)}，与主整数一致；最大对称误差 {fmt(INDEPENDENT['independent']['max_symmetry_error'])}。",
        "",
        "图 1 插入位置：体与端点状态之后、覆盖分析之前。",
        "",
        "![图 1：N600 体与端点结果](n600-result.png)",
        "",
        "**图 1**　主积分与独立复核一致，但端点联合判据仍未通过。",
        "",
        "## 二、覆盖尾部是否继续增长",
        "",
        "| 指标 | N=80 | N=160 | N=320 | N=600 |",
        "|:---|---:|---:|---:|---:|",
    ]
    for metric, label in (("L50", "L50"), ("L90", "L90"), ("mass20", "固定20格点质量"), ("center20_mass", "中心20%质量"), ("n_subspace_ipr", "N·IPR")):
        values = [item[metric] for item in old["rows"]] + [metrics[metric]]
        lines.append(f"| {label} | " + " | ".join(fmt(value) for value in values) + " |")
    lines += [
        "",
        "L50 从 21→31→51→85，L90 从 38→70→115→164，未形成平台。",
        "",
        f"N=600 包络拟合 R²={fmt(metrics['envelope']['r_squared'])}。N=600 的体 W0=1 不等于端点恢复，N=600 的尺寸本身也不证明短尾平台。",
        "",
        "图 2 插入位置：覆盖分析之后、解释边界之前。",
        "",
        "![图 2：N600 覆盖尾长对照](n600-coverage.png)",
        "",
        "**图 2**　N.05s0 与 N.1s0 的覆盖机制不同；N=400 的阈值穿越不能代替 N=600 的尾长诊断。",
        "",
        "## 三、解释边界与后续方向",
        "",
        "N=400 已验证 r=0.1、seed=0 的局部阈值穿越；N=600 则检验 r=0.05、seed=0 的尾长机制。两个案例必须分开解释。",
        "",
        "下一步不自动扩大到 N=640 或更大尺寸，而应保留这两个未恢复样本作为体边对应边界案例，结合现有 N=80/160/320/400/600 的 profile 分析，先判断是否存在可复核的平台，再决定是否有新尺寸能区分机制。",
        "",
        "复现：run_scale_diagnostic.py 分批执行两条网格；verify_scale_diagnostic.py --n 600 --step 0.25 使用原始 expm＋Schur 独立复核。原始数据：scale_diagnostic.json、scale_independent_n600.json、n600_scale.json。",
        "",
    ]
    (ROOT / "N600_DIAGNOSTIC.md").write_text("\n".join(lines), encoding="utf-8")


def main():
    metrics = compute_metrics()
    (ROOT / "n600_scale.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("N600 metrics", json.dumps({key: value for key, value in metrics.items() if key not in ("envelope", "profile_sha256")}, ensure_ascii=False))
    print("envelope_R2", metrics["envelope"]["r_squared"])
    row = next(row for row in DATA["rows"] if row["n"] == 600)
    figure_result(row)
    figure_scale(metrics)
    markdown(metrics)
    print("generated n600-result.png n600-coverage.png N600_DIAGNOSTIC.md")


if __name__ == "__main__":
    main()
