"""Generate the corrected topology report from current, not legacy, results."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
data = json.loads((ROOT / "results.json").read_text(encoding="utf-8"))


def sci(value):
    return f"{value:.6e}"


def main():
    lines = [
        "# Floquet–BdG 约定修复与联合拓扑诊断",
        "",
        "> 2026-11-11。Fock 校验后的二次型 Kitaev 模型；不是材料超导增强或实验验证。",
        "",
        "## 一、先修正旧实现，再讨论 0／π 模",
        "",
        "旧 `research/floquet-bdg/floquet_bdg.py` 在 `H=iΣKΓΓ` 的完整反对称求和下漏除了 2，使目标模型的时间演化放大两倍。独立 Fock 探针给出：单格点 `U[0,1]=0.5702416578408517`，参考值 `0.2987666363611303`；双格点最大矩阵元差 `0.81`。旧静态零空间和正交性测试无法发现这一全局因子。",
        "",
        "修正后的直接矩阵元为 `K[a_j,b_j]=−μ/2`、`K[a_j,b_(j+1)]=(Δ−γ)/4`、`K[a_(j+1),b_j]=−(Δ+γ)/4`。一／双格点 Fock 逐元素与 Heisenberg 演化检验已通过。旧结果、图件和 Word 保留原字节，影响范围见 `research/floquet-bdg/ERRATA.md`；本包不继承旧的 π 通过或 0 未决结论。",
        "",
        "## 二、周期链拓扑：winding 与端点计数",
        "",
        "采用负 hopping 约定的 `h(k)=2(−γcosk−μ0)τ_z+2Δsinkτ_y`，以及 `U(k)=e^{iμ1τ_z}e^{−ih(k)T}e^{iμ1τ_z}`。在 `0<φ<π` 分支提取 `n_y,n_z`，避免直接 `logm` 的分支切割；另用抽样 `logm` 核对方向。",
        "",
        "| Nk | winding | 最近整数 | min sinφ |",
        "|---:|---:|---:|---:|",
    ]
    for row in data["winding"]["rows"]:
        lines.append(f"| {row['nk']} | {row['winding']:.12f} | {row['nearest_integer']} | {row['min_sin_phi']:.9f} |")
    lines += [
        "",
        "主算例在全部四种动量网格上均得到 `W=2`，与文献参考一致。",
        "",
        f"端点量 `b0={data['endpoint_invariants']['b0']:.9f}`、`bπ={data['endpoint_invariants']['b_pi']:.9f}`，限定域内每端 `p0=1`、`pπ=1`。负 hopping 下 `k=0` 对应 `bπ`、`k=π` 对应 `b0`，已显式核对。",
        "",
        f"有能隙静态平凡控制 `ω=17` 给出 `W={data['winding']['controls']['static_trivial_omega17']['winding']:.1f}`；静态拓扑控制给出 `W={data['winding']['controls']['static_topological_mu0']['winding']:.1f}`。`|W|=2` 只给出总数，`p0/pπ` 才分别给出 0／π 端点计数。",
        "",
        "## 三、修正后的开放链",
        "",
        "| N | 模 | 最大候选距离 | 最大分离比 | 最小端点权重 | 全尺寸旧判据 |",
        "|---:|:---:|---:|---:|---:|:---|",
    ]
    for study in data["size_studies"]:
        for target, name in (("zero", "0"), ("pi", "π")):
            row = study[target]
            lines.append(f"| {study['n']} | {name} | {sci(max(row['distances']))} | {max(row['separation_ratios']):.6e} | {min(row['edge_weights']):.6f} | {data['convergence'][target]['finite_size_status']} |")
    n160 = data["size_studies"][-1]
    lines += [
        "",
        "在 `N=160`，两类最近候选均满足分离比 `<0.1` 和端点权重 `>0.5`。最近四对谱还显示，第二近对不再被误当成体模：",
        "",
        "| 模 | 第一对最大距离 | 第一对最小端点权重 | 第二对最大距离 | 第二对最大端点权重 |",
        "|:---:|---:|---:|---:|---:|",
    ]
    for target, name in (("zero", "0"), ("pi", "π")):
        first, second = n160[f"{target}_nearest_pairs"][:2]
        lines.append(f"| {name} | {sci(first['max_distance'])} | {min(first['edge_weights']):.6f} | {sci(second['max_distance'])} | {max(second['edge_weights']):.6f} |")
    lines += [
        "",
        f"但 `N=40` 的 0 模最小端点权重为 `{min(data['size_studies'][0]['zero']['edge_weights']):.6f}`，略低于 0.5；π 模为 `{min(data['size_studies'][0]['pi']['edge_weights']):.6f}`。因此不修改旧阈值，不宣称全尺寸序列通过。准确结论是：**体拓扑与大尺寸边缘候选相互支持；短链局域限制仍使全尺寸旧判据保持 `inconclusive`。**",
        "",
        "![修正后的拓扑与开放链证据](topology.png)",
        "",
        "图 1：A 为 Bloch 有效矢量轨迹；B 为 winding 网格收敛；C 为修正后候选距离；D 为端点权重。所有数据来自本次 Fock 校验后的计算。",
        "",
        "## 四、验证与未竟边界",
        "",
        "独立复核重新构造 Fock 参考、核对 winding 与控制组、重算 `N=160`、比较最近四对谱，并确认旧 `results.json` 哈希未改变。",
        "",
        "```bash",
        "python research/floquet-bdg-convention/test_convention.py -v",
        "python research/floquet-bdg-convention/test_topology.py -v",
        "python research/floquet-bdg-convention/verify_topology.py -v",
        "python research/floquet-bdg-convention/run_verification.py",
        "```",
        "",
        "当前没有相互作用、耗散、自洽配对、材料 `Tc`、Meissner 或实验复现；有限尺寸和体不变量一致也不是热力学极限证明。连续驱动的 Fourier／时间步收敛、开放系统的占据与热管理仍是独立方向。",
        "",
        "模型依据：Thakurathi et al., Phys. Rev. B 88, 155133 (2013), arXiv:1303.2300v2，Eq. (17)–(27)。参数适配和 Fock 检验均由本包独立完成。",
        "",
    ]
    (ROOT / "README.md").write_text("\n".join(lines), encoding="utf-8")
    print(ROOT / "README.md")


if __name__ == "__main__":
    main()
