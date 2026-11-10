# 主论文四版本与手册两章：证据角色、争议和未竟工作审计设计

- 日期：2026-11-10
- 分支：`audit/room-temp-claims-batch`
- 审计目录：`research/paper-direction-audit-2026-11-10/main-claims/`
- 范围：四份主论文版本、两章手册、前批方法审计及临界流形数值证据
- 原则：只生成审计与勘误建议，不直接修改六份原文，不删除正向或负向实验证据

## 1. 冻结来源

| ID | 路径或角色 | SHA-256 |
|:--|:--|:--|
| `main_master` | `organized/02-主论文/01-主论文.md` | `862e3232520ee961bc307a8e97cfd0b32a869a97197b159281596be3437d227f` |
| `nature_version` | `organized/02-主论文/02-Nature版本.md` | `fc5505cff6e3f65ee080ae4ec7a8f51f8ea2b4404e33a0d59146122bf91c568c` |
| `science_version` | `organized/02-主论文/03-Science版本.md` | `598de079d503596b9c9a5d43ba5027fafc5d9a13a12c4b3b03a3ba3e36d2e809` |
| `arxiv_version` | `organized/02-主论文/04-arXiv版本.md` | `7893cc30f25baca9aef27a3a3f9fc1a232e86fafdde109753885487f9268fc3b` |
| `handbook_materials` | `organized/08-手册章节/03-第4-5章_材料与实验.md` | `2816948242751325c7d3d28995f1ce836fb064e426f7d2bc941df3b14c8d5acd` |
| `handbook_future` | `organized/08-手册章节/04-第6章_未来展望.md` | `43e7826fac1fd4260e1cf0c01bf2ba6c1ffd6616652bb9b8825ea4fa006443bd` |
| `critical_results` | 临界流形 `results.json` | `f9438c770c1125c68b42a67778458d551f3694d1954b112bdf61d6942bac970b` |
| `prior_methods_review` | 前批 `room-temp-methods/review.json` | `cc73b74ad9951d6b0d25dee50ac06babd8f8ea2ffdde8a4823923d506cc466f7` |
| `song_pdf` | arXiv:2510.01273 PDF | `b820d4dac9162c0f8b914282afbbbe85e7005bce68c7b217abff070a715debdf` |
| `semenok_pdf` | arXiv:2605.29985 PDF | `a1dc4c13ecf800baf422e97aa51ba004b85ec7e6e32ecc7bf9f850df39a09bef` |

六份文档属于同一研究纲领，`research_program_count=1`。它们形成四个方法方向：必然性命题、可复现计算、实验争议与证据治理、出版与叙事边界。不得按版本数计算四个新理论。

## 2. 五层证据状态

所有关键陈述必须分开：

1. 文献/预印本是否存在；
2. 作者是否报告该结果；
3. 是否有独立正向复现；
4. 是否完成同行评议；
5. 是否支持数学必然性或普遍物理结论。

“未确立”不等于“已证伪”，“负向复现”不等于“作者必然造假”，“正向预印本”不等于“独立确认”。

## 3. LaSc₂H₂₄：正向与负向证据并存

### 3.1 理论预测

PNAS 121(26), e2401840121 是 2024 年理论预测：167 GPa 最高 316 K、250 GPa 最高 331 K。它本身不是实验论文，这一时间角色保持正确。

### 3.2 Song 正向实验预印本

arXiv:2510.01273 确实存在，v2 为 2025-10-06。作者报告：

- La-Sc 合金与氨硼烷在 250–260 GPa 激光加热合成；
- 195–266 GPa 下起始转变温度 271–298 K；
- 零电阻、外加磁场抑制 Tc、同步辐射 XRD；
- 13 次可重复实验运行。

审计只能写“作者报告”，不能自动升级为独立确认或已同行评议。全文还将直接 Meissner 磁测量列为未来工作，因此不得声称已经完成该直接磁测量。

“13 次可重复实验”没有提供“13 次全部成功、成功率 100%”的总尝试分母。手册的“成功率 100%”“铁证”“终极证明”不受当前证据支持。

### 3.3 Semenok 等负向复现预印本

arXiv:2605.29985 确实存在，v2 为 2026-08-20。作者报告：

