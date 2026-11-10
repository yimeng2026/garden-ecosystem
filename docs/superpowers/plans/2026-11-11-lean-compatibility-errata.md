# Lean 原文件兼容性勘误实施计划

> 分支 `fix/lean-compatibility-errata`，禁止子代理。只写勘误与验证，不修改原证明、不新增公理或证明位 `sorry`。

**目标：** 将四类真实编译错误绑定直接日志、实际常量／标识符、状态和清偿动作，形成可机检的后续工作入口。

### Task 1：失败合同

- [x] 创建 `test_compatibility_errata.py` 与 `compatibility-run.log`，固定原文件哈希和四类错误。
- [x] 确认缺少 `compatibility-issues.json` 时 RED，零测试保护生效。

### Task 2：勘误证据与独立复核

- [x] 创建 `build_compatibility_errata.py`，生成四项 `open` 记录、实际错误标记、下一步和双边界。
- [x] 明确 `Real.eulerMascheroniConstant`、ASCII `lam`、显式 `ω_D : ℝ → ℝ`／`ω₀ : ℝ`，以及不构造虚假 `HasEquiv ℝ` 实例。
- [x] 创建 `verify_compatibility_errata.py`，直接复核原文件哈希、日志标记、状态和未修复边界。
- [x] 生成 `COMPATIBILITY_ERRATA.md`，主合同此阶段只允许 Word 缺失。

### Task 3：原生 Word 与验收

- [x] 创建 `build_compatibility_report.js`，真实 TOC、中文页眉、PAGE-only 页脚、至少三个表格和准确来源脚注。
- [x] 执行 OOXML 验证与最终视图；退出 4／5／6 不重试、不用 LibreOffice，记录实际视觉状态。

### Task 4：交付

- [x] 重跑两套测试、JSON 解析、原文件哈希和 `git diff --check`，全部退出 0。
- [x] 提交 `docs: add Lean compatibility errata` 并推送具名分支，不合并主分支。
- [x] 以 `docs: record Lean compatibility errata delivery` 记录交付；继续真实证明与实验复现，保持全库目标 active。
