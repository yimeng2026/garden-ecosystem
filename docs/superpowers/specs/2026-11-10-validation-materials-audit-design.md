# 实验验证与材料预测：最小证据审计设计

- 日期：2026-11-10
- 分支：`audit/room-temp-validation-materials`
- 审计目录：`research/paper-direction-audit-2026-11-10/validation-materials/`
- 范围：两份文档、三条原始证据链和文内公式复算
- 原则：只审计，不修改原文，不新增材料预测，不把复算称为第一性原理结果

## 1. 冻结来源

| ID | 角色 | SHA-256 |
|:--|:--|:--|
| `validation_report` | `organized/05-实验验证/01-实验验证.md` | `51a4709522000dca521dcecd071f20766763821eca94cb9e279335ea91f47e90` |
| `material_predictions` | `organized/04-材料预测/01-材料预测.md` | `050b52aa56bb633fd1db95e198f9804085de26080f4b18f135f44e3c8ef326ef` |
| `numeric_spotcheck` | 文内公式独立复算脚本 | `c11de34cb4f238e9c837effb735ebc9629921ea9494af28d474d75fddcee95d9` |
| `primary_excerpts` | 原始论文定位和边界 | `62cf61470cc7be0d17ee5e53a7e9f01b8cf8013c009698526aeafdcf5c281528` |

两份文档属于同一研究纲领，`research_program_count=1`。形成四个方法问题族：公式链、材料与掺杂错配、高阶氢化物证据角色、验证评分治理；不是四个新理论。

## 2. H-S-Cl 公式链与来源方向

- 文中 H3S 参数按所列简化公式复算为 `161.081843791778823 K`，不是表内 203 K。
- 文中 H-S-Cl 参数按同一公式复算为 `237.894818964651591 K`，不是表内 320 K。
- 这只证明参数—公式—结果不一致，不能据此替换为新的材料预测。
- 原始第一性原理研究在 200 GPa 下给出 6.25% Cl→161 K、12.5% Cl→136 K，方向为削弱超导；与 20% Cl→320 K 的推断不相容。Cl 降低稳定压力与提高 Tc 必须分开。

未竟工作：明确 f1/f2、ω2/ωlog、参数来源、单位、压力和掺杂结构，提供可重跑输入与原始输出。

## 3. LaNiO₂ 掺杂错配

- 原始研究显示未掺杂及低掺杂 La1−xCaxNiO2 薄膜绝缘，超导穹顶为 `0.15 < x < 0.3`。
- 报告必须把化学式、掺杂元素、掺杂范围、薄膜形态和输运证据写清，不能把未掺杂 LaNiO2 写成 20–40 K 已验证超导体。
- 不用另一个极端温度替换原数字；当前只裁决样品和证据角色错配。

## 4. 556 K 高阶氢化物角色

- Grockowiak 等论文确实存在，报告初始 294 K 和热循环后不可逆 556 K onset。
- 原文描述扭曲 LaH10 骨架和取代形成高阶化合物，且缺少 Meissner、可靠高温 H–T 相图和热力学平衡，存在非零电阻和混合相。
- 因此不能把 556 K 写成二元 LaH₁₀ 的常规验证结果或独立确认，也不能删除这篇真实论文。

未竟工作：独立复现、成分与相确定、直接磁测量、热力学平衡、原始数据和样品路径核对。

## 5. 验证度百分比和星级排序

92%、88%、45%、9.5/10 和星级排序没有公开指标定义、权重、样本集、误差模型或复算公式。它们只能作为主观研究治理标签，不能称为定量科学验证结果。后续若保留，应建立可复算评分卡并公开不确定性和证据权重。

## 6. 交付与验收

- `review.json`：四项冻结资产、一个纲领、四个问题族、原始证据、复算、勘误建议和开放边界。
- `REVIEW.md`：正文、对照表、图 1 及插入顺序、确定错误与未决项。
- `formula-spotcheck.svg/.png`：文中值与文中公式复算值对照，标题明确不是材料预测。
- `REVIEW.docx`：同一 JSON 和 PNG 生成，含目录域、OMML、真实表格、图、中文页眉页码和原始文献脚注。
- `test_validation_materials_audit.py`：先因 `review.json` 缺失 RED，覆盖全部数值、来源角色、禁止升格和 Word 结构。
- `verify_primary_sources.py`：独立核对原始摘录与复算脚本。
- `run.log`、`word-qa/report.json`：实际命令、退出码和逐页结果。

必须为 false：`global_fit`、`first_principles_recomputed`、`prediction_replaced`、`experimental_verification`、`full_document_source_audit`、`full_repository_audit`。

Word 只渲染最终版本一次；退出 4/5/6 表示视觉 QA 不可用，不重试、不使用 LibreOffice。全库审计不得因本批完成而标记完成。
