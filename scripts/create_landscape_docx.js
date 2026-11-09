import fs from "node:fs";
import path from "node:path";
import {
  AlignmentType, Document, ExternalHyperlink, Footer, Header, HeadingLevel,
  ImageRun, ImportedXmlComponent, Packer, PageBreak, PageNumber, Paragraph,
  ShadingType, Table, TableCell, TableRow, TextRun, WidthType,
  convertInchesToTwip,
} from "docx";

const outputPath = process.argv[2];
if (!outputPath) throw new Error("Usage: create_landscape_docx.js output.docx");
const sourcePath = process.env.DOCX_SOURCE || path.join(path.dirname(outputPath), "landscape.md");
const isBridgeGuide = path.basename(sourcePath) === "bridge-integration.md";
const documentTitle = isBridgeGuide ? "千界花园受控桥接使用手册与验证记录" : "千界花园同类开源项目广泛调研与整体设计依据";
const documentSubtitle = isBridgeGuide ? "受控 stdio · 真实 Lean 健康检查 · Next.js API" : "GitHub · Gitee · GitLab · Codeberg · Hugging Face";
const sourceDir = path.dirname(sourcePath);
const font = { ascii: "Times New Roman", hAnsi: "Times New Roman", cs: "Times New Roman", eastAsia: "SimSun" };
const run = (text, options = {}) => new TextRun({ text, font, size: 22, ...options });
const para = (children, options = {}) => new Paragraph({
  spacing: { after: 150, line: 310 }, ...options,
  children: Array.isArray(children) ? children : [children],
});
const xmlEscape = (value) => String(value).replaceAll("&", "&amp;").replaceAll("<", "&lt;")
  .replaceAll(">", "&gt;").replaceAll('"', "&quot;");

