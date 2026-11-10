import fs from "node:fs";
import path from "node:path";
import {
  AlignmentType, Document, Footer, FootnoteReferenceRun, Header, HeadingLevel,
  ImageRun, ImportedXmlComponent, Math as MathEquation, MathRun, Packer,
  PageBreak, PageNumber, Paragraph, ShadingType, Table, TableCell, TableRow,
  TextRun, WidthType,
} from "docx";

const outputPath = process.argv[2];
if (!outputPath) throw new Error("Usage: node build_report.js /absolute/path/REVIEW.docx");
const audit = path.dirname(outputPath);
const data = JSON.parse(fs.readFileSync(path.join(audit, "review.json"), "utf8"));
const font = { ascii: "Times New Roman", hAnsi: "Times New Roman", cs: "Times New Roman", eastAsia: "SimSun" };
const palette = { dark: "263238", primary: "455A64", light: "78909C", fill: "EEF3F6" };
const run = (text, options = {}) => new TextRun({ text: String(text), font, size: 20, ...options });
const para = (children, options = {}) => new Paragraph({ spacing: { after: 100, line: 270 }, ...options, children: Array.isArray(children) ? children : [children] });
const body = (text, options = {}) => para(run(text), { indent: { firstLine: 400 }, ...options });
const citedBody = (text, footnoteId) => para([run(text), new FootnoteReferenceRun(footnoteId)], { indent: { firstLine: 400 } });
const heading = (text, level = 1) => para(run(text, { bold: true, size: level === 1 ? 29 : 25, color: palette.dark }), {
  heading: level === 1 ? HeadingLevel.HEADING_1 : HeadingLevel.HEADING_2,
  spacing: { before: 220, after: 120 }, keepNext: true,
});
const pageBreak = () => new Paragraph({ children: [new PageBreak()] });
const xmlEscape = (value) => String(value).replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;");
const toc = (entries) => {
  const cached = entries.map(({ title, level, page }) => `<w:p><w:pPr><w:pStyle w:val="TOC${level}"/>
    <w:tabs><w:tab w:val="right" w:leader="dot" w:pos="9000"/></w:tabs>
    <w:ind w:left="${Math.max(0, level - 1) * 360}"/></w:pPr>
    <w:r><w:t>${xmlEscape(title)}</w:t></w:r><w:r><w:tab/></w:r><w:r><w:t>${page}</w:t></w:r></w:p>`).join("");
  return ImportedXmlComponent.fromXmlString(`<w:sdt xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
    <w:sdtPr><w:alias w:val="目录"/></w:sdtPr><w:sdtContent>
      <w:p><w:r><w:fldChar w:fldCharType="begin" w:dirty="true"/>
        <w:instrText xml:space="preserve"> TOC \\o &quot;1-2&quot; \\h \\z \\u </w:instrText>
        <w:fldChar w:fldCharType="separate"/></w:r></w:p>
      ${cached}<w:p><w:r><w:fldChar w:fldCharType="end"/></w:r></w:p>
    </w:sdtContent></w:sdt>`).root[0];
};
const cell = (text, index, widths, header, size = 15) => new TableCell({
  children: [para(run(text, { size, bold: header }), { spacing: { after: 0, line: 200 } })],
  width: { size: widths[index], type: WidthType.DXA },
  margins: { top: 20, bottom: 20, left: 70, right: 70 },
  shading: header ? { type: ShadingType.CLEAR, fill: palette.fill } : undefined,
});
const makeTable = (headers, rows, widths, size = 15) => new Table({
  width: { size: widths.reduce((a, b) => a + b, 0), type: WidthType.DXA }, columnWidths: widths,
  rows: [
    new TableRow({ tableHeader: true, cantSplit: true, children: headers.map((text, index) => cell(text, index, widths, true, size)) }),
    ...rows.map((row) => new TableRow({ cantSplit: true, children: row.map((text, index) => cell(text, index, widths, false, size)) })),
  ],
});
const equation = (text) => para(new MathEquation({ children: [new MathRun(text)] }), { alignment: AlignmentType.CENTER, spacing: { before: 80, after: 100 } });
const footnote = (text) => para(run(text, { size: 15 }), { spacing: { after: 30, line: 190 } });
const titles = [
  "一、覆盖裁决与四个方向",
  "二、4 份文档逐篇裁决",
  "三、十二项分级勘误",
  "四、44 份文档覆盖清单",
  "五、19 项冻结来源",
  "六、双边界与后续",
];
const batchOrder = ["main-claims", "theory-breakthrough", "validation-materials", "isotope-dft", "dmrg-qec", "data-governance", "handbook-chapters", "room-temp-methods", "technical-docs", "magazine-design", "project-intro"];
const children = [
  para(run("目录与项目介绍审计", { bold: true, size: 38, color: palette.dark }), { heading: HeadingLevel.TITLE, alignment: AlignmentType.CENTER, spacing: { before: 600, after: 220 } }),
  para(run("44 份文档覆盖与未竟工作总图", { bold: true, size: 29, color: palette.primary }), { alignment: AlignmentType.CENTER, spacing: { after: 280 } }),
  para(run("40＋4＝44／44 · 四个方向 · 十二项勘误", { size: 21, color: palette.light }), { alignment: AlignmentType.CENTER, spacing: { after: 220 } }),
  para(run("2026-11-10　只读审计 · 覆盖完成不等于研究闭合", { size: 19 }), { alignment: AlignmentType.CENTER, spacing: { after: 330 } }),
  heading("目录"),
  para(run("以下页码为可见缓存；在 Word/WPS 中更新域可刷新。", { size: 17, italics: true, color: palette.light })),
  toc(titles.map((title, index) => ({ title, level: 1, page: [2, 3, 4, 4, 5, 6][index] }))),
  pageBreak(),

  heading(titles[0]),
  body(data.source_lineage.decision),
  equation("40 + 4 = 44／44，uncovered = []，duplicates = []"),
  makeTable(
    ["方向与角色", "已闭合的局部审计", "未竟工作与下一步"],
    data.directions.map((row) => [`${row.id}：${row.role}`, row.closed, `${row.unfinished} 下一步：${row.next}`]),
    [3000, 2800, 3706], 14,
  ),
  makeTable(
    ["批次", "覆盖数", "前批 false 开放状态项（含重叠）"],
    batchOrder.map((batch) => [batch, String(data.coverage.batch_counts[batch]), String(data.coverage.batch_open_false[batch] ?? "本批")]),
    [4800, 1300, 3406], 14,
  ),
  body("前十批共有 64 个 false 开放状态项，彼此可能重叠，不能解释为 64 个独立科学任务。覆盖计数只描述审计范围，不是科学验证百分比。"),
  para(new ImageRun({ type: "png", data: fs.readFileSync(path.join(audit, data.figure.png)), transformation: { width: 610, height: 366 } }), { alignment: AlignmentType.CENTER, keepNext: true }),
  para(run(`${data.figure.caption}。图件位于覆盖总览表之后、4 份文档逐篇裁决之前。`, { size: 18, italics: true }), { alignment: AlignmentType.CENTER }),
  pageBreak(),

  heading(titles[1]),
  makeTable(
    ["文档", "方向", "角色", "未竟工作与下一步"],
    data.document_assessments.map((row) => [row.title, row.direction_ids.join("／"), row.role, `${row.unfinished} 下一步：${row.next}`]),
    [1400, 1900, 2300, 3906], 13,
  ),
  citedBody("目录只列 01–11，遗漏 12–21 的资料收集与复盘；同时写入当前未找到的 PRL 版本。目录应由实际覆盖图生成，而不是手工维持完成叙事。", 1),
  citedBody("项目说明是 0.1-alpha 草案，明确承认 admit/sorry 和 M1–M5 待实现，却又声称可用这些标记确保不会报错。必须改为真实编译和证明债务验收。", 2),
  citedBody("手册说明写最后更新为 2025 年 4 月，却包含 2025 年 10 月突破。这里只标版本时间矛盾，不判造假。", 3),
  citedBody("杂志策划提供科技人文、栏目、视觉和互动方向；它不是独立物理理论，首刊标题和公众预期仍需科学证据约束。", 4),
  makeTable(
    ["证据对象", "实际观察", "验收裁决"],
    [
      ["基础 BibTeX", "24 条、5 个待补区块、6 次占位字符串", "缺现代关键条目，继续回源补齐"],
      ["增强 BibTeX", "22 字节；0 条；: true # [source skip]", "不可用，不能按路径存在推荐"],
      ["形式化", "admit/sorry；M1–M5 与精确路径未找到", "不写编译或证明完成"],
      ["README 血缘", "v7.33 与 0.1-alpha 不同", "不自动回填审慎声明"],
      ["原手册 DOCX", "44510 字节；Pages=1；Words=0", "约 50 页未据此验证"],
      ["原手册媒体与公式", "媒体 0；OMML=false", "不写图文并茂或原生公式已验收"],
    ],
    [2200, 3800, 3506], 14,
  ),
  citedBody("基础参考文献有 24 条和 5 个待补区块，缺少 Song／2025、Semenok／2026 与 PNAS 的关键标识，不能只以条目数量判断引用完整性。", 5),
  citedBody("目录推荐的增强参考文献文件实际只有 : true # [source skip]，没有 BibTeX 条目。它必须从可靠阅读路线中移除，直至生成可解析内容。", 6),
  citedBody("原 README 是 v7.33 的另一版本，含探索性假说声明；组织后项目说明是 0.1-alpha，两者不相同，不能自动把新版本的审慎措辞归给旧草案。", 7),
  citedBody("手册任务书把至少 10 个图表和输出要求列为任务。本批只核查资产与元数据，不把任务要求当作完成证明。", 8),
  citedBody("原手册 DOCX 的应用元数据为 Pages=1、Words=0，包内媒体为 0 且无 OMML。文件存在与 43.5 KB 大小不能证明约 50 页、图文并茂或公式合格。", 9),
  citedBody("手册中的完美对应、历史实现和 13 次从偶然到必然必须回到 Song、Semenok 与 PNAS 的不同证据角色；独立正向复现和直接 Meissner 仍未确立。", 10),
  pageBreak(),

  heading(titles[2]),
  makeTable(
    ["级别", "已观察问题", "建议动作"],
    data.corrections.map((row) => [row.severity, row.finding, row.action]),
    [800, 4400, 4306], 13,
  ),
  body("后续优先级：先阻断错误科学声明和不可用引用，再修目录与版本，随后清偿 Lean、文献和手册资产验收；杂志创意保留，但不越过证据等级。"),
  heading(titles[3]),
  body("以下每行均与实际文件和来源哈希核对。共享批次方向不等于单篇独立首创或新理论；本批四行使用当前文档方向。"),
  makeTable(
    ["文档路径", "来源 ID", "批次", "共享方向"],
    data.coverage.rows.map((row) => [row.path, row.source_id, row.batch, row.direction_ids.join("／")]),
    [3500, 1800, 1800, 2406], 11,
  ),
  heading(titles[4]),
  makeTable(
    ["来源 ID", "只读路径", "SHA-256"],
    data.sources.map((row) => [row.id, row.path, row.sha256]),
    [1700, 4500, 3306], 11,
  ),
  pageBreak(),

  heading(titles[5]),
  makeTable(
    ["边界", "状态", "当前含义"],
    Object.entries(data.open_boundaries).map(([key, value]) => [key, String(value), key === "organized_44_coverage_complete" ? "只表示 44 份文档覆盖核验完成。" : "仍未完成；不能由覆盖、文件存在或历史完成叙事推定。"]),
    [3500, 900, 5106], 14,
  ),
  citedBody("技术文档审计要求把资产存在、状态叙事和科学验证分开。本批的 44／44 只完成覆盖导航，不能消除前批的开放边界。", 11),
  citedBody("杂志设计审计已形成科学传播、可计算设计、无障碍和生产溯源工作线；本批策划案继续沿用这些约束，不另起未经验证的理论。", 12),
  body("后续以覆盖图为入口，按四个方向推进：修正真实目录；建立最小可编译命题；补齐并校验参考文献与手册资产；制作证据分级、可访问的公众样章。仓库在 44 份之外的研究资产不纳入本次完成声明。"),
  body("本批使用 19 项冻结来源、6 项独立来源测试和实际 44 路径核验。未修改原文，未新增证明或实验，未重新视觉验收原手册。覆盖完成不等于研究闭合。"),
];

