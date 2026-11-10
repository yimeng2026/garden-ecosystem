# Organized 导航与参考文献修复包实施计划

> 分支 `fix/organized-navigation-references`，复用现有隔离工作树，禁止子代理。规格见 `2026-11-10-organized-remediation-design.md`。先 RED 后 GREEN；原始证据只读。

**目标：** 生成真实 44 份导航、44 行 CSV、27 条可解析 BibTeX、独立验证和原生 Word 修复报告，闭合导航与引用交付的局部缺口。

**架构：** 从冻结覆盖清单生成导航，从旧 24 条和三条已核实记录生成新库；统一写入 `remediation.json`，独立脚本检查所有结果，再生成图件与 Word。

## Assumptions

- 新文件只写入 `research/organized-remediation/`；不修改原目录和旧 BibTeX。
- 27 条表示可解析交付，不表示全部回源或全部可信；5 个待补区块继续披露。
- PNAS、Song、Semenok 分属理论预测、作者正向预印本和独立负向预印本，不互相替代。

### Task 1：失败合同

- [ ] 创建 `test_remediation.py` 与 `run.log`，固定输入哈希、44 路径、27 条、三条标识、5／6 占位口径和非完成边界。
- [ ] 合同检查 00–21 全组、无 PRL 成品、44 行 CSV、27 个唯一 key、旧 24 条前缀逐字保留、审计链接存在。
- [ ] Word 合同包含真实 TOC、OMML、至少五个表格、PAGE、中文页眉、图件和来源脚注。
- [ ] 运行主测试，确认因 `remediation.json` 缺失而 RED；零测试保护生效。

### Task 2：生成修复资产与独立验证

- [ ] 创建 `build_remediation.py`，生成 `INDEX.md`、`coverage.csv`、`references_repaired.bib`、`remediation.json` 和对照图。
- [ ] 旧 24 条作为新库前缀逐字保留，追加 PNAS／Song／Semenok 三条唯一记录；写入各自证据角色注释。
- [ ] 创建 `verify_remediation.py`，独立检查 44 路径与哈希、00–21、27 key、三条标识、旧前缀、5／6 占位、链接和原始输入未改。
- [ ] 主合同此阶段只允许 Word 缺失；独立测试退出 0。

### Task 3：原生 Word 与视觉验收

- [ ] 创建 `build_report.js`，A4、CJK、真实 TOC、中文页眉、PAGE-only 页脚、OMML、至少五个表格、图件和准确来源脚注。
- [ ] 对照图呈现 44 路径、24＋3＝27、5 个待补区块和“可解析≠全部回源”；图件位于整改资产表之后、剩余边界之前。
- [ ] 构建后两套测试通过；最终视图先读联系表再逐页检查，退出 4／5／6 不重试、不用 LibreOffice。
- [ ] 记录实际页数、逐页观察、目录缓存、渲染限制和 DOCX SHA-256。

### Task 4：fresh 回归与交付

- [ ] 两套测试、JSON／CSV／BibTeX 解析、原输入哈希、DOCX 哈希、`docx.py validate` 和 `git diff --check` 全部退出 0。
- [ ] 仅暂存修复包与计划，提交 `feat: add organized navigation and reference remediation`。
- [ ] 推送 `fix/organized-navigation-references`，核对远端哈希，不合并主分支。
- [ ] 以 `docs: record organized remediation delivery` 记录交付；随后推进 Lean 与实验复现未竟工作，保持全库目标 active。
