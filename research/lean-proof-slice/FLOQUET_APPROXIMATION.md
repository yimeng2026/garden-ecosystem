# Floquet 显式误差界与零误差双向证明

> 2026-11-11。**语义切片通过，不是 Floquet 增强证明。**

## 定义与证明

- `DriveApprox` 使用 `|ω_drive - 2 * Δ / ℏ| ≤ ε`，不构造 `HasEquiv` 实例。
- `driveApprox_zero_exact` 从零误差推出 `ω_drive = 2 * Δ / ℏ`。
- `driveApprox_of_exact` 从精确等式推出零误差界。
- 三个定理真实编译退出码为 0，均只依赖标准三公理，无 `sorryAx`。

| 定理 | 含义 | sorryAx | 公理依赖 |
|:--|:--|:--|:--|
| `driveApprox_unfold` | 定义展开 | 无 | propext, Classical.choice, Quot.sound |
| `driveApprox_zero_exact` | 零误差推出精确等式 | 无 | propext, Classical.choice, Quot.sound |
| `driveApprox_of_exact` | 精确等式推出零误差 | 无 | propext, Classical.choice, Quot.sound |

## 边界

原文件未修改，原文件直译仍不兼容，原三条定理的 `sorryAx` 审计仍不可用。Floquet 增强、物理有效性、材料预测、数值模型和实验验证均未验证。

本切片只清偿误差语义，不宣称 Floquet 增强或项目级证明完成。实际命令与原始输出见 `floquet-run.log`、`floquet-compile.log` 和 `floquet-approximation.json`。