const document = new Document({
  creator: "TOE-SYLVA",
  title: "目录、项目介绍与 44 份文档覆盖图审计",
  description: "目录、项目介绍、44 份文档覆盖、参考文献、形式化和手册资产审计。",
  features: { updateFields: true },
  styles: {
    paragraphStyles: [1, 2].map((level) => ({
      id: `TOC${level}`, name: `TOC ${level}`, basedOn: "Normal", next: "Normal", quickFormat: true,
      run: { font, size: 19, color: palette.dark },
      paragraph: { spacing: { after: 70, line: 240 }, indent: { left: (level - 1) * 360 } },
    })),
  },
  footnotes: {
    1: { children: [footnote("Source: organized/00-目录索引.md; omissions and version routes.")] },
    2: { children: [footnote("Source: organized/01-封面与介绍/01-项目说明.md; alpha proof debt.")] },
    3: { children: [footnote("Source: organized/01-封面与介绍/02-手册说明.md; update date and October narrative.")] },
    4: { children: [footnote("Source: organized/01-封面与介绍/03-杂志简介.md; editorial planning, not a physical theory.")] },
    5: { children: [footnote("Source: organized/09-参考文献/01-参考文献.bib; 24 entries and five placeholder sections.")] },
    6: { children: [footnote("Source: organized/09-参考文献/02-增强参考文献.bib; 22 bytes and zero BibTeX entries.")] },
    7: { children: [footnote("Source: papers/room_temp_sc/README.md; v7.33 differs from organized 0.1-alpha.")] },
    8: { children: [footnote("Source: papers/room_temp_sc/HANDBOOK_TASK.md; requirements are not completion evidence.")] },
    9: { children: [footnote("Source: handbook/room_temp_sc_handbook.docx; read-only package and app metadata inspection.")] },
    10: { children: [footnote("Source: main-claims/review.json; Song, Semenok and PNAS evidence roles.")] },
    11: { children: [footnote("Source: technical-docs/review.json; artifacts, status narratives and scientific validation are separate.")] },
    12: { children: [footnote("Source: magazine-design/review.json; science communication, accessibility and production boundaries.")] },
  },
  sections: [{
    properties: { page: { margin: { top: 1050, bottom: 1050, left: 1050, right: 1050 } } },
    headers: { default: new Header({ children: [para(run("TOE-SYLVA · 目录与项目介绍审计 · 覆盖不等于闭合", { size: 17, color: palette.primary }), { alignment: AlignmentType.CENTER })] }) },
    footers: { default: new Footer({ children: [para(new TextRun({ children: [PageNumber.CURRENT], font, size: 17 }), { alignment: AlignmentType.CENTER })] }) },
    children,
  }],
});

fs.writeFileSync(outputPath, await Packer.toBuffer(document));
