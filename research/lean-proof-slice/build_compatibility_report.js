import fs from "node:fs";
import path from "node:path";
import {
  AlignmentType, Document, Footer, FootnoteReferenceRun, Header, HeadingLevel,
  ImageRun, ImportedXmlComponent, Math as MathEquation, MathRun, Packer,
  PageBreak, PageNumber, Paragraph, ShadingType, Table, TableCell, TableRow,
  TextRun, WidthType,
} from "docx";

const outputPath = process.argv[2];
if (!outputPath) throw new Error("Usage: node build_compatibility_report.js /absolute/path/COMPATIBILITY_ERRATA.docx");
const audit = path.dirname(outputPath);
const data = JSON.parse(fs.readFileSync(path.join(audit, "compatibility-issues.json"), "utf8"));
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
const titles = ["一、四类真实编译错误", "二、清偿动作与验证顺序", "三、开放边界与后续"];
const children = [
  para(run("Lean 原文件兼容性勘误", { bold: true, size: 38, color: palette.dark }), { heading: HeadingLevel.TITLE, alignment: AlignmentType.CENTER, spacing: { before: 600, after: 220 } }),
  para(run("四类开放问题与清偿动作", { bold: true, size: 29, color: palette.primary }), { alignment: AlignmentType.CENTER, spacing: { after: 280 } }),
  para(run("直接日志证据 · 原文件只读 · 未解决", { size: 21, color: palette.light }), { alignment: AlignmentType.CENTER, spacing: { after: 220 } }),
  para(run("2026-11-11　勘误不等于修复或物理证明", { size: 19 }), { alignment: AlignmentType.CENTER, spacing: { after: 330 } }),
  heading("目录"),
  para(run("以下页码为可见缓存；在 Word/WPS 中更新域可刷新。", { size: 17, italics: true, color: palette.light })),
  toc(titles.map((title, index) => ({ title, level: 1, page: [2, 3, 3][index] }))),
  pageBreak(),

  heading(titles[0]),
  equation("4 issues = 4 open"),
  citedBody("原文件直接编译退出码为 1。四类问题均来自实际原始日志，原文件和复制件的 SHA-256 保持一致，未修改源文件。", 1),
  makeTable(
    ["问题", "直接证据", "状态", "不能升级为"],
    data.issues.map((row) => [row.id, row.evidence, row.status, "原文件可编译或物理命题已证明"]),
    [2000, 3800, 1000, 2706], 13,
  ),
  citedBody("原文件的哈希与复制件一致，编译失败状态为 source_incompatible；因此原三条定理的 sorryAx 审计不可用，而不是已确认或已清除。", 4),
  para(new ImageRun({ type: "png", data: fs.readFileSync(path.join(audit, "lean-proof-slice.png")), transformation: { width: 610, height: 305 } }), { alignment: AlignmentType.CENTER, keepNext: true }),
  para(run("图 1　清洁定义切片与原文件结果分轨。图中只展示定义编译差异，不表示错误已经清偿。", { size: 18, italics: true }), { alignment: AlignmentType.CENTER }),
  pageBreak(),

  heading(titles[1]),
  makeTable(
    ["问题", "清偿动作", "验收要求"],
    [
      ["euler_mascheroni", data.issues[0].next, "核对真实标识符、import 和数值语义"],
      ["lambda_identifier", data.issues[1].next, "保持参数顺序与物理含义，真实编译"],
      ["omega_d_binding", data.issues[2].next, "明确函数类型、单位和物理定义，拒绝 autoImplicit 猜测"],
      ["has_equiv_real", data.issues[3].next, "选择等式、极限或显式误差估计，禁止虚假实例"],
    ],
    [2100, 5200, 2206], 13,
  ),
  citedBody("Mathlib 当前源码中实际存在 Real.eulerMascheroniConstant，已在 Gamma/Digamma.lean 中直接定位；不是凭记忆选择名称。", 2),
  body("执行顺序：先修常量、绑定变量和显式类型，使最小定义可解析；再处理约等号的命题语义。每一步都必须重新运行真实 Lean，并记录命令、退出码和依赖。"),
  citedBody("清洁定义切片已独立通过真实编译，但它只验证定义展开，不是对原文件这些错误或三条物理定理的修复。", 3),
  heading(titles[2]),
  makeTable(
    ["开放边界", "状态", "后续"],
    [
      ["original_file_compiled", "false", "先完成源码兼容清偿，再运行原文件编译"],
      ["original_theorems_proven", "false", "需要真实定义、命题与证明，不得以 rfl 冒充"],
      ["physical_validity_verified", "false", "需要物理推导、原始参数和实验证据"],
      ["all_errata_resolved", "false", "全部项目真实验收前保持 open"],
    ],
    [3000, 1000, 5506], 14,
  ),
  body("本勘误只登记错误与清偿动作，不修改原文件，不新增公理、证明位 sorry 或物理结论。兼容性、物理证明和实验复现均继续作为未竟工作。"),
];

const document = new Document({
  creator: "TOE-SYLVA",
  title: "Lean 原文件兼容性勘误：四类开放问题",
  description: "真实错误、直接日志、清偿动作和未解决边界。",
  features: { updateFields: true },
  styles: {
    paragraphStyles: [1, 2].map((level) => ({
      id: `TOC${level}`, name: `TOC ${level}`, basedOn: "Normal", next: "Normal", quickFormat: true,
      run: { font, size: 19, color: palette.dark },
      paragraph: { spacing: { after: 70, line: 240 }, indent: { left: (level - 1) * 360 } },
    })),
  },
  footnotes: {
    1: { children: [footnote("Source: original-compile.log; actual original compilation exit code and direct error markers.")] },
    2: { children: [footnote("Source: Mathlib/Analysis/SpecialFunctions/Gamma/Digamma.lean; Real.eulerMascheroniConstant located directly in source.")] },
    3: { children: [footnote("Source: proof-slice.json and clean-compile.log; independent clean definition results only.")] },
    4: { children: [footnote("Source: room_temp_sc_Formalization.lean and read-only copy; original hash and three static sorry lines.")] },
  },
  sections: [{
    properties: { page: { margin: { top: 1050, bottom: 1050, left: 1050, right: 1050 } } },
    headers: { default: new Header({ children: [para(run("TOE-SYLVA · Lean 兼容性勘误 · 开放问题", { size: 17, color: palette.primary }), { alignment: AlignmentType.CENTER })] }) },
    footers: { default: new Footer({ children: [para(new TextRun({ children: [PageNumber.CURRENT], font, size: 17 }), { alignment: AlignmentType.CENTER })] }) },
    children,
  }],
});

fs.writeFileSync(outputPath, await Packer.toBuffer(document));
