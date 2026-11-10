# Lean 原文件兼容性勘误：四类开放问题

> 2026-11-11。只登记错误和清偿动作，不修改原文件，不宣称修复或物理证明。

## 真实编译边界

原文件 SHA-256：`1971e95d7b375c24778d3adae8a1ab3be4c5abeb1ee8b79a2b1f347b7aa00439`。直接编译退出码为 1，原始日志为 `original-compile.log`。

| 问题 | 直接证据 | 当前状态 | 清偿动作 |
|:--|:--|:--|:--|
| `euler_mascheroni` | Unknown identifier `eulerMascheroni` | **open／未解决** | 将未限定的 eulerMascheroni 改为经 Mathlib 源码确认存在的 Real.eulerMascheroniConstant，并核对所需 import 与数值语义。 |
| `lambda_identifier` | unexpected token 'λ' | **open／未解决** | 将绑定变量 λ 改为 ASCII lam，保持公式参数顺序与物理含义不变。 |
| `omega_d_binding` | ω_D is unknown and autoImplicit cannot infer a function type | **open／未解决** | 显式声明 ω_D : ℝ → ℝ 与 ω₀ : ℝ 的类型、单位和物理定义，禁止依赖 autoImplicit 猜测。 |
| `has_equiv_real` | failed to synthesize instance of type class HasEquiv ℝ | **open／未解决** | 不构造虚假实例；将约等号命题改写为等式、极限或显式误差估计，并注明近似条件。 |

## 执行顺序

1. 先修常量、绑定变量和显式类型，使最小定义可解析；不得用 autoImplicit 猜测物理函数。
2. 再处理约等号的命题语义：等式、极限或显式误差估计三选一，不能为了通过编译构造虚假 `HasEquiv ℝ` 实例。
3. 每项修复都必须以真实 Lean 命令、退出码和公理依赖审计验收；未通过前保持 `open`。
4. 清洁定义切片继续独立保留，不把其成功当作原文件或三条物理定理的证明。

原文件未修改，未新增公理、证明位 `sorry` 或物理结论。物理有效性、材料预测和实验验证仍未解决。
