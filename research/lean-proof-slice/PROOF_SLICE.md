# Lean 独立清洁定义切片：真实编译与边界

> 2026-11-11。**定义展开通过，不是物理证明。**

## 实际结果

- Lean 4.35.0 与固定 Mathlib `56a005855ea17e0b0958f73ec801ae140b0a1679` 已在 D 盘隔离运行。
- 三个清洁定义展开定理编译退出码为 0；每个仅依赖 `propext`、`Classical.choice`、`Quot.sound`，没有 `sorryAx` 或额外公理。
- 原文件直接编译失败，存在 `eulerMascheroni` 未定义、希腊字母 `λ` 标识符错误、`ω_D` 未绑定和 `HasEquiv ℝ` 缺失。
- 原文件仍有 3 处既有 `sorry`（第 93、112、185 行）；由于编译失败，原三条定理的 `sorryAx` 审计不可用，不能伪造该结果。

## 三个定义展开

| 定理 | 编译 | sorryAx | 公理依赖 |
|:--|:--|:--|:--|
| `allenDynesTc_unfold` | 退出码 0 | 无 | propext, Classical.choice, Quot.sound |
| `h3s_tc_prediction_unfold` | 退出码 0 | 无 | propext, Classical.choice, Quot.sound |
| `lah10_tc_prediction_unfold` | 退出码 0 | 无 | propext, Classical.choice, Quot.sound |

## 明确边界

本次只验证三个清洁定义的展开，不调用原三条物理定理，不证明其弱耦合极限、同位素效应或 Floquet 增强命题。原文件复制件哈希与原文件一致，原文件未修改。

物理有效性、材料预测、数值模型和实验验证均未验证。Mathlib 的版本差异和原文件语法错误必须另行处理，不能用本次切片替代。

实际命令、原始输出和退出码见 `run.log`、`original-compile.log`、`clean-compile.log` 与 `proof-slice.json`。
