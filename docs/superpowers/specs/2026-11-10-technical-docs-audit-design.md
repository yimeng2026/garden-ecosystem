# 五份技术文档最小证据审计设计

日期：2026-11-10
分支：`audit/room-temp-technical-docs`

## 范围

审计 `01-交付摘要`、`02-最终报告`、`03-进度报告`、`04-质量进展`、`05-整合检查清单`，原文只读。使用九项来源：五份文档、实际资产清单、主论文审计、实验验证与材料预测审计、方法审计、手册审计。

不重跑计算或实验，不把文件存在等同于科学验证，不把历史状态叙事等同于当前交付状态。

## 核心裁决

- 最终报告写“完成状态 100%”，但 A／D 两路仍运行中、质量深化仍进行中、整合清单仍为 `TEMPLATE／PARTIAL／PLACEHOLDERS`，构成直接状态矛盾。
- 当前仓库未找到 `room_temp_sc_paper_FINAL_v2.tar.gz`，因此 63 KB 和 MD5 均不可验证。
- 未找到 `references_enhanced.bib` 和六张图，99 条引用及“6 个 Nature 标准图表”没有资产支撑。
- 存在 `manuscript.tex`、`manuscript_nature.tex`、`manuscript_science.tex`、`manuscript_arxiv.tex`，但 `manuscript_prl.tex` 和所声称的 Markdown 对应文件未找到。多版本只部分存在，不能写成全格式完成。
- `RoomTempSuperconductivity.lean` 未找到；另有 `room_temp_sc_Formalization.lean`，但既有审计显示未编译、存在证明债务，不能称为机器证明。
- SI 的替代文件 `organized/10-技术文档/06-补充信息.md` 存在，但为模板，含 31 处既定模式占位，DFT 输入、声子谱和收敛日志未提供。
- H₃S 文内公式复算为约 161.081844 K，不是 203 K；验证百分比没有可复算评分规则，因此 B／C 路“完成”不能等同于科学验证完成。
- Song 直接 Meissner 和独立正向复现未确立；PNAS 是理论预测，不是实验验证。交付日期 2025-04-19 又早于所引 2025-10 突破，需核对版本血缘。

## 四个发展方向

1. `artifact_existence`：压缩包、哈希、图件、引用库、版本和实际路径的可验证资产清单。
2. `status_evidence`：最终 100%、运行中、模板和占位状态的时间线与一致性治理。
3. `scientific_validation`：公式、评分、Lean、SI、实验角色和证据等级验证。
4. `delivery_governance`：把整合清单转化为带资产、命令、退出码、责任边界的验收任务。

## 交付与验证

目录：`research/paper-direction-audit-2026-11-10/technical-docs/`。

- 统一 `review.json`、Markdown、原生 Word、双面板图、实际资产清单和独立测试。
- 图左显示最终 100% 与运行中／模板矛盾；图右显示缺失压缩包、图、引用库与部分存在的 LaTeX 文件。
- 八项勘误：状态矛盾、压缩包、图与引用、版本不全、状态时间线、公式与评分、Lean／SI、实验与日期。
- 至少五个表格、原生公式、九条来源脚注和完整验证记录。
- 六个 false 边界：压缩包验证、图件验证、99 引用验证、科学验证、交付就绪、全库完成。

采用“资产＋状态＋科学证据”的最小审计，而非再写一份完成报告。先 RED 后 GREEN，提交并推送具名分支，不合并主分支。
