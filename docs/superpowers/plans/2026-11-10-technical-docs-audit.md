# 五份技术文档审计实施计划

> 复用现有隔离工作树，分支 `audit/room-temp-technical-docs`，禁止子代理。先 RED 后 GREEN；原文只读，完成声明必须来自实际命令与退出码。

**目标：** 建立资产存在性、状态一致性、科学验证和交付治理四层证据，纠正最终 100% 与实际资产及科学状态不符的问题。

**架构：** 先以只读资产清单固定实际存在与缺失，再由九项来源驱动 `review.json`；独立测试验证状态矛盾、科学边界和清单；统一生成图件、Markdown 和原生 Word。

## Assumptions

- 未找到只表示当前仓库未验证，不证明历史上从未存在；不判造假。
- 已存在的 LaTeX 和组织后文件保留，缺失只按精确路径记录。
- 不重跑计算或实验，未回源事实不整体背书。

## 冻结哈希

- `delivery_summary`：`957e71d98c74e813bed8780614552b20b0802f0ec6c4c598e2f3a39d2c49cdfc`
- `final_report`：`563b2fae7222a9ac9ccec3fac849b467e9ae46d571e99def0ef423a9f878e667`
- `progress_report`：`a4ffcdc575a2d9f0ae21108b5679856ed022c827bdd549020dc1f3be59d524bb`
- `quality_progress`：`0da15ed8122b1908bb8ce155956aebd55166330ca094982f81c6637624354d64`
- `integration_checklist`：`1510c3bc360560a1b131c9352616cd28717691abee41ff3951231a65d26d2909`
- `main_claims_review`：`e9ac6ff0bc88f11b1c2c91ae61ce398a05fc077815803f48669b46536d6f2f45`
- `validation_review`：`17eaa27d30df6849f752e3712d563ebe492ae394ea9c74b1b072ac0755acb491`
- `methods_review`：`f30d15d8665644d11957166efaea95d59f7a742037dc697b737704cd15dc9e21`
- `handbook_review`：`0394b996c271a6ca24b4692d7bd078b4c0fa8925eefde6df0347a478f298ac48`

### Task 1：规格、计划与失败合同

- [ ] 创建 `test_technical_docs_audit.py` 与 `run.log`，固定九项哈希、四个方向和八项勘误。
- [ ] 检查最终 100% 与运行中／模板矛盾、压缩包与 MD5 不可验证、图与引用缺失、版本部分存在、公式与评分、Lean／SI、实验与日期，以及六个 false 边界。
- [ ] Word 合同：OMML、TOC、至少五个表格、PAGE、中文页眉、图片和九条脚注，含 `2510.01273`、`024508`、五份原文文件名。
- [ ] 两套测试均含零测试保护；运行主合同确认 `review.json` 缺失 RED。
- [ ] 提交 `test: define technical documents audit contracts`。

### Task 2：实际资产清单、独立检查与图件

- [ ] 创建 `artifact_inventory.py`，只读检查压缩包、MD5 可验证性、六张图、引用库、各版本、Lean 和 SI 替代路径，生成 `sources/artifact-inventory.json` 并记录其 SHA-256。
- [ ] 创建 `verify_primary_sources.py`，直接核对五份文档状态、实际资产、H₃S 复算、评分规则、Lean／SI、Song／PNAS 角色和日期。
- [ ] 创建 `build_review.py`，生成 `review.json`、`technical-status-evidence.svg/.png` 和 `REVIEW.md`。图左为最终 100% 与运行中／模板矛盾，图右为缺失资产与部分存在文件。
- [ ] Markdown 含“完成状态 100%”“未找到”“161.081844”“图 1”“全库审计尚未完成”，并明确图件位于资产表后、解释前。
- [ ] 主合同此阶段只能剩余 DOCX 缺失；独立来源测试通过。

### Task 3：原生 Word 与逐页验收

- [ ] 创建 `build_report.js`、`.gitignore`、`.gitattributes`；A4、CJK 字体、中文页眉、PAGE-only 页脚、真实 TOC 域和可见缓存目录。
- [ ] 用 MathFraction／MathSubScript 创建原生 Tc 公式，展示 H₃S 复算而非 203 K，不以图片替代公式。
- [ ] 至少五个表格：方向、资产清单、状态时间线、科学边界、勘误与开放边界；图件在资产表后、解释前。
- [ ] 九条原生脚注覆盖九项来源。
- [ ] `check-docx` 后构建并运行两个测试套件；最终视图逐页检查，退出 4/5/6 不重试，不使用 LibreOffice。
- [ ] 记录页数、逐页观察或渲染不可用状态、版式修正、渲染器限制和 DOCX SHA-256。

### Task 4：fresh 回归与交付

- [ ] 两套测试、JSON、DOCX 哈希、`docx.py validate` 和 `git diff --check` 全部退出 0。
- [ ] SVG 和提取文本只通过 `.gitattributes` 保留原始空白，PDF 标 binary。
- [ ] 仅暂存本批文件，提交 `docs: audit technical delivery and validation evidence`。
- [ ] 推送 `audit/room-temp-technical-docs`，核对远端哈希，不合并主分支。
- [ ] 记录最终交付并继续杂志设计和项目介绍，保持全库目标 active。

## 计划自审

计划把实际资产、历史状态和科学验证分开，既保留存在的文件，也阻止缺失资产、未完成计算和矛盾状态被包装成最终交付。
