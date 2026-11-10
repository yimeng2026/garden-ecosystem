# Organized 导航与参考文献修复包设计

日期：2026-11-10
分支：`fix/organized-navigation-references`
基线：`1f5df69fed7e9121b53e4b7293cb4f177065aa91`

## 目标与边界

在 `research/organized-remediation/` 生成独立、可重复、可机检的导航和参考文献修复包。不得修改 `toe-sylva-audit/` 中的原始文档、原始 BibTeX、Lean、手册或实验数据。完成只表示导航与引用交付改善，不表示科学验证、全部文献回源、Lean 证明或实验复现完成。

## 方案选择

采用独立修复包。直接修改原目录会破坏只读证据约束；只写整改建议而不生成可用文件无法闭合交付缺口。修复包保留原路径与哈希，所有新增内容均可独立删除和重建。

## 输入与证据血缘

- `project-intro/sources/coverage-inventory.json`：44 份真实路径、批次、共享方向与哈希，冻结 SHA-256 `638f1e0cfb41ed7902869d28677d6adf50cc7644abe7de3a82a9e0ba6d025f7b`。
- `organized/09-参考文献/01-参考文献.bib`：24 条旧条目、5 个真实待补区块、6 次占位字符串，冻结 SHA-256 `ca014a4bae5023081149a1c4d051917e7f0540df18241400992c2b2276d43698`。
- `main-claims/review.json`：PNAS、Song、Semenok 的证据角色和原始 URL，冻结 SHA-256 `e9ac6ff0bc88f11b1c2c91ae61ce398a05fc077815803f48669b46536d6f2f45`。
- `main-claims/build_report.js` 中的三条已核对题名、年份和标识。

旧增强文件的 22 字节 `: true # [source skip]` 只作为反例，不作为新库内容来源。

## 文件与职责

- `INDEX.md`：真实 44 份导航，包含 00–21 全部路径、批次、共享方向、对应审计链接和开放状态说明；不再写入不存在的 PRL 成品或不可用增强文献路径。
- `coverage.csv`：44 行机器可读覆盖表，字段为 `path,source_id,batch,direction_ids,source_sha256,review_path`。
- `references_repaired.bib`：保留旧 24 条，新增三条唯一记录，合计 27 条。旧条目不因复制而自动获得可信度背书，5 个待补区块继续以注释披露。
- `remediation.json`：唯一结构化结果，记录输入哈希、44 覆盖、27 条目、三条现代来源、未决占位和非完成边界。
- `validate_remediation.py` 与 `test_remediation.py`：独立验证与交付合同，含零测试保护。
- `build_review.py`、`build_report.js`、`REMEDIATION.md`、`REMEDIATION.docx`、对照图和 `run.log`：统一生成报告、原生 Word、验证证据与实际命令记录。

## 三条新增文献

1. PNAS 2024 理论预测：`Predicted hot superconductivity in LaSc2H24 under pressure`，121(26)，e2401840121，DOI `10.1073/pnas.2401840121`。角色只能是理论预测。
2. Song 2025 v2：`Room-Temperature Superconductivity at 298 K in Ternary La-Sc-H System at High-pressure Conditions`，arXiv `2510.01273`。角色只能是作者正向实验预印本，不写独立确认。
3. Semenok 2026 v2：`Stability analysis of superconductivity in P6/mmm-LaSc2H24 and its experimental reproducibility from La-Sc alloys`，arXiv `2605.29985`。角色只能是独立负向复现预印本，不写最终否证。

作者字段仅使用已核实的 `He and others`、`Song and others`、`Semenok and others`，不虚构完整作者列表。题名、年份、卷页、DOI／arXiv 和 URL 必须精确匹配上述证据。

## 数据流

`coverage-inventory.json` 与实际 44 文件 → `coverage.csv` 与 `INDEX.md`；基础 24 条与三条已核实记录 → `references_repaired.bib`；两者汇入 `remediation.json` → Markdown、对照图和原生 Word。禁止在报告脚本中另建第二套事实数据库。

## 验收合同

- 44 个实际 Markdown 路径全部出现且无重复；00–21 各组均可检索；PRL 只作为未找到项说明。
- 每个覆盖行来源哈希与实际文件一致，审计链接指向存在的报告。
- BibTeX 可解析出 27 个 `@...{key` 条目且 key 唯一；三条现代标识全部存在；旧 24 条内容逐字保留在新库前半部。
- 5 个待补区块和 6 次占位字符串继续披露；不得以 27 条总数宣称全部文献已回源。
- 原输入哈希不变；不新增 axiom、postulate 或证明位 sorry；不宣称科学验证、全部文献回源或实验复现完成。
- 两套测试、JSON／CSV 解析、BibTeX 解析和 `git diff --check` 退出 0；Word 通过 OOXML 验证，并在可用时完成最终视图逐页检查。

## 报告叙事

对照图只显示可验证变化：目录覆盖从缺组到 44 份真实路径，引用交付从增强文件 0 条到新库 27 条，同时保留 5 个待补区块和科学开放边界。报告必须明确“可解析与可导航”不等于“全部可信、已验证或已回源”。
