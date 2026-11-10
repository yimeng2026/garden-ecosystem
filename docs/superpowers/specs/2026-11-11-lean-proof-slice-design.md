# Lean 最小真实证明切片设计

日期：2026-11-11
分支：`fix/lean-proof-slice`
基线：`db7e1eb2e805f7b88ac4e92335840a0629f10a52`

## 目标

用真实 Lean 4.35.0 和固定 Mathlib 提交，在独立项目中验证原文件三个定义展开，分别检查新定理与原三条 `sorry` 定理的公理依赖。结果只表示“定义展开通过及依赖隔离”，不表示原物理定理、材料预测、数值模型或实验结论得到证明。

## 方案与禁止项

采用真实隔离编译。静态扫描不能替代机器验证；不得把三条物理 `sorry` 改成 `rfl`，不得新增 `axiom`、`postulate`、证明位 `sorry`、`admit`、`native_decide` 或跳过内核的选项。原文件只复制，不修改。

现有 `2026-11-09-lean-proof.md` 属于花园 API 项目，不能替代本切片的科学证明计划。

## 冻结来源与工具链

- 原始 Lean：`toe-sylva-audit/papers/room_temp_sc/room_temp_sc_Formalization.lean`，SHA-256 `1971e95d7b375c24778d3adae8a1ab3be4c5abeb1ee8b79a2b1f347b7aa00439`。
- 原文件现状：5 个定义、3 个定理、3 个证明位 `sorry`（第 93、112、185 行）。
- elan：官方 GitHub `leanprover/elan` v4.2.4，Windows 资产 `elan-x86_64-pc-windows-msvc.zip`，大小 2508099 字节，发布方给出的 SHA-256 `fad2e980a191c15884cc1d80d170ffc5fa84f3774541020145b66d1a644c6111`。
- Lean：`leanprover/lean4:v4.35.0`。
- Mathlib：标签 `v4.35.0`，固定提交 `56a005855ea17e0b0958f73ec801ae140b0a1679`。

下载、安装和依赖均隔离到 `D:/migration/toolchains/elan` 与项目 `.lake/`，不修改系统 PATH，不使用系统级包安装。官方资产先核验字节数与 SHA-256，再解压和执行；不符合即停止。

## 项目结构

`research/lean-proof-slice/` 包含：

- `RoomTempSC_Formalization.lean`：原文件的只读复制，哈希必须与原文件一致。
- `ProofSlice.lean`：只新增三个定义展开定理及 `#print axioms` 审计命令。
- `lakefile.toml`、`lean-toolchain`：固定 Lean 和 Mathlib。
- `audit_lean.py`、`test_lean_slice.py`：执行真实编译、解析依赖、静态否定合同和零测试保护。
- `proof-slice.json`、`PROOF_SLICE.md`、`run.log`：实际命令、退出码、原始输出和边界。
- 真实编译通过后再生成 `PROOF_SLICE.docx` 与视觉 QA；环境或编译失败时不得生成“机器验证通过”的报告。

## 三个定义展开定理

分别对 `allenDynesTc`、`h3s_tc_prediction`、`lah10_tc_prediction` 写出与定义右边项相等的定理，证明只允许 `rfl`。它们检查定义展开，不调用原三条含 `sorry` 的定理，不引入新的数值断言或物理结论。

`#print axioms` 同时作用于三个新定理和原三条定理：

- 新定理不得出现 `sorryAx`；若出现标准三公理之外的依赖，也必须单独解释，不能隐藏。
- 原三条定理应记录 `sorryAx`，作为已有债务证据，而不是删除或掩盖。
- 原文件的警告可以保留，但只有实际编译退出码为 0 且依赖解析满足合同，才可称该定义切片编译通过。

## 数据流与错误处理

先验证官方资产 → 安装固定 Lean → 获取固定 Mathlib 及依赖 → 复制并核验原文件 → 编译切片 → 解析依赖 → 运行独立回归 → 生成报告。任何网络、工具、编译、依赖解析或哈希失败均写入 `proof-slice.json` 和 `run.log`，并将机器验证状态保持为 `unavailable` 或 `failed`，不得生成成功结论。

依赖下载优先使用 `lake exe cache get`；缓存失败时保留原始错误，再决定是否执行真实 `lake build`。不得把跳过构建、忽略错误或只运行静态检查称为编译通过。

## 验收合同

1. 原文件与复制件哈希一致，原路径内容不变。
2. `ProofSlice.lean` 不含新的公理、证明位 `sorry`、`admit` 或 `native_decide`，只含三个 `rfl` 定义展开证明。
3. 真实 Lean 版本为 4.35.0，Mathlib 提交为固定值。
4. 编译退出码为 0；三个新定理无 `sorryAx`，原三条定理的 `sorryAx` 被如实记录。
5. 独立测试同时验证成功条件与这些否定边界，含零测试保护。
6. 最终报告明确区分定义编译、既有证明债务、物理有效性和实验验证；不宣称整个原文件或项目已证明。
