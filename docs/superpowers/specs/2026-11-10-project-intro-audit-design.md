# 目录、项目介绍与 44 份文档覆盖图审计规格

日期：2026-11-10
分支：`audit/room-temp-project-intro`
基线：`cd14ead1754eb82a9a92408e2e8d5b12722046a8`

## 范围

完整审计 `organized/00-目录索引.md` 与 `organized/01-封面与介绍/` 的 3 份文档，并只读核查参考文献、原 README、手册任务书、原手册 DOCX 和前十个批次的结构化审计。原文不修改。

前十批覆盖 40 份组织后 Markdown，本批 4 份补齐为 44／44。覆盖只表示每份文档已进入审计，不表示每篇是独立新理论，也不表示科学验证或未竟工作已经完成。仓库在此 44 份之外仍有其他研究资产，不宣称整个仓库全部研究完成。

## 四个方向

1. `coverage_governance`：目录、批次血缘、44 份覆盖图与证据导航。
2. `conditional_formalization`：把必然性草案恢复为假设、定义、证明债务和可编译验收。
3. `handbook_reference_governance`：手册版本、日期、资产元数据和参考文献可用性。
4. `public_communication`：杂志策划的科学措辞、公众预期与媒介边界。

## 冻结来源（19 项）

- `directory_index`：`633844466f9c1fad0929a5250380a7e0467b7a458c24dc9006d820071dcad317`
- `project_intro`：`ddab8da04e8373fccedacc4634dfee09c7fc4be8eee5064e050f162f6bee4164`
- `handbook_intro`：`dd6721843deed0ad442b5ec3fc53303d4c895b6638d5d3dd5eb8b207b166161a`
- `magazine_plan`：`7f691b8f56f4d7ff04d4a3b3090cc4b48974fd7da89922ddeb8597bd046c34aa`
- `base_bib`：`ca014a4bae5023081149a1c4d051917e7f0540df18241400992c2b2276d43698`
- `enhanced_bib`：`d4a7d80243bc2fec0b05af4b0c9519d1be86edd0a62cd0d3d82b94a912ab870f`
- `original_readme`：`8eca2b541eb2412517af4ed28feafb301a29caeac960b6dede08be3717e1b9ff`
- `handbook_task`：`e520e11faa500339ceac76c324bddbcae9c6de16908d299fa832cfd7f85edec7`
- `handbook_docx`：`c2b77fa2b705b634a19f9959015acc990f663ba41d0b116bc6b48a37aa451b50`
- `main_claims_review`：`e9ac6ff0bc88f11b1c2c91ae61ce398a05fc077815803f48669b46536d6f2f45`
- `theory_review`：`e6acb59a95f4dc159db2692e5db0a6ae40d640f8a8aef04ca1b69da80e3ed8c8`
- `validation_review`：`17eaa27d30df6849f752e3712d563ebe492ae394ea9c74b1b072ac0755acb491`
- `isotope_review`：`e04428ca5980171619ca97bd2cc450fa772074cd9edd73f980905a72b1c2d4b4`
- `dmrg_review`：`367fada5ec9f68011ea50bb437922d140aa7fcb77bbab7517d8548196332a68d`
- `data_review`：`e09aeb77dd254d061d980c306e6762c1ef21ad8a5e826be6a08226d581680aa8`
- `handbook_review`：`0394b996c271a6ca24b4692d7bd078b4c0fa8925eefde6df0347a478f298ac48`
- `methods_review`：`f30d15d8665644d11957166efaea95d59f7a742037dc697b737704cd15dc9e21`
- `technical_review`：`d27fca5597387c24e9d0038e971055566522441a1f1f1dd8a0dd7dfe662e305f`
- `magazine_review`：`f025cef1935a604b67fe1c0504d6cdfc377ab2c69db450d3fd2da6034364b3bb`

## 已观察问题

- 目录遗漏 12–21 的资料收集与复盘，写入不存在的 PRL 版本，并直接推荐增强文献与 Lean 路径。
- `01-参考文献.bib` 有 24 条 BibTeX、5 处 `TO_BE_COMPLETED`；未找到 `2510.01273`、`2605.29985`、`2401840121`。
- `02-增强参考文献.bib` 存在但仅 22 字节，内容为 `: true # [source skip]`，BibTeX 条目为 0；文件存在不等于文献库可用。
- 项目说明含 admit/sorry，M1–M5 仍列待实现，却同时写“不会报错”；理论文档与所称 Lean 精确路径未找到。
- 原 README 是 v7.33 的另一版本，组织后项目说明是 0.1-alpha，二者 LF 归一化后仍不相同，不能混作同一版本。
- 手册说明更新日期为 2025 年 4 月，却含 2025 年 10 月突破，构成版本时间矛盾，不判造假。
- 原手册 DOCX 存在，大小 44510 字节；应用元数据为 Pages=1、Words=0，媒体文件为 0、OMML 不存在，约 50 页和图文并茂不能据此视为已验收。
- 杂志策划代表公众传播方向，不独立构成新物理理论；标题与互动形式仍受科学证据和无障碍边界约束。

## 交付

- `sources/coverage-inventory.json`：19 项来源、44 份覆盖行、批次方向、开放状态汇总与资产证据。
- `review.json`：4 份逐篇裁决、4 个方向、12 项勘误和覆盖／科学双边界。
- `REVIEW.md`、原生 `REVIEW.docx`、一张“覆盖完成不等于研究闭合”证据图。
- 独立来源测试、主合同、构建脚本、视觉 QA 和 `run.log`。

## 非目标

不补写证明、不新增 axiom/postulate/sorry、不修复原目录、不重建文献库、不对原手册重新进行视觉验收、不把历史报告当作当前科学证据。未回源内容只标未核实。
