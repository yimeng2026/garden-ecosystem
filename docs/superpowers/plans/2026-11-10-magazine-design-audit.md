# 杂志设计系统审计实施计划

> 复用 `room-temp-isotope-dft-audit`，分支 `audit/room-temp-magazine-design`，禁止子代理、禁止嵌套工作树、禁止修改原文。先 RED 后 GREEN；所有 PASS 必须绑定当次命令和退出码。

**目标：** 完成 11 份文档逐篇裁决，建立科学传播、可计算设计、无障碍交互和生产溯源四条工作线，纠正“规范完成＝生产完成”的叙事。

**架构：** 以 17 项冻结来源和只读资产清单为底座；用独立复算检查 MD5 血缘、网格、页数和对比度；生成结构化裁决、Markdown、图件和原生 Word；最后逐页验收并推送具名分支。

## Assumptions

- 组织后文件是当前只读证据，原目录缺失不表示内容历史丢失；LF 归一化 MD5 可验证七项内容血缘。
- 不运行 `generate_pdf.py`，因为它覆写三份原说明文档；只做静态分析和现有 PDF 的只读检测。
- 未回源的历史、价格、引文和科学示例标记未核实，不判造假；全库目标保持 active。

### Task 1：规格与失败合同

- [x] 写入 17 项 SHA-256、11 份文档、四方向和十二项勘误合同。
- [x] 固定七项 LF-MD5 匹配、七个原路径缺失、六份 PDF、500 字预览、覆写风险和禁止运行约束。
- [x] 固定 212／174、176／165、10.833333／10.083333、106／60／14／16 和两项对比度复算。
- [x] 主测试与独立来源测试均含零测试保护；运行主测试确认缺少 `review.json` 的 RED。

### Task 2：只读清单与独立复算

- [x] 创建 `inspect_sources.py`，生成 `sources/source-inventory.json`，记录路径、哈希、LF-MD5、PDF 页数／页面尺寸／元数据和资产缺口。
- [x] 创建 `verify_primary_sources.py`，直接读取原文与脚本，复核科学措辞、H₂S 单位、占位符、网格、页数、对比度和禁止运行原因。
- [x] 创建 `build_review.py`，生成 `review.json`、`REVIEW.md` 和证据图；11 份文档均含方向、未竟工作和下一步。
- [x] 主合同此时仅允许 Word 尚未生成导致失败；独立来源测试必须通过。

### Task 3：报告与原生 Word

- [x] 图件呈现“内容血缘保留／生产链断开”“网格标称／复算”“对比度门槛”三组证据，不绘制验证百分比。
- [x] 创建 `build_report.js`，A4、CJK 字体、真实 TOC、中文页眉、PAGE-only 页脚、原生公式、至少六个表格、图片和来源脚注。
- [x] Word 明确图件位置、逐文档裁决、十二项勘误、未竟任务和非验证边界；构建后两套测试通过。
- [x] 最终视图先读联系表再逐页检查；退出 4／5／6 不重试、不用 LibreOffice；记录实际页数、观察、渲染限制和 DOCX SHA-256。

### Task 4：回归与交付

- [x] fresh 运行两套测试、JSON 解析、DOCX 哈希、`docx.py validate` 和 `git diff --check`，全部退出 0。
- [x] 仅暂存本批及规格计划，提交 `docs: audit magazine science communication and production`。
- [x] 推送 `audit/room-temp-magazine-design`，核对本地与远端哈希，不合并主分支。
- [x] 以 `docs: record magazine design audit delivery` 记录交付；目录索引与项目介绍列入后续审计，全库目标保持 active。
