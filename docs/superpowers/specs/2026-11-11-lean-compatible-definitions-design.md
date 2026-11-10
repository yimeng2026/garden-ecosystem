# Lean 兼容性清偿切片：常量、绑定与显式 Debye 类型设计

日期：2026-11-11
分支：`fix/lean-compatible-definitions`
基线：`cc6a1b5532c19232bc530340ec7dac66d4861cd9`

## 目标与范围

在独立模块中清偿三类已定位问题：未限定的 `eulerMascheroni`、希腊字母 `λ` 绑定、未显式声明的 Debye 函数与常量类型。保留原文件、原始错误日志和四项 `open` 勘误，不直接修改原证明。

本切片不包含 `HasEquiv ℝ`，不处理约等号的命题形式，不证明弱耦合极限、同位素比值或 Floquet 增强，不断言物理有效性、材料预测或实验验证。

## 方案选择

采用独立兼容模块。直接修改原文件违反只读证据约束；构造 `HasEquiv ℝ` 实例会掩盖命题语义并可能形成假证明，因此均不采用。已有的清洁定义切片继续作为 ASCII `lam` 的证据，新模块只补足 Euler 常量和 Debye 类型。

## 模块职责

`research/lean-proof-slice/CompatibleDefinitions.lean` 只承担两项定义：

1. `bcsCriticalTemp`：使用经当前 Mathlib 源码确认的 `Real.eulerMascheroniConstant`，不再使用未限定的 `eulerMascheroni`。
2. `debyeModel`：以显式 `ω₀ : ℝ` 定义类型为 `ℝ → ℝ` 的函数，输入 `M : ℝ` 时返回 `ω₀ / Real.sqrt M`。这给出了 `ω_D : ℝ → ℝ` 的明确函数类型与参数，而不是依赖 `autoImplicit` 推断。

只新增两个定义展开定理：`bcsCriticalTemp_unfold` 与 `debyeModel_unfold`，证明只允许 `rfl`，并执行 `#print axioms`。它们检查定义与展开的一致性，不是 BCS 或同位素效应的物理证明。

## 数据与证据流

原文件哈希和原始失败日志 → 三项兼容性问题 → 独立两个定义 → 真实 Lean 4.35.0 编译与依赖输出 → `compatible-definitions.json`、Markdown、Word 和验证记录。

原文件与复制件的 SHA-256 必须继续等于 `1971e95d7b375c24778d3adae8a1ab3be4c5abeb1ee8b79a2b1f347b7aa00439`。Lean 和 Mathlib 继续使用已安装的 D 盘固定工具链，Mathlib 提交为 `56a005855ea17e0b0958f73ec801ae140b0a1679`。

## 错误处理

- 若正确常量或 Debye 定义仍无法编译，状态保持 `failed`，不生成成功结论。
- 若原文件哈希变化，立即停止。
- 不新增 `axiom`、`postulate`、证明位 `sorry`、`admit`、`native_decide` 或 `HasEquiv` 实例。
- 不把原三条定理的 `sorryAx` 审计写成真或假；原文件直接编译不可用时保持“不可用”。
- 视觉验收不可用时，只记录 OOXML 和测试门，不声称视觉通过。

## 验收合同

1. 两个新定义均存在，Euler 常量名和 Debye 类型准确，未引入 `HasEquiv`。
2. 新文件只有两个 `rfl` 证明，无禁止声明；真实编译退出码为 0。
3. 两个新定理无 `sorryAx`，除标准三公理外无额外依赖。
4. 独立测试验证原文件未变、两个定理、原始错误仍存在、三项局部清偿与 `HasEquiv` 开放边界。
5. 报告明确：本切片只完成局部定义兼容清偿，不表示原文件、物理定理、材料预测或实验复现完成。
