"""Build the complete benchmark report directly from verified result files."""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
results = json.loads((ROOT / "surface-code-threshold" / "results.json").read_text(encoding="utf-8"))
verification = json.loads((ROOT / "surface-code-threshold" / "verification.json").read_text(encoding="utf-8"))
points = results["points"]
summary = results["crossing_summary"]
assert len(points) == 28
assert sum(point["shots"] for point in points) == 560000
assert verification["status"] == "pass" and not verification["mismatches"] and not verification["csv_mismatches"]
assert all(point["errors"] > 0 for point in points)


def pct(value):
    return f"{100 * value:.4f}%"


lines = [
    "# 表面码真实电路级蒙特卡洛阈值基准",
    "",
    "**性质**：独立 Stim＋PyMatching 基准；不是对原稿缺失模拟的重建，也不是硬件实验。",
    "**协议 SHA-256**：`" + results["protocol_sha256"] + "`",
    "**结论边界**：交叉估计仅适用于本报告冻结的电路级噪声与 MWPM 解码，不是有限尺寸标度拟合或宇宙级通用阈值。",
    "",
    "## 直接结论",
    "",
    f"28 个网格点全部得到非零真实逻辑错误计数，合计 **560,000 shots**。六组成对码距曲线均发生交叉，交叉中位数为 **{pct(summary['median'])}**，观察范围为 **{pct(summary['minimum'])}–{pct(summary['maximum'])}**。该范围是不同码距对插值交叉的离散程度，不是统计置信区间。",
    "",
    "这一结果与 PyMatching 文档中相近电路级噪声配置约 0.7% 的示例一致。原稿的 1.03% 属于另一套尚未公开的噪声与解码配置，不能用本结果直接判错；但原稿也没有资格继续在没有原始 shots、探测器错误模型和种子的条件下声称已经完成大规模蒙特卡洛。",
    "",
    "![图1：四种码距在电路级噪声下的真实逻辑错误率与 Wilson 95% 区间](surface-code-threshold/threshold.png)",
    "",
    "**图1定位**：置于直接结论之后。每个点都来自实际 Stim 采样和 PyMatching 解码，误差棒为 Wilson 95% 区间，纵轴为每个 shot 的逻辑错误率（对数坐标）。",
    "",
    "## 冻结协议与复现命令",
    "",
    "- 电路：`surface_code:rotated_memory_x`；码距 `d∈{3,5,7,9}`，`rounds=d`。",
    "- 概率：`p∈{0.004,0.005,0.006,0.007,0.008,0.009,0.010}`。",
    "- 噪声：Clifford 后、轮次数据、复位和测量四路均使用同一 `p` 的退极化／翻转错误。",
    "- 解码：`detector_error_model(decompose_errors=True)` 后使用 PyMatching MWPM。",
    "- 每点：20,000 shots；种子为 `20261110 + 1000*d + 概率索引`。",
    f"- 环境：Python {results['dependencies']['python']}、Stim {results['dependencies']['stim']}、PyMatching {results['dependencies']['pymatching']}、NumPy {results['dependencies']['numpy']}。",
    "",
    "```bash",
    "PYTHONPATH=research/paper-direction-audit-2026-11-10/scripts .tools/qec-venv/Scripts/python research/paper-direction-audit-2026-11-10/scripts/run_surface_code_threshold.py",
    "PYTHONPATH=research/paper-direction-audit-2026-11-10/scripts .tools/qec-venv/Scripts/python research/paper-direction-audit-2026-11-10/scripts/verify_surface_code_threshold.py",
    "PYTHONPATH=research/paper-direction-audit-2026-11-10/scripts .tools/qec-venv/Scripts/python research/paper-direction-audit-2026-11-10/scripts/plot_surface_code_threshold.py",
    "```",
    "",
    "三条命令的实际退出码均为 **0**。独立复验输出 `status: pass`、`mismatches: []`、`csv_mismatches: []`。另执行 13 项回归测试，覆盖统计边界、真实零噪声、同种子复现、独立输出复验和 SVG 标签，全部通过。",
    "",
    "## 全部真实网格结果",
    "",
    "| 码距 d | 物理错误率 p | 逻辑错误 shots | 总 shots | 逻辑错误率 | Wilson 95% 区间 |",
    "|---:|---:|---:|---:|---:|---:|",
]
for point in points:
    lines.append(f"| {point['distance']} | {point['p']:.3f} | {point['errors']} | {point['shots']} | {pct(point['rate'])} | {pct(point['wilson95_low'])}–{pct(point['wilson95_high'])} |")
lines.extend([
    "",
    "## 成对曲线交叉",
    "",
    "对每个码距对的 `log10(p_L)` 做分段线性插值并求交点。六对均有交叉，未跳过任何码距对。",
    "",
    "| 码距对 | 插值交叉 p |",
    "|---|---:|",
])
for crossing in summary["crossings"]:
    lines.append(f"| d={crossing['pair'][0]} 与 d={crossing['pair'][1]} | {pct(crossing['p'])} |")
lines.extend([
    "",
    "## 对论文三的具体修订要求",
    "",
    "1. **把噪声模型写全。** 不能只写“独立 Pauli 错误”。必须明确是码容量、现象学还是电路级噪声，是否包含测量、复位、Clifford 和数据空闲错误，以及每一路的概率。",
    "2. **公开原始证据。** 上传逐点 shots、DEM、解码配置、种子和有限尺寸标度输入；不能再用预设标度公式代替蒙特卡洛。",
    "3. **统一数值。** 原稿摘要的 `1.03±0.05%` 与结论的 `1.03±0.06%` 必须给出同一拟合协议与置信区间来源。",
    "4. **分离外部实验与本仓库模拟。** Google d=7、101 比特、0.143%／周期是真实硬件结果，不是本仓库模拟的验证标签。",
    "5. **保留新基准的边界。** 本次中位数约 0.6725% 不是对 1.03% 的普遍否定；只有按原稿完整协议复算后，才能裁决其原始数值是否可复现。",
    "",
    "## 下一阶段",
    "",
    "下一阶段应扩展码距与 shots，实施显式有限尺寸标度拟合和参数不确定度传播，再把同一框架用于颜色码、qLDPC 和其他解码器。当前报告没有覆盖这些码族，也没有执行真实硬件、相关噪声、泄漏或逻辑门实验。",
    "",
    "机器可读证据：[协议](surface-code-threshold/protocol.json)、[结果 JSON](surface-code-threshold/results.json)、[结果 CSV](surface-code-threshold/results.csv)、[独立复验](surface-code-threshold/verification.json)。",
    "",
])
(ROOT / "SURFACE_CODE_BENCHMARK.md").write_text("\n".join(lines), encoding="utf-8", newline="\n")
summary_payload = {
    "points": len(points),
    "total_shots": sum(point["shots"] for point in points),
    "crossing_median": summary["median"],
    "crossing_minimum": summary["minimum"],
    "crossing_maximum": summary["maximum"],
    "verification": verification["status"],
    "protocol_sha256": results["protocol_sha256"],
}
(ROOT / "surface-code-threshold" / "report-summary.json").write_text(
    json.dumps(summary_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
print(json.dumps(summary_payload, ensure_ascii=False, indent=2))