- 7 次从 (La,Sc₂) 合金合成 LaSc₂H₂₄ 的实验未成功；
- 250–280 GPa 下未观察到 245–300 K 的超导迹象；
- 前驱体制备和原子有序化可能是关键；
- 理论上仍给出 300 GPa 下 Tc>300 K 的可能性，并指出展宽参数和稳定性问题。

它是独立负向复现证据，不是对 Song 论文或整个材料族的最终逻辑否证。当前正确状态是**实验结果存在实质争议，独立正向复现未确立**。

## 4. Nature 引文错配

手册 [C1] 声称 Chen et al. (2024) 的 LaSc₂H₂₄ 论文位于 Nature 626, 779–784。Crossref DOI `10.1038/s41586-024-07036-5` 的权威元数据明确显示该卷页实际是 **Twisted-layer boron nitride ceramic with high deformability and strength**，主题为氮化硼陶瓷，不是 LaSc₂H₂₄。

这是确认的 P0 书目错配。后续原文修订应删除该错误引文并留痕，分别引用 PNAS 预测、Song 预印本和 Semenok 预印本，不得用 Song 预印本倒填成 2024 Nature 论文。

## 5. 必然性命题与数值反例

四份主论文版本均以不同强度声称形式证明、严格下界、材料验证或普遍必然性，但：

- 主论文仍有 `[To be imported]` 和证明占位；
- 前批审计记录 Lean Markdown 48 处行首证明债务，独立 Lean 文件 3 个显式 `sorry`，未运行编译；
- SI 有 31 处既定模式占位，未形成 DFT 输入、声子谱和收敛日志；
- 临界流形的三个锚点温度 148.243…、166.850…、267.453…K 均低于 300 K；936 组根、38,376 个直接点分类不一致为 0。

这些数值只反驳使用同一简化公式时的普适必然性措辞，不否定完整 Eliashberg 理论、特定材料或 Song 的实验报告。报告必须保留这一范围，不能把反例扩大成整个超导理论被推翻。

## 6. 手册叙事和未核实内容

- “13 次全部成功／成功率 100%”没有总尝试分母支持。
- “第 42 次失败、第 43 次成功”、300 万元成本等叙事在当前 Song 全文的针对性检索中未找到支持，标为“未核实”，不直接判定虚构。
- “直接 Meissner 已完成”“独立实验室交叉验证”“必然性的终极证明”均不得使用。
- 2024 年“320 K 突破”与 2024 Nature 引文必须更正；Song 的 2025 年报告不得倒填为 2024 年实验事实。

## 7. 前批审计补充

前批关于 PNAS 是理论预测的判断仍正确，但其范围外登记只反映了当时的检索状态。本批必须明确补充：Song 正向实验预印本和 Semenok 负向复现均真实存在，不能再把 LaSc₂H₂₄ 的总体状态简写为“只有预测”。这不意味着前批数值或 PNAS 判断错误，而是新增证据改变了争议结构的完整性。

## 8. 交付与验收

交付：

- `review.json`：唯一证据对象，含 10 项冻结资产、四个方向、正负实验、Nature 错配、数值反例、未竟工作及前批补充。
- `REVIEW.md`：中文审计正文、证据时间线图及插入顺序、分档勘误建议。
- `REVIEW.docx`：同一 JSON 和 PNG 生成，含目录域、页眉页码、真正表格、原生公式、原生脚注和嵌入图。
- `claims-timeline.svg/.png`：2024 预测与错误引文、2025 正向报告、2026 负向复现的时间线，不表示真伪投票。
- `test_main_claims_audit.py`：`run_all_tests()`，先因 `review.json` 缺失 RED，再检查全部证据与边界。
- `verify_primary_sources.py`：独立核对 PDF 提取文本、Crossref 摘录和数值反例。
- `run.log`、`word-qa/report.json`：实际命令、退出码和逐页视觉结果。

必须为 false：`formal_proof_completed`、`lean_proof_verified`、`si_complete`、`peer_review_established`、`independent_positive_replication`、`direct_meissner_completed`、`success_rate_100_supported`、`ultimate_necessity_proven`、`full_repository_audit_completed`。

Word 通过 `docx.py build/validate` 后只渲染一次；4/5/6 表示视觉 QA 不可用，不重试、不使用 LibreOffice。全库审计不得因本批完成而标记完成。
