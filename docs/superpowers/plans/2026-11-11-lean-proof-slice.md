# Lean 最小真实证明切片实施计划

> 分支 `fix/lean-proof-slice`，禁止子代理。规格见 `2026-11-11-lean-proof-slice-design.md`。只写 `research/lean-proof-slice/` 和 D 盘隔离工具链；原文件只读。

**目标：** 用真实 Lean 4.35.0 验证三个定义展开，证明只用 `rfl`，并将新定理与原三条 `sorry` 定理的依赖分别记录。

**架构：** 官方 elan 哈希核验 → 固定 Lean／Mathlib → 原文件只读复制 → 真实编译与 `#print axioms` → 独立回归与报告。

## Assumptions

- 静态检查不是机器证明；任何工具或编译失败都保持 `unavailable`／`failed`，不生成成功结论。
- 三个定义展开不是三条物理命题的证明，也不改变材料预测和实验状态。
- 所有新代码和依赖均不修改系统 PATH，不新增公理、证明位 `sorry`、`admit` 或 `native_decide`。

### Task 1：冻结输入与失败合同

- [ ] 创建 `test_lean_slice.py` 和 `run.log`，固定原文件哈希、官方 elan 哈希、Mathlib 提交和三个定义展开目标。
- [ ] 合同覆盖新文件零债务、三个 `rfl`、原文件复制一致、真实编译退出码和新旧依赖差异。
- [ ] 在 `proof-slice.json` 不存在时运行主测试，确认 RED；零测试保护生效。

### Task 2：官方工具链隔离安装

- [ ] 创建 `bootstrap_elan.py`，下载官方 v4.2.4 Windows 资产到 D 盘，先验证 2508099 字节与 SHA-256 `fad2e980a191c15884cc1d80d170ffc5fa84f3774541020145b66d1a644c6111`。
- [ ] 验证后解压并调用 elan；`ELAN_HOME=D:/migration/toolchains/elan`，不修改系统 PATH，安装 `leanprover/lean4:v4.35.0`。
- [ ] 记录真实 `elan --version`、`lean --version`、工具链路径和退出码；任何失败保持机器验证不可用。

### Task 3：Mathlib、定义切片与真实编译

- [ ] 创建 `lakefile.toml`、`lean-toolchain`，固定 Mathlib `56a005855ea17e0b0958f73ec801ae140b0a1679`。
- [ ] 复制原文件为 `RoomTempSC_Formalization.lean`，SHA-256 必须等于 `1971e95d7b375c24778d3adae8a1ab3be4c5abeb1ee8b79a2b1f347b7aa00439`。
- [ ] 创建 `ProofSlice.lean`，仅三个 `rfl` 定义展开证明和 `#print axioms`，不调用原三条 `sorry` 定理。
- [ ] 获取固定依赖，优先 `lake exe cache get`；失败后保留错误并决定是否真实 `lake build`，不得跳过错误。
- [ ] 创建 `audit_lean.py`，执行真实编译并解析：新定理无 `sorryAx`，原三条定理保留 `sorryAx` 债务，生成 `proof-slice.json` 和 `PROOF_SLICE.md`。

### Task 4：fresh 回归与交付

- [ ] 重跑主合同和独立审计，验证原文件哈希、Lean／Mathlib 版本、编译退出码、依赖差异和零测试保护。
- [ ] 真实编译通过后才生成 `PROOF_SLICE.docx`，执行 OOXML 验证和最终视图逐页 QA；不可用则明确记录。
- [ ] `git diff --check` 退出 0，仅暂存本批，提交 `feat: add isolated Lean definition proof slice` 并推送具名分支，不合并主分支。
- [ ] 以 `docs: record Lean proof slice delivery` 记录交付；继续物理证明债务与实验复现，不把定义切片当作项目级证明。
