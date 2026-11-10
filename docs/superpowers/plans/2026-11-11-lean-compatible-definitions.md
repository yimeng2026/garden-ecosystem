# Lean 兼容性清偿切片实施计划

> 分支 `fix/lean-compatible-definitions`，禁止子代理。规格见 `2026-11-11-lean-compatible-definitions-design.md`。只新增独立定义和验证，不修改原文件。

**目标：** 真实编译 `bcsCriticalTemp` 与 `debyeModel`，验证 Euler 常量、ASCII `lam` 和显式 Debye 类型，保留 `HasEquiv ℝ` 与物理证明为开放工作。

### Task 1：失败合同

- [ ] 创建 `test_compatible_definitions.py` 与 `compatible-run.log`，固定原文件哈希、两个定义、两个 `rfl` 和禁止项。
- [ ] 确认 `compatible-definitions.json` 缺失时 RED，零测试保护生效。

### Task 2：独立定义与真实编译

- [ ] 创建 `CompatibleDefinitions.lean`：`Real.eulerMascheroniConstant`、显式 `ω₀ : ℝ`、返回 `ω₀ / Real.sqrt M` 的 `debyeModel`，不包含 `HasEquiv`。
- [ ] 仅添加 `bcsCriticalTemp_unfold` 和 `debyeModel_unfold` 两个 `rfl` 证明及 `#print axioms`。
- [ ] 创建 `audit_compatible_definitions.py`，在 D 盘固定工具链中编译并解析依赖，生成 `compatible-definitions.json` 和 `COMPATIBLE_DEFINITIONS.md`。
- [ ] 创建 `verify_compatible_definitions.py`，独立复核原文件哈希、常量、类型、禁止声明、退出码和开放边界。

### Task 3：原生 Word 与验收

- [ ] 创建 `build_compatible_report.js`，真实 TOC、中文页眉、PAGE-only 页脚、至少三个表格和准确来源脚注。
- [ ] 执行 OOXML 验证与最终视图；退出 4／5／6 不重试、不用 LibreOffice，记录实际视觉状态。

### Task 4：交付

- [ ] 重跑两套测试、JSON 解析、原文件哈希和 `git diff --check`，全部退出 0。
- [ ] 提交 `feat: add Lean compatible definition slice` 并推送具名分支，不合并主分支。
- [ ] 以 `docs: record Lean compatible definitions delivery` 记录交付；继续 `HasEquiv` 语义、物理证明和实验复现，保持全库目标 active。
