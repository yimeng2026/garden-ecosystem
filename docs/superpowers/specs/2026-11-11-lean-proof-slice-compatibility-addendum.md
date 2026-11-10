# Lean 切片兼容性补充：从原文件直译到独立清洁定义

日期：2026-11-11

## 变更原因

原设计希望直接编译只读复制的 `RoomTempSC_Formalization.lean` 并对原三条定理执行 `#print axioms`。真实 Lean 4.35.0 编译证明该目标当前不成立：原文件同时存在 `eulerMascheroni` 未定义、希腊字母 `λ` 的标识符错误、`ω_D` 未绑定和 `HasEquiv ℝ` 实例缺失。继续修改原文件会违反只读约束。

## 修订后的交付语义

- 原文件和复制件保持哈希一致，直接编译状态为 `source_incompatible`，原始日志为 `original-compile.log`。
- 原三条定理的 `sorryAx` 审计为“不可用”，不是真或假；静态扫描仍记录第 93、112、185 行三处 `sorry`。
- `ProofSlice.lean` 不再导入原模块，只含三个独立清洁定义和三个 `rfl` 展开证明。
- 清洁切片真实编译退出码为 0，三个新定理只依赖 `propext`、`Classical.choice`、`Quot.sound`，无 `sorryAx` 或额外公理。
- `Mathlib.Analysis.SpecialFunctions.Log.lean` 只转发 `Log.Basic`，属于独立兼容导入层，不修改 Mathlib 源码；其 `.olean` 只作为构建产物生成。
- 清洁定义不等于原文件直译成功，不等于物理命题、材料预测、数值模型或实验验证通过。

## 构建与验证边界

官方 elan 资产已按发布方大小和 SHA-256 验证。Lean、Lake、Mathlib、缓存与构建副本均放在 D 盘。依赖首次写入 C 盘时发生空间不足；通过 D 盘缓存和独立构建副本解决。临时副本的 Git 元数据问题通过重新获取干净依赖解决，没有修改原仓库历史或源目录权限。

Lake 库目标会遮蔽真实 `Log.Basic`，因此最终编译使用直接 Lean 调用和明确的 `.olean` 输出路径，不再注册兼容库目标。自动审计使用固定 Windows 可执行路径，避免 Bash／Windows PATH 格式差异。

最终 Word 通过 OOXML 校验和 7 项主合同。最终视图渲染因临时目录权限失败（退出码 6），按规则不重试、不使用 LibreOffice，视觉验收状态为 `unavailable`，`visualPassClaimed=false`。交付依据是实际 Lean 编译、独立审计和 OOXML 验证门，而不是结构检查冒充视觉检查。
