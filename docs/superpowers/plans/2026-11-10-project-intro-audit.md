# 目录、项目介绍与 44 份覆盖图审计计划

> 复用现有隔离工作树，分支 `audit/room-temp-project-intro`，禁止子代理和嵌套工作树。先 RED 后 GREEN；原文只读，所有完成声明绑定命令与退出码。

**目标：** 完成最后 4 份文档审计，生成无重复、无遗漏的 44 份覆盖图，并把目录、形式化、手册、参考文献和公众传播的未竟工作转成可验收任务。

**架构：** 从十份既有 `review.json` 的只读来源重建 40 份覆盖，再加入本批 4 份并与实际 44 个 Markdown 路径对比；独立检查文献、Lean、版本和手册资产；统一生成报告与原生 Word。

## Assumptions

- 覆盖完成只针对 `organized/` 的 44 份 Markdown，不表示整个仓库或全部科学任务完成。
- 每篇共享批次方向，不把共享方向自动升级为单篇独立首创或新理论。
- 原 README 与原手册只作版本和资产证据，不重新展开其全部科学内容。

### Task 1：规格与失败合同

- [ ] 固定 19 项来源、4 份新审计、40＋4＝44 覆盖、4 方向和 12 项勘误。
- [ ] 固定目录遗漏、PRL、24／0 条 BibTeX、5 处占位、Lean／模块缺失、版本与时间矛盾、手册元数据。
- [ ] 两套测试含零测试保护；主测试在缺少 `review.json` 时按预期 RED。

### Task 2：覆盖清单与独立复核

- [ ] 创建 `inspect_sources.py`，从十批来源生成 40 份覆盖，加入本批 4 份，检查唯一性、遗漏、方向和评审哈希。
- [ ] 创建 `verify_primary_sources.py`，直接复核目录、文献条目、占位、Lean、README、日期与原手册元数据。
- [ ] 创建 `build_review.py`，生成 `review.json`、`REVIEW.md` 和覆盖／资产证据图。
- [ ] 主合同此时仅允许 Word 缺失；独立测试通过。

### Task 3：原生 Word 与逐页验收

- [ ] 创建 `build_report.js`，A4、CJK、真实 TOC、中文页眉、PAGE-only 页脚、原生公式、至少七个表格、图件和来源脚注。
- [ ] 明确 44 份逐文档覆盖、4 份逐篇裁决、12 项勘误及“覆盖完成／研究未闭合”双边界。
- [ ] 构建后两套测试通过；最终视图先读联系表再逐页检查，退出 4／5／6 不重试、不用 LibreOffice。
- [ ] 记录页数、逐页观察、版式修正、渲染限制和 DOCX SHA-256。

### Task 4：回归、交付与全库裁决

- [ ] fresh 运行两套测试、JSON、覆盖唯一性、DOCX 哈希、`docx.py validate` 和 `git diff --check`，全部退出 0。
- [ ] 提交 `docs: complete organized paper direction coverage` 并推送具名分支，核对远端哈希，不合并主分支。
- [ ] 以 `docs: record organized coverage delivery` 记录交付。
- [ ] 仅在 44 份覆盖、报告和验证全部闭合后更新目标状态；科学未竟工作保留为后续研究方向，不虚报完成。
