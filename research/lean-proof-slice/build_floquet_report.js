import fs from "node:fs";
import path from "node:path";
import {
  AlignmentType, Document, Footer, FootnoteReferenceRun, Header, HeadingLevel,
  ImageRun, ImportedXmlComponent, Math as MathEquation, MathRun, Packer,
  PageBreak, PageNumber, Paragraph, ShadingType, Table, TableCell, TableRow,
  TextRun, WidthType,
} from "docx";

const outputPath = process.argv[2];
if (!outputPath) throw new Error("Usage: node build_floquet_report.js /absolute/path/FLOQUET_APPROXIMATION.docx");
const audit = path.dirname(outputPath);
const data = JSON.parse(fs.readFileSync(path.join(audit, "floquet-approximation.json"), "utf8"));
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
const titles = ["一、显式误差界与零误差证明", "二、原文件与物理命题边界", "三、工具链与后续"];
const children = [
  para(run("Floquet 显式误差界语义切片", { bold: true, size: 38, color: palette.dark }), { heading: HeadingLevel.TITLE, alignment: AlignmentType.CENTER, spacing: { before: 600, after: 220 } }),
  para(run("零误差与精确等式的双向证明", { bold: true, size: 29, color: palette.primary }), { alignment: AlignmentType.CENTER, spacing: { after: 280 } }),
  para(run("显式误差界 · 无 HasEquiv 实例 · 不证明 Floquet 增强", { size: 21, color: palette.light }), { alignment: AlignmentType.CENTER, spacing: { after: 220 } }),
  para(run("2026-11-11　语义切片通过 ≠ 物理证明", { size: 19 }), { alignment: AlignmentType.CENTER, spacing: { after: 330 } }),
  heading("目录"),
  para(run("以下页码为可见缓存；在 Word/WPS 中更新域可刷新。", { size: 17, italics: true, color: palette.light })),
  toc(titles.map((title, index) => ({ title, level: 1, page: [2, 3, 3][index] }))),
  pageBreak(),

  heading(titles[0]),
  equation("|ω_drive − 2Δ/ℏ| = 0 ↔ ω_drive = 2Δ/ℏ"),
  citedBody("DriveApprox 在真实 Lean 4.35.0 下编译退出码为 0。driveApprox_zero_exact 从零误差推出精确等式，driveApprox_of_exact 从精确等式推出零误差界；三个定理均只依赖标准三公理，没有 sorryAx。", 1),
  makeTable(
    ["定理", "语义", "sorryAx", "公理依赖"],
    [
      ["driveApprox_unfold", "定义展开", "无", "propext、Classical.choice、Quot.sound"],
      ["driveApprox_zero_exact", "零误差推出精确等式", "无", "propext、Classical.choice、Quot.sound"],
      ["driveApprox_of_exact", "精确等式推出零误差", "无", "propext、Classical.choice、Quot.sound"],
    ],
    [2700, 2600, 1100, 3106], 13,
  ),
  body("DriveApprox 使用 |ω_drive - 2 * Δ / ℏ| ≤ ε 的显式绝对误差界，不构造 HasEquiv 实例。零误差只是精确等式的特例，不能替代 Floquet 增强命题。"),
  para(new ImageRun({ type: "png", data: fs.readFileSync(path.join(audit, "floquet-approximation.png")), transformation: { width: 610, height: 283 } }), { alignment: AlignmentType.CENTER, keepNext: true }),
  para(run("图 1　显式误差界与未闭合命题。左侧为已验证语义，右侧为 Floquet 增强、原文件与物理实验的开放边界。", { size: 18, italics: true }), { alignment: AlignmentType.CENTER }),
  pageBreak(),

  heading(titles[1]),
  citedBody("原文件未修改，原文件直译仍不兼容，原三条定理的 sorryAx 审计仍不可用。Floquet 增强、物理有效性、材料预测、数值模型和实验验证均未验证。", 2),
  makeTable(
    ["开放边界", "状态", "后续"],
    [
      ["floquet_enhancement_proven", "false", "需要独立的 Floquet 物理推导和证据"],
      ["physical_validity_verified", "false", "需要物理假设、参数与实验验证"],
      ["original_file_compiled", "false", "先清偿原文件语法与模块兼容性"],
      ["original_theorems_proven", "false", "需要真实定义、命题与证明，不得以语义切片替代"],
    ],
    [3200, 1000, 5306], 14,
  ),
  heading(titles[2]),
  citedBody("Lean、Lake 和 Mathlib 均使用固定版本，D 盘隔离构建副本不修改系统 PATH。官方 elan 资产已先核对大小和 SHA-256 后执行。", 3),
  makeTable(
    ["工具与边界", "当前结果", "说明"],
    [
      ["Lean", "4.35.0", "真实误差语义编译与 #print axioms"],
      ["Mathlib", data.toolchain.mathlib_rev, "固定提交，不使用浮动分支"],
      ["构建位置", data.toolchain.build_copy, "D 盘隔离副本；系统 PATH 未修改"],
      ["原文件", data.original.sha256, "复制一致；源文件未修改"],
    ],
    [2100, 4800, 2606], 12,
  ),
  body("后续需要独立的 Floquet 物理推导：明确驱动、配对与温度之间的实际关系，再决定增强命题是否成立。材料预测和实验复现另行推进。"),
  body("实际命令与原始输出见 floquet-run.log、floquet-compile.log 和 floquet-approximation.json。本切片只完成误差语义清偿，不宣称项目级证明或实验验证完成。"),
];

const document = new Document({
  creator: "TOE-SYLVA",
  title: "Floquet 显式误差界语义切片：零误差与精确等式",
  description: "显式误差界、零误差双向证明、真实编译和开放物理边界。",
  features: { updateFields: true },
  styles: {
    paragraphStyles: [1, 2].map((level) => ({
      id: `TOC${level}`, name: `TOC ${level}`, basedOn: "Normal", next: "Normal", quickFormat: true,
      run: { font, size: 19, color: palette.dark },
      paragraph: { spacing: { after: 70, line: 240 }, indent: { left: (level - 1) * 360 } },
    })),
  },
  footnotes: {
    1: { children: [footnote("Source: floquet-compile.log; actual Lean compilation and #print axioms output for DriveApprox and zero-error proofs.")] },
    2: { children: [footnote("Source: room_temp_sc_Formalization.lean and original-compile.log; original hash, source incompatibility and static proof debt.")] },
    3: { children: [footnote("Source: bootstrap-result.json; verified official elan asset and D: isolated Lean/Lake toolchain.")] },
  },
  sections: [{
    properties: { page: { margin: { top: 1050, bottom: 1050, left: 1050, right: 1050 } } },
    headers: { default: new Header({ children: [para(run("TOE-SYLVA · Floquet 误差界 · 语义通过≠增强证明", { size: 17, color: palette.primary }), { alignment: AlignmentType.CENTER })] }) },
    footers: { default: new Footer({ children: [para(new TextRun({ children: [PageNumber.CURRENT], font, size: 17 }), { alignment: AlignmentType.CENTER })] }) },
    children,
  }],
});

fs.writeFileSync(outputPath, await Packer.toBuffer(document));
