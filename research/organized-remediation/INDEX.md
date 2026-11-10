# Sylva 室温超导项目：真实 44 份导航（修复版）

> 由 `coverage.csv` 与 `remediation.json` 生成。原始文件只读；此目录不替代科学审计。

## 使用边界

- **40＋4＝44／44**：前十批 40 份，目录与项目介绍 4 份；无遗漏、无重复。
- **PRL 版本未找到**，不列为现有成品。主论文当前只列实际存在的版本。
- Lean、DFT、实验复现和独立 Meissner 仍为开放工作，不按“技术验证已完成”导航。
- 参考文献使用本包 `references_repaired.bib`；27 条可解析不代表全部回源或全部可信。
- 目录组：00、01、02、03、04、05、06、07、08、09、10、11、12、13、14、15、16、17、18、19、20、21。

## 推荐阅读顺序

1. `01-封面与介绍/01-项目说明.md`：只按 0.1-alpha 草案阅读，先查看证明债务。
2. `02-主论文/`：对照主论文审计，区分条件框架、预测和实验争议。
3. `03-理论框架` → `04-材料预测` → `05-实验验证`：同时打开对应审计，不使用必然性成稿口吻。
4. `07-形式化代码/`：先检查真实模块、编译命令和退出码，不把 admit/sorry 当完成。
5. `09-参考文献/`：旧增强文件不可用；使用本包新库并保留证据角色。

## 44 份文档与审计入口

