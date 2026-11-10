import fs from "node:fs";
import path from "node:path";
import {
  AlignmentType, Document, Footer, FootnoteReferenceRun, Header, HeadingLevel,
  ImageRun, ImportedXmlComponent, Math as MathEquation, MathRun, Packer,
  PageBreak, PageNumber, Paragraph, ShadingType, Table, TableCell, TableRow,
  TextRun, WidthType,
} from "docx";

const outputPath = process.argv[2];
if (!outputPath) throw new Error("Usage: node build_report.js /absolute/path/REMEDIATION.docx");
const audit = path.dirname(outputPath);
const data = JSON.parse(fs.readFileSync(path.join(audit, "remediation.json"), "utf8"));
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
const titles = ["一、整改交付与证据图", "二、真实导航与现代来源", "三、输入血缘与验证", "四、剩余边界与下一步"];
const batchCounts = Object.entries(data.coverage.rows.reduce((counts, row) => ({ ...counts, [row.batch]: (counts[row.batch] || 0) + 1 }), {}));
const children = [
  para(run("导航与参考文献修复包", { bold: true, size: 38, color: palette.dark }), { heading: HeadingLevel.TITLE, alignment: AlignmentType.CENTER, spacing: { before: 600, after: 220 } }),
  para(run("44 份真实导航与 27 条可解析文献", { bold: true, size: 29, color: palette.primary }), { alignment: AlignmentType.CENTER, spacing: { after: 280 } }),
  para(run("独立新增 · 原始证据只读 · 可解析≠全部回源", { size: 21, color: palette.light }), { alignment: AlignmentType.CENTER, spacing: { after: 220 } }),
  para(run("2026-11-11　可机检验证 · 不宣称科学验证完成", { size: 19 }), { alignment: AlignmentType.CENTER, spacing: { after: 330 } }),
  heading("目录"),
  para(run("以下页码为可见缓存；在 Word/WPS 中更新域可刷新。", { size: 17, italics: true, color: palette.light })),
  toc(titles.map((title, index) => ({ title, level: 1, page: [2, 2, 3, 3][index] }))),
  pageBreak(),

  heading(titles[0]),
  equation("40 + 4 = 44／44，24 + 3 = 27"),
  makeTable(
    ["文件", "用途", "验收重点"],
    [
      ["INDEX.md", "真实 44 份导航与审计入口", "全路径、全目录组、无 PRL 成品、链接存在"],
      ["coverage.csv", "44 行机器覆盖表", "唯一路径、来源哈希、方向与评审路径"],
      ["references_repaired.bib", "27 条新库", "唯一 key、旧前缀保留、三条现代标识"],
      ["remediation.json", "统一结构化结果", "输入哈希、证据角色和双边界"],
      ["REMEDIATION.docx", "原生整改报告", "公式、表格、图件、脚注和逐页 QA"],
    ],
    [2300, 3500, 3706], 14,
  ),
  para(new ImageRun({ type: "png", data: fs.readFileSync(path.join(audit, data.figure.png)), transformation: { width: 610, height: 305 } }), { alignment: AlignmentType.CENTER, keepNext: true }),
  para(run(`${data.figure.caption}。图件位于整改资产表之后、剩余证据边界之前。`, { size: 18, italics: true }), { alignment: AlignmentType.CENTER }),
  body("仍有 5 个待补区块和 6 次占位字符串。可解析与可导航不等于全部可信、全部回源或科学验证完成。"),
  heading(titles[1]),
  citedBody("覆盖清单来自实际 44 个 Markdown 路径：前十批 40 份，本批 4 份。新目录同时提供来源哈希和审计入口，不再把 PRL 写成现有成品。", 1),
  makeTable(["批次", "覆盖数"], batchCounts.map(([batch, count]) => [batch, String(count)]), [6500, 3006], 14),
  equation("24 + 3 = 27 个唯一 BibTeX 条目"),
  citedBody("基础 24 条作为字节级前缀保留，旧条目仍有 5 个待补区块；复制不会自动提高其可信度，也不表示已逐条回源。", 2),
  makeTable(
    ["来源", "标识", "允许角色", "禁止升级"],
    [
      ["PNAS 2024", "10.1073/pnas.2401840121", "理论预测", "实验确认"],
      ["Song 2025 v2", "2510.01273", "作者正向实验预印本", "独立确认或必然性证明"],
      ["Semenok 2026 v2", "2605.29985", "独立负向复现预印本", "对 Song 或材料族的最终否证"],
    ],
    [1700, 2600, 3000, 2206], 14,
  ),
  citedBody("三条新增记录分别承担理论预测、作者正向预印本和独立负向预印本角色，彼此不能替代，也不能合并成“实验已完美验证”。", 3),
  citedBody("题名、年份、卷页和标识来自已核对的报告构建来源；作者字段只写 He／Song／Semenok and others，不虚构完整作者列表。", 4),
  citedBody("旧增强参考文献只有 : true # [source skip]，没有 BibTeX 条目。本包没有复用其内容，而是保留基础 24 条并追加三条已核实记录。", 5),
  heading(titles[2]),
  makeTable(
    ["输入 ID", "只读路径", "SHA-256"],
    data.source_inputs.map((row) => [row.id, row.path, row.sha256]),
    [1800, 3900, 3806], 12,
  ),
  makeTable(
    ["验证对象", "通过条件"],
    [
      ["覆盖导航", "44 个实际路径、00–21 全组、无重复、无 PRL 成品、审计链接存在"],
      ["CSV", "44 行、字段完整、来源哈希为 64 位、评审报告存在"],
      ["BibTeX", "27 个唯一 key、旧前缀保留、三条现代标识和角色注释存在"],
      ["占位披露", "5 个待补区块与 6 次占位字符串均保留"],
      ["原始证据", "五项输入哈希不变，不修改原文、Lean、手册或实验数据"],
    ],
    [2300, 7206], 14,
  ),
  body("两套验证均含零测试保护。最终交付还需通过 JSON／CSV／BibTeX 解析、OOXML 校验和最终视图逐页检查，具体命令与退出码见 run.log。"),
  heading(titles[3]),
  makeTable(
    ["边界", "状态", "含义"],
    Object.entries(data.open_boundaries).map(([key, value]) => [key, String(value), value ? "仅表示对应的局部交付或解析目标完成。" : "仍未完成，不能由导航、文件存在或条目数量推定。"]),
    [3600, 900, 5006], 14,
  ),
  body("后续先逐条回源旧 24 条并清偿 5 个待补区块，再推进 Lean 的真实模块、最小命题和编译验收；实验侧仍需独立正向复现与直接 Meissner。"),
  body("本包只完成导航和引用交付的局部整改，不修改原始证据，不新增证明、实验或独立复现，不宣称整个仓库或全部研究完成。"),
];

