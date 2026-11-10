# DMRG 与量子纠错资料审计实施计划

> 复用现有隔离工作树，当前分支 `audit/room-temp-dmrg-qec`，禁止子代理。先 RED 后 GREEN，原文只读，所有完成声明以实际命令和退出码为准。

**目标：** 形成 DMRG 证据阶梯、扩展模型完成、QEC 同口径基准和跨学科治理四个方向，闭合两份资料文档的证据角色。

**架构：** 九项冻结来源驱动一个 `review.json`；Python 核对 PDF／HTML 原文并生成双面板图和 Markdown；独立测试复核来源与否定边界；docx-js 生成原生 Word。

## Assumptions

- 不重跑 DMRG、解码器或硬件实验。
- Chen 的 8-leg 基态结果真实保留，不等于无限二维证明；Qu 的有限温度研究单列。
- 其他未回源引文不整体背书，保持 `all_citations_checked=false`。
- 未核实跨学科内容标为假说，不判造假。

## 冻结哈希

- `dmrg_notes`：`59e6b00f0cb240b9b0d3417f0f7906ae0fb5cf4a9b7cbcf79a8229181147d392`
- `qec_notes`：`59e747f55a96fd8d93885455d7ae7c2579acdeff4139e292023f5a723ec3fce2`
- `stripes_pdf`：`d37490cd24da075fd622ef48bc3f212ce35fa09ec8db8bcd737a7fe4b04e1531`
- `finite_temperature_pdf`：`e1ce8e1480fcf95156b7fffd23800b2b8dc4d6def9b64afb5835903cca3ae107`
- `extended_hubbard_pdf`：`2cbaa6cd2ec3e9b00a61627d23cf3f5e3f5ac022b1cd80d73e495028646a7a55`
- `global_dwave_html`：`3c2a77b1550f35e8a8eb8870150872cdc5e7b80c3ddd1d2799f9f455d3a2daca`
- `google_pdf`：`9ba05a64dfec13f5d733e0e22484e8f22db2482dc2a5a0d63e6f0766c9c3d368`
- `xzzx_pdf`：`918860f120639eb6897faff9d834aa977fbf54f781522276bff17c88c8db0cb7`
- `neutral_atoms_pdf`：`0b81702eedfd2525eb6ab74fe82f43a7dbc930a219298f1f21c7ee7698afa8e7`

### Task 1：规格、计划与失败合同

- [ ] 创建 `test_dmrg_qec_audit.py` 与 `run.log`，固定九项哈希、四个方向和九项勘误。
- [ ] 检查 Qu／Chen 层级、条纹 [43,44] 与 [41,42] 映射、Peng 四腿 d 波、XZZX 噪声、Google 指标、中性原子 [[8,3,2]]、LDPC 泛化、涡旋假说和六个 false 边界。
- [ ] Word 合同：OMML 分式、TOC、至少五个表格、PAGE、中文页眉、图片、九条来源脚注及标识 `2501.15709`、`2311.15092`、`2206.03486`、`2408.13687`、`[[8,3,2]]`、两份原文文件名。
- [ ] 两套测试均含零测试发现保护。
- [ ] 运行主合同，确认 `review.json` 缺失 RED；提交 `test: define DMRG and QEC audit contracts`。

### Task 2：统一证据对象、独立来源测试和图件

- [ ] 保留 `extract_sources.py`，记录六份 PDF 的页数和提取字符数。
- [ ] 创建 `verify_primary_sources.py`，直接核对 Qu 宽度／温度、Chen 8-leg 与 0.15、条纹编号、Peng 四腿、XZZX 噪声、Google 指标、中性原子码块和 2024 年。
- [ ] 创建 `build_review.py`，生成 `review.json`、`dmrg-qec-evidence.svg/.png` 和 `REVIEW.md`。图左分层 Qu、Chen 和二维极限；图右并列 Google、中性原子和被否决的“48 个 distance-7 LDPC”。
- [ ] Markdown 必须含“8-leg”“18.7%”“63 μs”“[[8,3,2]]”“图 1”“全库审计尚未完成”，并说明图件位于证据角色表之后、结果解释之前。
- [ ] 主合同此阶段只能剩余 DOCX 缺失；来源测试独立通过。

### Task 3：原生 Word 与逐页验收

- [ ] 创建 `build_report.js`、`.gitignore`、`.gitattributes`；A4、CJK 字体、中文页眉、PAGE-only 页脚、真实 TOC 域和可见缓存目录。
- [ ] 用 `MathFraction`／`MathSubScript` 构造原生 \(|t_2/t_1|\gtrsim0.15\)。
- [ ] 至少五个表格：方向、DMRG 证据、QEC 证据、勘误、开放边界；图件在证据角色表后、解释前，保持自然比例。
- [ ] 九条原生脚注覆盖九项来源。
- [ ] `check-docx` 后构建并运行两个测试套件；最终视图逐页检查，修改后重新验收，不用 LibreOffice。
- [ ] 记录页数、逐页观察、版式修正、渲染器限制和 DOCX SHA-256。

### Task 4：fresh 回归与交付

- [ ] 两个测试套件、JSON、DOCX 哈希、`docx.py validate` 和 `git diff --check` 全部退出 0。
- [ ] SVG 与提取文本只通过 `.gitattributes` 保留原始空白，PDF 标 binary；失败或残缺的下载不得入库。
- [ ] 仅暂存本批文件，提交 `docs: audit DMRG and quantum error correction evidence`。
- [ ] 推送 `audit/room-temp-dmrg-qec`，核对远端哈希，不合并主分支。
- [ ] 记录最终交付并继续其余 room_temp_sc 文档，保持全库目标 active。

## 计划自审

计划同时保留真实研究进展与否定边界，不把纠错扩大为对 DMRG 或 QEC 领域的整体否定，也不把局部回源称为全部引文审计。
