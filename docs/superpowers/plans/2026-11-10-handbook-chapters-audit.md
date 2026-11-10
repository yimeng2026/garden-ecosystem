# 手册第 1–3 章审计实施计划

> 复用现有隔离工作树，分支 `audit/room-temp-handbook-chapters`，禁止子代理。先 RED 后 GREEN；原文只读，所有结论以实际命令和退出码为准。

**目标：** 保留准确的入门教学与简化模型充分条件，纠正公式 4、条件集错位、频率换算、实验越级和入门叙事错误。

**架构：** 六项冻结来源驱动 `review.json`；独立 Python 数值函数复算 Tc、阈值、频率换算和相对误差；另一套来源测试核对 BCS、McMillan 与既有审计；统一生成图件、Markdown 和原生 Word。

## Assumptions

- 不重跑 DFT 或实验，不把简化 McMillan 模型当完整 Eliashberg 或普遍物理证明。
- Θ_D＝2100 K 若与 210 meV 是同一最大频率则不匹配；若属于不同有效量，需单列来源，不直接判其虚假。
- 其余入门历史和应用事实未逐项回源，保持未全审。

## 冻结哈希

- `handbook_intro`：`bb67c6d7b57a2dad1f42eed1bd2729697e590c643953e05e19ca0a7016463d23`
- `handbook_theorem`：`062b0011cc45b34ed8545a5890769ca71382608b09371641af5a51060c476e97`
- `physics_foundations`：`93dd0cc19dc0b72c3103c607ded0a513837f664b3aaa872150e9bcb0a7d1c13e`
- `main_claims_review`：`e9ac6ff0bc88f11b1c2c91ae61ce398a05fc077815803f48669b46536d6f2f45`
- `theory_review`：`e6acb59a95f4dc159db2692e5db0a6ae40d640f8a8aef04ca1b69da80e3ed8c8`
- `data_governance_review`：`e09aeb77dd254d061d980c306e6762c1ef21ad8a5e826be6a08226d581680aa8`

### Task 1：规格、计划与失败合同

- [x] 创建 `test_handbook_chapters_audit.py` 与 `run.log`，固定六项哈希、四个方向和八项勘误。
- [x] 检查公式 4=259.594501、示例=326.617108、阈值=2426.861883、210 meV=2436.948806、150 meV=1740.677718、298<300、条件集不等价、教学时间线、H₃S 和六个 false 边界。
- [x] Word 合同：OMML 分式、TOC、至少五个表格、PAGE、中文页眉、图片、六条脚注及 `108.1175`、`167.331`、`2510.01273`、两份手册文件名。
- [x] 两套测试均含零测试保护；运行主合同确认 `review.json` 缺失 RED。
- [x] 提交 `test: define handbook chapters audit contracts`。

### Task 2：数值函数、独立来源测试与证据对象

- [x] 创建 `numeric_checks.py`，实现 `exponent(lam,mu)`、`tc(lam,mu,theta)`、`theta_threshold(lam,mu)` 和 `mev_to_kelvin`，输出全部规定值。
- [x] 创建 `verify_primary_sources.py`，核对 BCS／McMillan 原文、两份手册原文、既有 Song／Semenok／临界流形角色和独立数值。
- [x] 创建 `build_review.py`，生成 `review.json`、`handbook-evidence.svg/.png` 和 `REVIEW.md`。图左为公式 4 与正确示例对照，图右为三条件、定理条件和实验角色分层。
- [x] Markdown 含“259.594501”“326.617108”“2436.948806”“图 1”“全库审计尚未完成”，并明确图件位于复算表后、解释前。
- [x] 主合同此阶段只能剩余 DOCX 缺失；独立来源测试通过。

### Task 3：原生 Word 与逐页验收

- [x] 创建 `build_report.js`、`.gitignore`、`.gitattributes`；A4、CJK 字体、中文页眉、PAGE-only 页脚、真实 TOC 域和可见缓存目录。
- [x] 用 MathFraction／MathSubScript 创建原生 McMillan 指数和 Tc 公式，不以图片替代。
- [x] 至少五个表格：方向、数值复算、教学勘误、实验角色、开放边界；图件在复算表后、解释前。
- [x] 六条原生脚注覆盖六项来源。
- [x] `check-docx` 后构建并运行两个测试套件；最终视图逐页检查，修改后重新验收，不用 LibreOffice。
- [x] 记录页数、逐页观察、版式修正、渲染器限制和 DOCX SHA-256。

### Task 4：fresh 回归与交付

- [x] 两套测试、JSON、DOCX 哈希、`docx.py validate` 和 `git diff --check` 全部退出 0。
- [x] SVG 和提取文本只通过 `.gitattributes` 保留原始空白，PDF 标 binary。
- [x] 仅暂存本批文件，提交 `docs: audit handbook pedagogy and necessity claims`。
- [x] 推送 `audit/room-temp-handbook-chapters`，核对远端哈希，不合并主分支。
- [x] 记录最终交付并继续技术文档、杂志设计和项目介绍，保持全库目标 active。

## 计划自审

计划同时保留正确示例、阈值和真实研究进展，阻断公式 4、条件集、实验验证和教学绝对化的错误传播。
