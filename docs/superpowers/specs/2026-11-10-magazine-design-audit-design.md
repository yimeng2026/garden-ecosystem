# 杂志设计系统审计规格

日期：2026-11-10
分支：`audit/room-temp-magazine-design`
基线：`bf1973db1809dd3566dd282a4a10e70f5bfffdf7`

## 范围与裁决

完整阅读 `organized/11-杂志设计/` 的 11 份文档，并只读检查原 `magazine/` 目录的生成脚本、交付报告、索引、校验清单与 PDF 资产。原文不修改；不运行会覆写原文的 `generate_pdf.py`；不把 PDF 文件存在等同于内容、印刷或科学验证通过。

这 11 份文档不是 11 篇论文或 11 个新理论。它们共同形成一个此前未充分展开的方向：**面向公众的科学传播与证据治理**。该方向向下分为四条工作线：

1. `editorial_evidence`：科学声明、引文、示例、状态图标与发布措辞的证据等级。
2. `computational_design`：开本、页数、栏宽、网格、色彩和版本的可计算一致性。
3. `accessible_media`：响应式、对比度、键盘替代、减弱动效、真实与模拟互动数据区分。
4. `production_provenance`：路径迁移、PDF／模板／字体／图像权利、压缩包和印前交付。

## 冻结来源（17 项）

- `magazine_readme`：`8462664575ea8c2be26f87edb185bd92ad5bd79ed05edc4d9b83a86508f46920`
- `magazine_intro`：`7137a7552f2eefd97eee3681da904a35d4bffcb68af12c0e063620f6106f2b3d`
- `pixel_system`：`2b05baac70fe8d8760df027d2d625f2801c5c0e947ece6beb3de93a4defe31b2`
- `vi_design`：`a7508aeda44598c028c200c0b3bdd1f30807f652c9cc26c88b9171dbefe52826`
- `layout_system`：`4602f8893cf31707858ff373c76068d2f080283599cc5894f2ee741d332089f8`
- `content_architecture`：`97cfb31cdb3269f3645f5f953b418d001139137eadfae2f562aa37d61db3670a`
- `web_layout`：`6c1d2e6d183b63d62a8a7355180f3c6fcbf6711da81a189ae959fe8430c943c4`
- `chat_culture`：`fe0dbae3b98307a02b32a286055657e7ecb604f31d621e579789880fe6746a7b`
- `page_designs`：`740e6d85ceb025e263f62d1772c8c60270836a39d595c07bf7e696ac71400036`
- `print_guide`：`d7ea6c943ea3c33ed16c4d41cbda3e8e5caed48573a3f4104aa8d0a09571ef72`
- `design_notes`：`71780e9bce7b365779a7b462091d405100f17508da378d3cb020dc0cc8cc2221`
- `generator`：`0d1a07296af61de49ed651f6210e237e561da6e77f9859c5795d3d56a778460c`
- `delivery_report`：`95bb50a5188edc8ac904bf5e7c057212d8606a711592222103ccd904ca82c10f`
- `file_index`：`8dab54d9cb830f649eed67574fba3fc7c22d85b309f274cfa852d46e8d43d3da`
- `checksums`：`b5e402be6adc80031d48994d4b80b6e81ea9b26d73435e791c257517e72e0b69`
- `handbook_review`：`0394b996c271a6ca24b4692d7bd078b4c0fa8925eefde6df0347a478f298ac48`
- `technical_review`：`d27fca5597387c24e9d0038e971055566522441a1f1f1dd8a0dd7dfe662e305f`

## 已观察证据

### 血缘与生产资产

- 原 `magazine/` 只有 `DELIVERY_REPORT.md`，七个原始设计 Markdown 路径均缺失；组织后 11 份文档均存在。
- 七份组织后设计文档统一 CRLF→LF 后的 MD5 与 `checksums.md5` 完全一致；这是换行差异，不是内容差异。
- `generate_pdf.py` 存在，但仅取每份文档前 500 字符生成预览；`run()` 会覆写 README、DESIGN_NOTES、PRINT_GUIDE。禁止对原目录执行。
- 当前发现六份 PDF；未发现 InDesign 模板或 VI 资源包。交付报告称 67 KB 压缩包已创建，需检查当前路径，不能把历史报告当作当前资产。
- `file_index.json` 是历史索引，可证明历史记录，不可证明当前路径仍存在。

### 可计算设计

- `05-排版系统`：12×14mm＋11×4mm＝212mm，不是 174mm；174mm 文本宽对应栏宽约 10.833333mm。
- `09-页面设计`：12×11mm＋11×4mm＝176mm，不是 165mm；165mm 文本宽对应栏宽约 10.083333mm。
- `02-杂志简介` 写 106 页，`06-内容架构` 写 60 页且封面故事分配 14 页、细项却为 16 页；另有 96 页纸张分段和 48–64 页建议。没有版本—页数清单不能视为同一成品规格。
- A4、210×285mm、256×192mm 等规格并存；8px 与 8mm 的换算未定义 DPI，不能直接互换。
- `#B829DD` 对 `#0A0A0F` 对比度约 4.137746，`#606070` 对同背景约 3.202044，均低于文档承诺的普通文本 4.5:1。

### 科学传播与编辑

- `02` 把 McMillan 简化公式写成“严格证明”和“数学必然”，并复述 13 次实验与 6% 误差；必须受前批手册和实验角色审计约束。
- `09` 的表格把 H₂S 的 155 GPa 放在“临界磁场”列；GPa 是压力单位，不能如此归类。
- 能源传输 99%、MRI 液氦比例、无限续航、模糊“最新新闻”、直接引语、量子通信“绝对安全”等均需来源、限定或降级；未核实项不直接判假。
- 模拟聊天、点赞数、田野调查和访谈提纲必须标明示例或提供真实材料，不能把模板当完成报道。
- `READY_FOR_PRODUCTION` 与未闭合科学声明、占位符、资产缺口并存，不能视为实际生产放行。

## 交付物

- `sources/source-inventory.json`：来源哈希、七项 LF-MD5 血缘、路径与 PDF 只读元数据。
- `review.json`：11 份逐文档裁决、四方向、十二项分级勘误、复算值和开放边界。
- `REVIEW.md`、原生 `REVIEW.docx`、一张证据图。
- `inspect_sources.py`、`build_review.py`、`build_report.js`、`verify_primary_sources.py`、`record_qa.py` 和两套测试。
- `run.log`：实际命令、退出码、失败与修正、视觉 QA、迁移和推送哈希。

## 非目标与边界

不重写杂志，不生成新印刷 PDF，不运行危险生成器，不将内部检查升级为同行评议、实验验证、PDF/X 认证或正式印前签字。外部历史、价格和引文未逐项回源时只标“未核实”。全库审计在本批后仍保留目录索引与项目介绍。