| 序号 | 文档路径 | 来源 ID | 批次 | 共享方向 | 审计 |
|--:|:--|:--|:--|:--|:--|
| 1 | `00-目录索引.md` | `directory_index` | `project-intro` | `coverage_governance` | [打开](../paper-direction-audit-2026-11-10/project-intro/REVIEW.md) |
| 2 | `01-封面与介绍/01-项目说明.md` | `project_intro` | `project-intro` | `conditional_formalization` | [打开](../paper-direction-audit-2026-11-10/project-intro/REVIEW.md) |
| 3 | `01-封面与介绍/02-手册说明.md` | `handbook_intro` | `project-intro` | `handbook_reference_governance` | [打开](../paper-direction-audit-2026-11-10/project-intro/REVIEW.md) |
| 4 | `01-封面与介绍/03-杂志简介.md` | `magazine_plan` | `project-intro` | `public_communication` | [打开](../paper-direction-audit-2026-11-10/project-intro/REVIEW.md) |
| 5 | `02-主论文/01-主论文.md` | `main_master` | `main-claims` | `necessity_proof`、`reproducible_computation`、`experimental_controversy`、`publication_governance` | [打开](../paper-direction-audit-2026-11-10/main-claims/REVIEW.md) |
| 6 | `02-主论文/02-Nature版本.md` | `nature_version` | `main-claims` | `necessity_proof`、`reproducible_computation`、`experimental_controversy`、`publication_governance` | [打开](../paper-direction-audit-2026-11-10/main-claims/REVIEW.md) |
| 7 | `02-主论文/03-Science版本.md` | `science_version` | `main-claims` | `necessity_proof`、`reproducible_computation`、`experimental_controversy`、`publication_governance` | [打开](../paper-direction-audit-2026-11-10/main-claims/REVIEW.md) |
| 8 | `02-主论文/04-arXiv版本.md` | `arxiv_version` | `main-claims` | `necessity_proof`、`reproducible_computation`、`experimental_controversy`、`publication_governance` | [打开](../paper-direction-audit-2026-11-10/main-claims/REVIEW.md) |
| 9 | `03-理论框架/01-理论框架.md` | `theory_framework` | `theory-breakthrough` | `conditional_proof`、`assumption_falsifiability`、`experimental_controversy`、`provenance_governance` | [打开](../paper-direction-audit-2026-11-10/theory-breakthrough/REVIEW.md) |
| 10 | `04-材料预测/01-材料预测.md` | `material_predictions` | `validation-materials` | `formula_evidence`、`sample_doping`、`higher_order_hydride`、`validation_governance` | [打开](../paper-direction-audit-2026-11-10/validation-materials/REVIEW.md) |
| 11 | `05-实验验证/01-实验验证.md` | `validation_report` | `validation-materials` | `formula_evidence`、`sample_doping`、`higher_order_hydride`、`validation_governance` | [打开](../paper-direction-audit-2026-11-10/validation-materials/REVIEW.md) |
| 12 | `06-突破详解/01-2025年10月突破.md` | `breakthrough_report` | `theory-breakthrough` | `conditional_proof`、`assumption_falsifiability`、`experimental_controversy`、`provenance_governance` | [打开](../paper-direction-audit-2026-11-10/theory-breakthrough/REVIEW.md) |
| 13 | `07-形式化代码/01-Lean形式化代码.md` | `lean_markdown` | `room-temp-methods` | `floquet_evidence`、`eliashberg_bounds`、`lean_formalization`、`literature_digest`、`reproducible_si` | [打开](../paper-direction-audit-2026-11-10/room-temp-methods/REVIEW.md) |
| 14 | `08-手册章节/01-第1-2章_超导入门与科普.md` | `handbook_intro` | `handbook-chapters` | `pedagogical_physics`、`conditional_model`、`experimental_roles`、`unit_provenance` | [打开](../paper-direction-audit-2026-11-10/handbook-chapters/REVIEW.md) |
| 15 | `08-手册章节/02-第3章_必然性定理.md` | `handbook_theorem` | `handbook-chapters` | `pedagogical_physics`、`conditional_model`、`experimental_roles`、`unit_provenance` | [打开](../paper-direction-audit-2026-11-10/handbook-chapters/REVIEW.md) |
| 16 | `08-手册章节/03-第4-5章_材料与实验.md` | `handbook_materials` | `main-claims` | `necessity_proof`、`reproducible_computation`、`experimental_controversy`、`publication_governance` | [打开](../paper-direction-audit-2026-11-10/main-claims/REVIEW.md) |
| 17 | `08-手册章节/04-第6章_未来展望.md` | `handbook_future` | `main-claims` | `necessity_proof`、`reproducible_computation`、`experimental_controversy`、`publication_governance` | [打开](../paper-direction-audit-2026-11-10/main-claims/REVIEW.md) |
| 18 | `10-技术文档/01-交付摘要.md` | `delivery_summary` | `technical-docs` | `artifact_existence`、`status_evidence`、`scientific_validation`、`delivery_governance` | [打开](../paper-direction-audit-2026-11-10/technical-docs/REVIEW.md) |
| 19 | `10-技术文档/02-最终报告.md` | `final_report` | `technical-docs` | `artifact_existence`、`status_evidence`、`scientific_validation`、`delivery_governance` | [打开](../paper-direction-audit-2026-11-10/technical-docs/REVIEW.md) |
| 20 | `10-技术文档/03-进度报告.md` | `progress_report` | `technical-docs` | `artifact_existence`、`status_evidence`、`scientific_validation`、`delivery_governance` | [打开](../paper-direction-audit-2026-11-10/technical-docs/REVIEW.md) |
| 21 | `10-技术文档/04-质量进展.md` | `quality_progress` | `technical-docs` | `artifact_existence`、`status_evidence`、`scientific_validation`、`delivery_governance` | [打开](../paper-direction-audit-2026-11-10/technical-docs/REVIEW.md) |
| 22 | `10-技术文档/05-整合检查清单.md` | `integration_checklist` | `technical-docs` | `artifact_existence`、`status_evidence`、`scientific_validation`、`delivery_governance` | [打开](../paper-direction-audit-2026-11-10/technical-docs/REVIEW.md) |
| 23 | `10-技术文档/06-补充信息.md` | `si_template` | `room-temp-methods` | `floquet_evidence`、`eliashberg_bounds`、`lean_formalization`、`literature_digest`、`reproducible_si` | [打开](../paper-direction-audit-2026-11-10/room-temp-methods/REVIEW.md) |
| 24 | `11-杂志设计/01-杂志说明.md` | `magazine_readme` | `magazine-design` | `editorial_evidence`、`computational_design`、`accessible_media`、`production_provenance` | [打开](../paper-direction-audit-2026-11-10/magazine-design/REVIEW.md) |
| 25 | `11-杂志设计/02-杂志简介.md` | `magazine_intro` | `magazine-design` | `editorial_evidence`、`computational_design`、`accessible_media`、`production_provenance` | [打开](../paper-direction-audit-2026-11-10/magazine-design/REVIEW.md) |
| 26 | `11-杂志设计/03-黑白像素系统.md` | `pixel_system` | `magazine-design` | `editorial_evidence`、`computational_design`、`accessible_media`、`production_provenance` | [打开](../paper-direction-audit-2026-11-10/magazine-design/REVIEW.md) |
| 27 | `11-杂志设计/04-VI设计.md` | `vi_design` | `magazine-design` | `editorial_evidence`、`computational_design`、`accessible_media`、`production_provenance` | [打开](../paper-direction-audit-2026-11-10/magazine-design/REVIEW.md) |
| 28 | `11-杂志设计/05-排版系统.md` | `layout_system` | `magazine-design` | `editorial_evidence`、`computational_design`、`accessible_media`、`production_provenance` | [打开](../paper-direction-audit-2026-11-10/magazine-design/REVIEW.md) |
| 29 | `11-杂志设计/06-内容架构.md` | `content_architecture` | `magazine-design` | `editorial_evidence`、`computational_design`、`accessible_media`、`production_provenance` | [打开](../paper-direction-audit-2026-11-10/magazine-design/REVIEW.md) |
| 30 | `11-杂志设计/07-网页风格排版.md` | `web_layout` | `magazine-design` | `editorial_evidence`、`computational_design`、`accessible_media`、`production_provenance` | [打开](../paper-direction-audit-2026-11-10/magazine-design/REVIEW.md) |
| 31 | `11-杂志设计/08-网聊文化融入.md` | `chat_culture` | `magazine-design` | `editorial_evidence`、`computational_design`、`accessible_media`、`production_provenance` | [打开](../paper-direction-audit-2026-11-10/magazine-design/REVIEW.md) |
| 32 | `11-杂志设计/09-页面设计.md` | `page_designs` | `magazine-design` | `editorial_evidence`、`computational_design`、`accessible_media`、`production_provenance` | [打开](../paper-direction-audit-2026-11-10/magazine-design/REVIEW.md) |
| 33 | `11-杂志设计/10-印刷指南.md` | `print_guide` | `magazine-design` | `editorial_evidence`、`computational_design`、`accessible_media`、`production_provenance` | [打开](../paper-direction-audit-2026-11-10/magazine-design/REVIEW.md) |
| 34 | `11-杂志设计/11-设计笔记.md` | `design_notes` | `magazine-design` | `editorial_evidence`、`computational_design`、`accessible_media`、`production_provenance` | [打开](../paper-direction-audit-2026-11-10/magazine-design/REVIEW.md) |
| 35 | `12-资料收集-氢化物与验证进展.md` | `hydrides_overview` | `data-governance` | `claim_lineage`、`benchmark_scope`、`data_completeness`、`research_update` | [打开](../paper-direction-audit-2026-11-10/data-governance/REVIEW.md) |
| 36 | `13-资料收集-Floquet工程LaH10.md` | `floquet_notes` | `room-temp-methods` | `floquet_evidence`、`eliashberg_bounds`、`lean_formalization`、`literature_digest`、`reproducible_si` | [打开](../paper-direction-audit-2026-11-10/room-temp-methods/REVIEW.md) |
| 37 | `14-资料收集-DMRG-Hubbard模型.md` | `dmrg_notes` | `dmrg-qec` | `dmrg_evidence_ladder`、`extended_model_completion`、`qec_benchmark_roles`、`cross_domain_governance` | [打开](../paper-direction-audit-2026-11-10/dmrg-qec/REVIEW.md) |
| 38 | `15-资料收集-Eliashberg理论边界.md` | `eliashberg_notes` | `room-temp-methods` | `floquet_evidence`、`eliashberg_bounds`、`lean_formalization`、`literature_digest`、`reproducible_si` | [打开](../paper-direction-audit-2026-11-10/room-temp-methods/REVIEW.md) |
| 39 | `16-资料收集-总览与下一步.md` | `batch_overview` | `data-governance` | `claim_lineage`、`benchmark_scope`、`data_completeness`、`research_update` | [打开](../paper-direction-audit-2026-11-10/data-governance/REVIEW.md) |
| 40 | `17-资料收集-同位素效应与压力导数.md` | `isotope_pressure` | `isotope-dft` | `isotope_lineage`、`method_aware_pressure`、`reproducible_dft`、`ml_benchmark_governance` | [打开](../paper-direction-audit-2026-11-10/isotope-dft/REVIEW.md) |
| 41 | `18-资料收集-量子纠错码进展.md` | `qec_notes` | `dmrg-qec` | `dmrg_evidence_ladder`、`extended_model_completion`、`qec_benchmark_roles`、`cross_domain_governance` | [打开](../paper-direction-audit-2026-11-10/dmrg-qec/REVIEW.md) |
| 42 | `19-资料收集-多层结构DFT参数.md` | `multilayer_dft` | `isotope-dft` | `isotope_lineage`、`method_aware_pressure`、`reproducible_dft`、`ml_benchmark_governance` | [打开](../paper-direction-audit-2026-11-10/isotope-dft/REVIEW.md) |
| 43 | `20-资料收集-总览与完整清单.md` | `complete_overview` | `data-governance` | `claim_lineage`、`benchmark_scope`、`data_completeness`、`research_update` | [打开](../paper-direction-audit-2026-11-10/data-governance/REVIEW.md) |
| 44 | `21-技术复盘-全领域数据审计.md` | `technical_review` | `data-governance` | `claim_lineage`、`benchmark_scope`、`data_completeness`、`research_update` | [打开](../paper-direction-audit-2026-11-10/data-governance/REVIEW.md) |

## 未竟工作

覆盖完成不等于研究闭合。请优先处理各审计中的 P0／P1 项；不得把此导航当作科学验证、Lean 证明、全部文献回源或实验复现的完成证明。
