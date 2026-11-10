# 理论框架与突破详解审计实施计划

> 在当前隔离工作树执行，禁止子代理。先 RED 后 GREEN；所有完成声明必须来自当次命令、退出码和关键输出。

**目标：** 闭合 `03-理论框架` 与 `06-突破详解` 的证据角色，识别四个可发展方向及其未竟工作，不修改原文、不制造证明或实验完成状态。

**架构：** Python 构建器冻结四个来源、独立扫描理论原文并读取既有审计对象，生成唯一 `review.json`、逻辑／实验双面板图和 Markdown。独立来源测试不依赖构建器结论。docx-js 从同一 JSON 和 PNG 生成原生 Word，最终经 OOXML 与逐页视觉验收。

**技术：** Python 3 标准库、unittest、Matplotlib、docx-js、原生 Math API、kimi-word 验证与 doc-k 最终视图。

## Assumptions

- 两份原文位于工作区 `toe-sylva-audit`，只读；所有新文件写入当前工作树。
- PNAS、Song、Semenok 和临界流形的证据角色复用已回源的 `main-claims/review.json`，本批不重复宣称新做外部事实核查。
- 理论 Markdown 是伪代码草案；本批做文本与逻辑审计，不声称 Lean 编译成功或失败。
- 模块检索无命中仅表示本次仓库范围未解析，不证明其他位置不存在实现。
- 自动持续推进模式下，设计中的范围与否定边界即为执行约束，不另行扩大任务。

## 冻结哈希

- `theory_framework`：`c53b9b8fbab8018e3e2948e8ecff71d0232dd47e60c8a86f4281e58200c262fb`
- `breakthrough_report`：`7d9711df200880690a82c814380e4392f35a1ca3c6df957cabe6607678ba00ce`
- `main_claims_review`：`e9ac6ff0bc88f11b1c2c91ae61ce398a05fc077815803f48669b46536d6f2f45`
- `methods_review`：`f30d15d8665644d11957166efaea95d59f7a742037dc697b737704cd15dc9e21`

---

### Task 1：规格、计划与失败合同

**文件：**
- 创建 `research/paper-direction-audit-2026-11-10/theory-breakthrough/test_theory_breakthrough_audit.py`
- 创建 `research/paper-direction-audit-2026-11-10/theory-breakthrough/run.log`

- [x] 写主合同，覆盖四个哈希、一个研究纲领、四个方向、17 处 `admit`、5 处 `sorry`、5 个模块引用、单点到全称非推论、298<300、预测／实验分轨、13 次运行边界、日期矛盾、六个开放边界、Markdown 和原生 Word 结构。
- [x] Word 合同要求 `m:oMath`、TOC、至少四个 `w:tbl`、PAGE、中文页眉、图片、`word/footnotes.xml`，以及 `01-理论框架.md`、`critical_manifold/results.json`、`2401840121`、`2510.01273`、`2605.29985` 五个来源标识。
- [x] 两个测试套件都使用 `run_all_tests()`，零测试发现返回非零。
- [x] 运行主合同，记录预期 `FileNotFoundError: review.json` 和退出码 1。
- [x] 提交规格、计划和失败合同：`test: define theory and breakthrough audit contracts`。

### Task 2：统一证据对象、独立检查与双面板图

**文件：**
- 创建 `build_review.py`、`numeric_and_text_checks.py`、`verify_sources.py`
- 生成 `review.json`、`logic-evidence-map.svg/.png`、`REVIEW.md`

- [x] `numeric_and_text_checks.py` 独立读取理论原文，使用 `^\s*admit\b` 与 `^\s*sorry\b` 统计 17／5；读取突破原文，核对 298、316、13 次、P6/mmm、准二维和日期文本。
- [x] `build_review.py` 冻结四来源，读取既有审计的 Song onset `[271,298]`、PNAS 预测 316/331、Semenok 七次未成功和临界流形锚点。记录五个模块引用及仓库检索结果，不将未命中升级为绝对不存在。
- [x] 设置 `admit_count=17`、`sorry_count=5`、`existence_to_universal_valid=false`、`continuity_bridges_universal=false`、`p6mmm_implies_quasi_2d=false`、`mechanism_verified_by_structure_and_tc=false`、`author_runs_equal_independent_labs=false`、`metadata_date_precedes_cited_preprint=true`。
- [x] 六项边界保持 false：形式证明、Lean 模块解析、实验必然性证明、独立正向复现、直接 Meissner、全库审计。
- [x] 图左面板展示“假设→单点存在→普遍必然”的断点，右面板并列 PNAS 预测、Song 正向预印本、Semenok 负向复现和缺失的独立验证。不得制作成功率或证明完成百分比。
- [x] Markdown 必须含“17 处 admit”“5 处 sorry”“298 K 低于 300 K”“图 1”“全库审计尚未完成”，并说明图件位于证据角色表之后、结果解释之前。
- [x] `verify_sources.py` 独立复算文本计数、298<300、文档日期先于 2025-10、既有审计中的正负实验角色及数值锚点。运行两个套件，预期主合同仅剩 DOCX 缺失。

### Task 3：原生 Word 与最终视图

**文件：**
- 创建 `build_report.js`、`.gitignore`、`.gitattributes`
- 生成 `REVIEW.docx`、`word-qa/report.json`

- [x] 使用 A4、显式 CJK 字体、中文页眉、PAGE-only 页脚、真实 TOC 域及可见缓存目录、稳定 DXA 表格。
- [x] 用 `MathSubScript` 构造 \(T_c\)，用原生 MathRun 表达“单点存在不能推出全称必然”；不得用图片替代公式。
- [x] 至少五个真实表格：方向、证明债务、实验角色、勘误、开放边界。插入 PNG 于实验角色表之后、结果解释之前，保持自然宽高比。
- [x] 五条原生脚注定位理论原文、既有临界流形结果、PNAS、Song、Semenok。
- [x] `check-docx` 后使用 `docx.py build`，运行两个测试套件。
- [x] 对最终 DOCX 执行一次 doc-k 渲染；先读 contact sheet，再读全部页面、content-loss 和 near-blank 项。若修改最终文件，需对修改后的文件重新验收。退出 4/5/6 不重试，不使用 LibreOffice。
- [x] 将实际页数、逐页观察、渲染器限制、最终 SHA-256 写入 `word-qa/report.json`，所有实际命令和退出码写入 `run.log`。

### Task 4：fresh 回归与具名分支交付

- [x] 重跑两个测试套件、JSON 解析、DOCX 哈希一致性、`docx.py validate` 和 `git diff --check`，全部退出 0。
- [x] Matplotlib SVG 如产生行尾空格，使用本目录 `.gitattributes` 的 `whitespace=-trailing-space` 保留证据，不改写路径数据。
- [ ] 仅暂存本批文件和计划，不混入其他目录的未跟踪资料。
- [ ] 提交 `docs: audit theory framework and breakthrough evidence`，推送 `audit/room-temp-theory-breakthrough`。
- [ ] 用 `git rev-parse HEAD` 与 `git ls-remote` 核对哈希；记录交付状态，不合并主分支。
- [ ] 本批只闭合两份文档；继续其余 30 份 room_temp_sc 文档，保持全库目标 active。

## 计划自审

每一步都有具体文件、接口、否定边界和实际验证命令。证据对象同时服务 Markdown、图件和 Word；文本债务、逻辑跳跃、实验争议和元数据矛盾分别可检验，不会将审计升级为形式证明、材料预测或实验复现。