const document = new Document({
  creator: "TOE-SYLVA",
  title: "导航与参考文献修复包：44 份导航与 27 条文献",
  description: "真实导航、可解析 BibTeX、输入血缘、验证与剩余边界。",
  features: { updateFields: true },
  styles: {
    paragraphStyles: [1, 2].map((level) => ({
      id: `TOC${level}`, name: `TOC ${level}`, basedOn: "Normal", next: "Normal", quickFormat: true,
      run: { font, size: 19, color: palette.dark },
      paragraph: { spacing: { after: 70, line: 240 }, indent: { left: (level - 1) * 360 } },
    })),
  },
  footnotes: {
    1: { children: [footnote("Source: project-intro/sources/coverage-inventory.json; real paths, batches and source hashes.")] },
    2: { children: [footnote("Source: organized/09-参考文献/01-参考文献.bib; legacy 24 entries and five placeholder sections.")] },
    3: { children: [footnote("Source: main-claims/review.json; PNAS, Song and Semenok evidence roles and URLs.")] },
    4: { children: [footnote("Source: main-claims/build_report.js; checked titles, years and identifiers.")] },
    5: { children: [footnote("Source: organized/09-参考文献/02-增强参考文献.bib; 22 bytes and zero BibTeX entries.")] },
  },
  sections: [{
    properties: { page: { margin: { top: 1050, bottom: 1050, left: 1050, right: 1050 } } },
    headers: { default: new Header({ children: [para(run("TOE-SYLVA · 导航与参考文献修复 · 可解析≠全部回源", { size: 17, color: palette.primary }), { alignment: AlignmentType.CENTER })] }) },
    footers: { default: new Footer({ children: [para(new TextRun({ children: [PageNumber.CURRENT], font, size: 17 }), { alignment: AlignmentType.CENTER })] }) },
    children,
  }],
});

fs.writeFileSync(outputPath, await Packer.toBuffer(document));