function rich(text, size = 22) {
  const parts = [];
  const pattern = /\[([^\]]+)\]\(([^)]+)\)|\*\*([^*]+)\*\*|`([^`]+)`/g;
  let cursor = 0;
  for (const match of text.matchAll(pattern)) {
    if (match.index > cursor) parts.push(run(text.slice(cursor, match.index), { size }));
    if (match[1]) {
      parts.push(new ExternalHyperlink({ link: match[2], children: [run(match[1], { size, color: "315B7D", underline: {} })] }));
    } else if (match[3]) {
      parts.push(run(match[3], { size, bold: true }));
    } else {
      parts.push(new TextRun({ text: match[4], size, font: { ascii: "Consolas", hAnsi: "Consolas", cs: "Consolas", eastAsia: "SimSun" } }));
    }
    cursor = match.index + match[0].length;
  }
  if (cursor < text.length) parts.push(run(text.slice(cursor), { size }));
  return parts.length ? parts : [run("", { size })];
}

function splitRow(line) {
  const trimmed = line.trim().replace(/^\|/, "").replace(/\|$/, "");
  return trimmed.split(/(?<!\\)\|/).map((cell) => cell.trim().replaceAll("\\|", "|"));
}

const lines = fs.readFileSync(sourcePath, "utf8").split(/\r?\n/);
const blocks = [];
for (let index = 0; index < lines.length;) {
  const line = lines[index];
  if (!line.trim()) { index += 1; continue; }
  const image = line.match(/^!\[(.*)\]\(([^)]+)\)$/);
  if (image) { blocks.push({ type: "image", alt: image[1], path: image[2] }); index += 1; continue; }
  if (line.startsWith("#")) {
    const match = line.match(/^(#+)\s+(.*)/);
    if (match) { blocks.push({ type: "heading", level: match[1].length, text: match[2] }); index += 1; continue; }
  }
  if (line.trim().startsWith("|") && index + 1 < lines.length && /^\|(?:---\|)+$/.test(lines[index + 1].trim())) {
    const rows = [splitRow(line)];
    index += 2;
    while (index < lines.length && lines[index].trim().startsWith("|")) {
      rows.push(splitRow(lines[index])); index += 1;
    }
    blocks.push({ type: "table", rows });
    continue;
  }
  const text = [line];
  index += 1;
  while (index < lines.length && lines[index].trim() && !lines[index].startsWith("#") && !lines[index].trim().startsWith("|") && !lines[index].startsWith("![")) {
    text.push(lines[index]); index += 1;
  }
  blocks.push({ type: "paragraph", text: text.join(" ") });
}

const tocEntries = blocks.filter((block) => block.type === "heading" && block.level === 2)
  .map((block, index) => ({ title: block.text, page: 3 + index * 2 }));
const toc = ImportedXmlComponent.fromXmlString(`<w:sdt xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:sdtPr><w:alias w:val="目录"/></w:sdtPr><w:sdtContent>
    <w:p><w:r><w:fldChar w:fldCharType="begin" w:dirty="true"/>
      <w:instrText xml:space="preserve"> TOC \\o &quot;1-3&quot; \\h \\z \\u </w:instrText>
      <w:fldChar w:fldCharType="separate"/></w:r></w:p>
    ${tocEntries.map((entry) => `<w:p><w:pPr><w:pStyle w:val="TOC1"/><w:tabs><w:tab w:val="right" w:leader="dot" w:pos="9000"/></w:tabs></w:pPr><w:r><w:t>${xmlEscape(entry.title)}</w:t></w:r><w:r><w:tab/></w:r><w:r><w:t>${entry.page}</w:t></w:r></w:p>`).join("")}
    <w:p><w:r><w:fldChar w:fldCharType="end"/></w:r></w:p>
  </w:sdtContent></w:sdt>`).root[0];

const children = [
  para(run("千界花园", { bold: true, size: 34, color: "557180" }), { alignment: AlignmentType.CENTER, spacing: { before: 2200, after: 400 } }),
  para(run(documentTitle, { bold: true, size: 44, color: "203746" }), { heading: HeadingLevel.TITLE, alignment: AlignmentType.CENTER, spacing: { after: 500 } }),
  para(run(documentSubtitle, { size: 24, color: "557180" }), { alignment: AlignmentType.CENTER, spacing: { after: 240 } }),
  para(run("2026 年 11 月 9 日", { size: 24, color: "557180" }), { alignment: AlignmentType.CENTER, spacing: { after: 1200 } }),
  para(run(isBridgeGuide ? "真实协议与边界验证，不把健康检查或 mock 冒称为定理证明。" : "可追溯采样，不宣称全球穷尽；候选数量不等于可用项目数量。", { size: 22, color: "557180" }), { alignment: AlignmentType.CENTER }),
  new Paragraph({ children: [new PageBreak()] }),
  para(run("目录", { bold: true, size: 30, color: "203746" }), { alignment: AlignmentType.CENTER }),
  para(run("打开 Word/WPS 后更新目录域可刷新页码。", { size: 18, color: "6D7D86", italics: true }), { alignment: AlignmentType.CENTER }),
  toc,
  new Paragraph({ children: [new PageBreak()] }),
];

for (const block of blocks) {
  if (block.type === "heading") {
    if (block.level === 1) continue;
    children.push(para(rich(block.text, block.level === 2 ? 30 : 26), { heading: block.level === 2 ? HeadingLevel.HEADING_1 : HeadingLevel.HEADING_2, spacing: { before: 300, after: 150 } }));
  } else if (block.type === "paragraph") {
    children.push(para(rich(block.text), { indent: { firstLine: convertInchesToTwip(0.33) } }));
  } else if (block.type === "image") {
    const imagePath = path.resolve(sourceDir, block.path);
    const data = fs.readFileSync(imagePath);
    const dimensions = block.path.includes("platform") ? [1584, 837] : [1800, 940];
    const width = 620;
    children.push(para(new ImageRun({ type: "png", data, transformation: { width, height: Math.round(width * dimensions[1] / dimensions[0]) } }), { alignment: AlignmentType.CENTER }));
  } else if (block.type === "table") {
    const count = block.rows[0].length;
    const first = block.rows[0][0];
    let widths;
    if (count === 3 && first === "平台") widths = [1600, 1200, 6560];
    else if (count === 3) widths = [2500, 2500, 4360];
    else if (count === 5 && first === "项目") widths = [2300, 1300, 900, 1550, 3310];
    else widths = [2100, 950, 1100, 650, 4560];
    children.push(new Table({
      width: { size: 9360, type: WidthType.DXA }, columnWidths: widths,
      rows: block.rows.map((row, rowIndex) => new TableRow({
        tableHeader: rowIndex === 0,
        children: row.map((value, column) => new TableCell({
          width: { size: widths[column], type: WidthType.DXA },
          margins: { top: 90, bottom: 90, left: 90, right: 90 },
          shading: rowIndex === 0 ? { type: ShadingType.CLEAR, fill: "E6EEF1" } : undefined,
          children: [para(rich(value, 16), { spacing: { after: 40, line: 220 } })],
        })),
      })),
    }));
    children.push(para(run("", { size: 10 }), { spacing: { after: 100 } }));
  }
}

const doc = new Document({
  creator: "garden-ecosystem contributors",
  title: documentTitle,
  description: isBridgeGuide ? "受控 stdio、真实 Lean 健康检查与 Next.js 桥接验证" : "公开代码平台调研、许可证边界与花园适配层总体设计",
  features: { updateFields: true },
  styles: {
    default: { document: { run: { font, size: 22 } } },
    paragraphStyles: [{ id: "TOC1", name: "toc 1", basedOn: "Normal", next: "Normal", quickFormat: true,
      run: { font, size: 20 }, paragraph: { spacing: { after: 120 } } }],
  },
  sections: [{
    properties: { page: { margin: { top: 1200, right: 1200, bottom: 1200, left: 1200 } } },
    headers: { default: new Header({ children: [para(run(isBridgeGuide ? "千界花园 · 受控桥接与真实验证" : "千界花园 · 开源生态调研与总体设计", { size: 17, color: "557180" }), { alignment: AlignmentType.CENTER })] }) },
    footers: { default: new Footer({ children: [para(new TextRun({ children: [PageNumber.CURRENT] }), { alignment: AlignmentType.CENTER })] }) },
    children,
  }],
});
fs.writeFileSync(outputPath, await Packer.toBuffer(doc));
console.log(JSON.stringify({ tables: blocks.filter((b) => b.type === "table").length, images: blocks.filter((b) => b.type === "image").length, headings: tocEntries.length }));
