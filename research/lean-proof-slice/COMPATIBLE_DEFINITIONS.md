# Lean 兼容性清偿切片：常量、绑定与 Debye 类型

> 2026-11-11。**两个定义展开通过，不是物理证明。**

## 实际编译结果

- `bcsCriticalTemp` 使用 `Real.eulerMascheroniConstant`，不再使用未限定的 `eulerMascheroni`。
- `debyeModel` 显式给出 `ω₀ : ℝ` 与 `ℝ → ℝ` 函数类型，输入 `M : ℝ` 时返回 `ω₀ / Real.sqrt M`。
- ASCII `lam` 继续沿用前述清洁定义切片；本文件没有 `HasEquiv`。
- 两个 `rfl` 展开定理真实编译退出码为 0，均只依赖标准三公理，无 `sorryAx`。

| 定理 | 编译 | sorryAx | 公理依赖 |
|:--|:--|:--|:--|
| `bcsCriticalTemp_unfold` | 退出码 0 | 无 | propext, Classical.choice, Quot.sound |
| `debyeModel_unfold` | 退出码 0 | 无 | propext, Classical.choice, Quot.sound |

## 开放边界

原文件未修改，原文件直译仍不兼容，原三条定理的 `sorryAx` 审计仍不可用。`HasEquiv ℝ` 的命题语义保持开放，不能通过构造实例强行通过。

本切片不证明弱耦合极限、同位素比值或 Floquet 增强，不验证物理有效性、材料预测、数值模型或实验复现。实际命令与原始输出见 `compatible-run.log`、`compatible-compile.log` 和 `compatible-definitions.json`。
