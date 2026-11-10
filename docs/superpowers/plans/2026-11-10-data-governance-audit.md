# 总览与技术复盘数据治理审计实施计划

> 复用现有隔离工作树，分支 `audit/room-temp-data-governance`，禁止子代理。先 RED 后 GREEN；原文只读，完成声明必须来自实际命令与退出码。

**目标：** 建立原始证据、单篇审计与多份总览之间的纠错传播链，形成事实血缘、基准范围、数据完整性和动态更新四个方向。

**架构：** 十二项冻结来源驱动 `review.json`；独立测试核对 HTSC、Song、Patsnap、B–C 和既有审计；Python 生成双面板图和 Markdown；docx-js 生成原生 Word。

## Assumptions

- 不重跑计算或实验，不把重复总览当独立证据。
- Li₂NaH₁₇ 的 340 K 与 HTSC 讨论值 297 K 仅登记差异并列入 Jiang 原文待核，不擅断哪个值正确。
- Patsnap 只作二手框架，273 K 与项目 300 K 不混用。
- 未回源引文不整体背书，保持全部总览未全审。

## 冻结哈希

- `hydrides_overview`：`5b3c56d2ea572412b894f6643fb2ab7e31e693ad7755b63e112e51c0fa46f277`
- `batch_overview`：`243ef403bc372d13b442cc0086807fade7f7f478dba010bbfef2d3b9eeb11167`
- `complete_overview`：`314402bf0ae374bd74200c3a8492af8727b53082062d26b3bb7eaf28f2aa4fc7`
- `technical_review`：`992707a8092e65297ebe604d16d5ca203c0f2e0e32a76b43132e16133b7bea05`
- `htsc_pdf`：`b1669a6771c685519a5fbcfb45258dd606b957df23720405663408f59809af01`
- `patsnap_excerpts`：`4c43394d89bf1d8eb48e2a9dadb6b7396b2640f1a702f7ae87a19c65bb6d6a10`
- `boron_prb111_excerpts`：`542a2bac4ad20821e68b87879c7a07a1c10128dabfe3b6e9c8207f5c51973883`
- `main_claims_review`：`e9ac6ff0bc88f11b1c2c91ae61ce398a05fc077815803f48669b46536d6f2f45`
- `validation_materials_review`：`17eaa27d30df6849f752e3712d563ebe492ae394ea9c74b1b072ac0755acb491`
- `isotope_dft_review`：`e04428ca5980171619ca97bd2cc450fa772074cd9edd73f980905a72b1c2d4b4`
- `dmrg_qec_review`：`367fada5ec9f68011ea50bb437922d140aa7fcb77bbab7517d8548196332a68d`
- `methods_review`：`f30d15d8665644d11957166efaea95d59f7a742037dc697b737704cd15dc9e21`

### Task 1：规格、计划与失败合同

- [ ] 创建 `test_data_governance_audit.py` 与 `run.log`，固定十二项哈希、四个方向和十项勘误。
- [ ] 检查 Song 边界、HTSC 140／27.3／160、273／300 K 口径、B–C 77.1 K、Kruglov 024508、N_F Ry、压力方法、Chen 更新、QEC 复制错误、数据完整性和七个 false 边界。
- [ ] Word 合同：OMML、TOC、至少五个表格、PAGE、中文页眉、图片和来源脚注，含 `2506.03837`、`014510`、`2510.01273`、`024508` 及四份原文文件名。
- [ ] 两套测试均含零测试保护；运行主合同确认 `review.json` 缺失 RED。
- [ ] 提交 `test: define data governance audit contracts`。

### Task 2：统一证据对象、独立检查与图件

- [ ] 保留 `extract_sources.py`，记录 HTSC 7 页、31774 字符的提取结果。
- [ ] 创建 `verify_primary_sources.py`，直接核对 HTSC 样本与排除范围、Patsnap 二手角色、B–C 预测、Song 直接 Meissner／独立复现、既有 Kruglov 和 QEC 勘误。
- [ ] 创建 `build_review.py`，生成 `review.json`、`data-governance-evidence.svg/.png` 和 `REVIEW.md`。图左为总览宣称到原始证据，图右为可用研究进展及边界，不画验证百分比。
- [ ] Markdown 含“140 个样本”“27.3 K”“77.1 K”“024508”“图 1”“全库审计尚未完成”，并明确图件位于证据表后、解释前。
- [ ] 主合同此阶段只能剩余 DOCX 缺失；独立来源测试通过。

### Task 3：原生 Word 与逐页验收

- [ ] 创建 `build_report.js`、`.gitignore`、`.gitattributes`；A4、CJK 字体、中文页眉、PAGE-only 页脚、真实 TOC 域和可见缓存目录。
- [ ] 使用原生 MathSubScript 表示 N_F 与 T_c，明确 Ry 单位及 273／300 K 不同口径，不以图片替代公式。
- [ ] 至少五个表格：方向、Song／HTSC、研究进展、勘误、开放边界；图件在证据表后、解释前。
- [ ] 来源脚注覆盖 HTSC、Patsnap、B–C、Song、Kruglov、既有 QEC 和四份原文。
- [ ] `check-docx` 后构建并运行两个测试套件；最终视图逐页检查，修改后重新验收，不用 LibreOffice。
- [ ] 记录页数、逐页观察、版式修正、渲染器限制和 DOCX SHA-256。

### Task 4：fresh 回归与交付

- [ ] 两套测试、JSON、DOCX 哈希、`docx.py validate` 和 `git diff --check` 全部退出 0。
- [ ] SVG 和提取文本只通过 `.gitattributes` 保留原始空白，PDF 标 binary。
- [ ] 仅暂存本批文件，提交 `docs: audit overview and technical data governance`。
- [ ] 推送 `audit/room-temp-data-governance`，核对远端哈希，不合并主分支。
- [ ] 记录最终交付并继续其余 room_temp_sc 文档，保持全库目标 active。

## 计划自审

计划保留 HTSC 与 B–C 的真实发展价值，同时阻断 Song 循环确认、二手共识、实验化预测、重复书目错误和“归档即验证”的误判。
