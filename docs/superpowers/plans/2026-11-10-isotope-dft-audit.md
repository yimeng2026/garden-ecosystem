# 同位素、压力导数与多层 DFT 审计实施计划

> 当前隔离工作树执行，禁止子代理。两份原文只读，所有新证据与报告写入 `isotope-dft/`。先 RED 后 GREEN，验证必须有当次命令、退出码和关键输出。

**目标：** 闭合两份资料文档的证据角色，形成同位素参数血缘、方法一致压力曲线、可复现 DFT 和 ML 基准治理四个发展方向。

**架构：** 冻结两份原文、三份原始 PDF 和镍酸盐检索 CSV；Python 独立复算同位素系数与压力斜率，从 PDF 提取文本核对方法角色。统一 `review.json` 驱动双面板图、Markdown 和原生 Word。

## Assumptions

- 不重跑 DFT／DFPT／SCDFT／ALIGNN，不新做实验。
- JARVIS 1000+／150+ 零压数据集是真实既有资产，不列为错误；只纠正与新增 900+ 高压数据混排的问题。
- 镍酸盐“未找到精确出处”仅限本次 10 条 Scholar 结果，不判该研究不存在。
- 任何未核实内容不判造假；不把文内复算称为第一性原理结果。

## 冻结哈希

- `isotope_pressure`：`6199a3f71c53ffe6dfe9505f942d713cdb8b8c8da87d35913898163c04366c07`
- `multilayer_dft`：`ef31a1048fe415dfff433effc7fd7caefc4b124b320b104eb5e595e6d0752c5c`
- `kruglov_pdf`：`25632b30de626a14d2607f9c4ae1c0c57e78b4af2e0723985a6558e00c1555a4`
- `isotope_pdf`：`b5c69550005f7b4e926b12a60078a649d9939cbf6af51e07f42eec4063cfb6a6`
- `jarvis_pdf`：`de1d282d5924f1a695e47a52f4e6bb8d696aea3e423ae894ca165452b47a03ab`
- `nickelate_search`：`c82c8d735270ac6a154682dfcac6507e3d59224520fd15c5478be93b9e371fa4`

### Task 1：规格、计划和失败合同

- [x] 创建 `test_isotope_dft_audit.py` 与 `run.log`，固定上述哈希和四个方向。
- [x] 主合同检查：同位素 0.514573172829758／0.468148835738406／0.389211511910938；三段斜率 +0.4／−2.2／−0.075；200 GPa 为 SCDFT，其余表内三点为 Eliashberg；Kruglov=024508；JARVIS 数据角色；k 点、ML 基准、镍酸盐、六层定义和六个 false 边界。
- [x] Word 合同要求原生 OMML 分式、TOC、至少五个表格、PAGE、中文页眉、图片和六条来源脚注，标识 `024508`、`1912.09663`、`2312.12694`、`nickelate-dome-scholar.csv` 及两份原文文件名。
- [x] 两个测试套件使用 `run_all_tests()`，零测试发现返回非零。
- [x] 运行主合同，确认因 `review.json` 缺失而 RED，保存退出码 1 和完整错误。
- [x] 提交 `test: define isotope and DFT audit contracts`。

### Task 2：来源提取、数值复算与证据对象

- [x] 保留 `extract_sources.py`，从三份 PDF 生成只读分析用 `.txt`，记录页数和字符数。
- [x] 创建 `numeric_checks.py`：独立实现 `isotope_alpha(tc_h,tc_d,mass_h=1,mass_d=2)` 和 `slope(p1,t1,p2,t2)`，输出全部规定数值。
- [x] 创建 `verify_primary_sources.py`：直接检查 PDF 提取文本中的 271 星号、SCDFT 脚注、249／180 K 同位素对、JARVIS 数据规模和成本，以及检索 CSV 条数；独立调用数值函数。
- [x] 创建 `build_review.py`：生成 `review.json`、双面板 `isotope-pressure-evidence.svg/.png` 和 `REVIEW.md`。图左比较两组同位素值，图右区分 Eliashberg 圆点与 SCDFT 菱形；不得写成实验验证百分比。
- [x] Markdown 必须含“0.514573”“024508”“跨方法”“1000 倍”“图 1”“全库审计尚未完成”，并明确图件位于压力斜率表之后、结果解释之前。
- [x] 运行两个测试套件；主合同此阶段只能剩余 DOCX 缺失。保存所有实际输出。

### Task 3：原生 Word 与逐页验收

- [x] 创建 `build_report.js`、`.gitignore`、`.gitattributes`，使用显式 CJK 字体、A4、中文页眉、PAGE-only 页脚、真实 TOC 域和可见缓存目录。
- [x] 用 `MathFraction`、`MathSubScript` 创建原生 α 分式公式，不用图片替代。
- [x] 至少六个表格：方向、同位素、压力斜率、DFT／ML、勘误、开放边界。PNG 位于压力斜率表之后、结果解释之前，保持自然比例。
- [x] 六条原生脚注分别定位 Kruglov、Durajski、JARVIS、镍酸盐检索和两份原文。
- [x] `check-docx` 后用 `docx.py build`，运行两个测试套件。
- [x] 对最终 DOCX 渲染并逐页检查 contact sheet、所有页面、content-loss 和 near-blank 项；修改后必须重新验收，不用 LibreOffice。
- [x] 将页数、逐页观察、版式修正、渲染器限制和最终 SHA-256 写入 `word-qa/report.json`，命令与退出码写入 `run.log`。

### Task 4：fresh 回归和交付

- [x] 重跑两个测试套件、JSON 解析、DOCX 哈希、`docx.py validate` 和 `git diff --check`，全部退出 0。
- [x] SVG 原始行尾空格仅用 `.gitattributes` 豁免，不改写证据。
- [x] 仅暂存本批文件与计划，提交 `docs: audit isotope pressure and multilayer DFT evidence`。
- [x] 推送 `audit/room-temp-isotope-dft`，核对本地和远端哈希，不合并主分支。
- [x] 记录最终交付；继续其余 room_temp_sc 文档，保持全库目标 active。

## 计划自审

同位素、压力、DFT 和 ML 各自有可执行证据接口；真实数据角色与错误结论分开，未把审计扩大为计算或实验完成声明。
