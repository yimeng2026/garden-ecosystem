import fs from "node:fs";
import path from "node:path";
import {
  AlignmentType, Document, Footer, FootnoteReferenceRun, Header, HeadingLevel,
  ImageRun, ImportedXmlComponent, Math as MathEquation, MathFraction, MathRun,
  MathSubScript, MathSuperScript, Packer, PageBreak, PageNumber, Paragraph,
  ShadingType, Table, TableCell, TableRow, TextRun, WidthType,
} from "docx";

const outputPath = process.argv[2];
if (!outputPath) throw new Error("Usage: node build_matched_beta_report.js /absolute/path/report.docx");
const root = path.dirname(outputPath);
const analysis = JSON.parse(fs.readFileSync(path.join(root, "matched_beta_control_analysis.json"), "utf8"));
const summary = analysis.summary;
const font = { ascii: "Times New Roman", hAnsi: "Times New Roman", cs: "Times New Roman", eastAsia: "SimSun" };
const palette = { dark: "293B40", primary: "356A64", accent: "A25B3F", light: "687A7E", fill: "EDF3F1" };
const run = (text, options = {}) => new TextRun({ text: String(text), font, size: 20, ...options });
const para = (children, options = {}) => new Paragraph({ spacing: { after: 100, line: 270 }, ...options, children: Array.isArray(children) ? children : [children] });
const body = (text) => para(run(text), { indent: { firstLine: 400 } });
const citedBody = (text, id) => para([run(text), new FootnoteReferenceRun(id)], { indent: { firstLine: 400 } });
const heading = (text, level = 1) => para(run(text, { bold: true, size: level === 1 ? 29 : 23, color: palette.dark }), { heading: level === 1 ? HeadingLevel.HEADING_1 : HeadingLevel.HEADING_2, spacing: { before: 170, after: 100 }, keepNext: true });
const pageBreak = () => new Paragraph({ children: [new PageBreak()] });
const xmlEscape = (value) => String(value).replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;");
const toc = (entries) => {
  const cached = entries.map(({ title, level, page }) => `<w:p><w:pPr><w:pStyle w:val="TOC${level}"/><w:tabs><w:tab w:val="right" w:leader="dot" w:pos="9000"/></w:tabs><w:ind w:left="${Math.max(0, level - 1) * 360}"/></w:pPr><w:r><w:t>${xmlEscape(title)}</w:t></w:r><w:r><w:tab/></w:r><w:r><w:t>${page}</w:t></w:r></w:p>`).join("");
  return ImportedXmlComponent.fromXmlString(`<w:sdt xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:sdtPr><w:alias w:val="目录"/></w:sdtPr><w:sdtContent><w:p><w:r><w:fldChar w:fldCharType="begin" w:dirty="true"/><w:instrText xml:space="preserve"> TOC \\o &quot;1-2&quot; \\h \\z \\u </w:instrText><w:fldChar w:fldCharType="separate"/></w:r></w:p>${cached}<w:p><w:r><w:fldChar w:fldCharType="end"/></w:r></w:p></w:sdtContent></w:sdt>`).root[0];
};
const cell = (text, index, widths, header, size = 9) => new TableCell({
  children: [para(run(text, { size, bold: header }), { spacing: { after: 40, line: 240, lineRule: "auto" } })],
  width: { size: widths[index], type: WidthType.DXA }, margins: { top: 80, bottom: 80, left: 60, right: 60 },
  shading: header ? { type: ShadingType.CLEAR, fill: palette.fill } : undefined,
});
const makeTable = (headers, rows, widths, size = 9) => new Table({
  width: { size: widths.reduce((a, b) => a + b, 0), type: WidthType.DXA }, columnWidths: widths,
  rows: [new TableRow({ tableHeader: true, cantSplit: true, children: headers.map((text, index) => cell(text, index, widths, true, size)) }), ...rows.map((row) => new TableRow({ cantSplit: true, children: row.map((text, index) => cell(text, index, widths, false, size)) }))],
});
const equation = (children) => para(new MathEquation({ children: Array.isArray(children) ? children : [new MathRun(children)] }), { alignment: AlignmentType.CENTER, spacing: { before: 55, after: 70 } });
const sub = (base, subscript) => new MathSubScript({ children: [new MathRun(base)], subScript: [new MathRun(subscript)] });
const sup = (base, superScript) => new MathSuperScript({ children: [new MathRun(base)], superScript: [new MathRun(superScript)] });
const subSup = (base, subscript, superScript) => new MathSuperScript({ children: [sub(base, subscript)], superScript: [new MathRun(superScript)] });
const footnote = (text) => para(run(text, { size: 15 }), { spacing: { after: 30, line: 190 } });
const fmt = (value) => Number(value).toPrecision(6).replace(/\.0+$/, "");
const spectrumTable = makeTable(["N", "最近对中心", "次近对中心", "中心间隔", "端点权重", "L50", "诊断"], analysis.cells.map((cell) => [String(cell.n), fmt(cell.pairs[0].center), fmt(cell.pairs[1].center), fmt(cell.center_separation), fmt(cell.pairs[0].edge_weight), String(cell.pairs[0].L50), String(cell.pairs[0].diagnostic_joint_pass)]), [650, 1700, 1700, 1600, 1300, 800, 2156], 8);
const assignmentRows = ["linear_point", "cell_average"].flatMap((method) => analysis.methods[method].grids.map((grid) => [method, String(grid.m), fmt(grid.diagonal_score), fmt(grid.swapped_score), grid.dominant_assignment]));
const assignmentTable = makeTable(["方法", "M", "同谱秩得分", "交换得分", "主导分配"], assignmentRows, [2200, 1000, 2400, 2400, 1906], 9);
const comparisonTable = makeTable(["无序实现", "线性点值", "单元平均", "解释"], [
  ["旧候选（不同实现）", analysis.old_candidate_comparison.old_assignments.linear_point, analysis.old_candidate_comparison.old_assignments.cell_average, "仅登记，不作相减"],
  ["共同β(x)控制", analysis.old_candidate_comparison.control_assignments.linear_point, analysis.old_candidate_comparison.control_assignments.cell_average, "同谱秩主导3/3网格"],
], [2600, 1900, 1900, 3506], 9);
const titles = ["一、共同无序剖面与谱结构", "二、跨尺寸与跨表示图证据", "三、实现依赖与解释边界"];
const children = [
  para(run("Floquet-BdG 共同无序剖面尺寸隔离", { bold: true, size: 34, color: palette.dark }), { heading: HeadingLevel.TITLE, alignment: AlignmentType.CENTER, spacing: { before: 600, after: 220 } }),
  para(run("同一主剖面，而不是仅共享随机种子名称", { bold: true, size: 25, color: palette.primary }), { alignment: AlignmentType.CENTER, spacing: { after: 230 } }),
  para(run("seed=6，r=0.05 · N=400／600 · 两个新控制单元", { size: 20, color: palette.light }), { alignment: AlignmentType.CENTER, spacing: { after: 260 } }),
  para(run("2026-11-11　不新增类别，不补算体 winding，未计算 N=640", { size: 19, color: palette.accent }), { alignment: AlignmentType.CENTER, spacing: { after: 300 } }),
  heading("目录"),
  para(run("以下页码为可见缓存；在 Word/WPS 中更新域可刷新。", { size: 17, italics: true, color: palette.light })),
  toc(titles.map((title, index) => ({ title, level: 1, page: index + 2 }))),
  pageBreak(),

  heading(titles[0]),
  citedBody("主网格 M=4800 只生成一次无序剖面。每个粗格点取其覆盖主格点的算术平均，形成 N=400 和 N=600 的嵌套采样。", 1),
  equation([sub("β", "N,j"), new MathRun(" = "), new MathFraction({ numerator: [new MathRun("1")], denominator: [new MathRun("K")] }), sub("Σ", "k∈B_N,j"), sup("β", "*")]),
  para(run("其中 K=4800/N，B_N,j 是第 j 个粗格点覆盖的主格点集合，β* 为主剖面。两种采样的块平均误差均为 0。", { size: 18, color: palette.light })),
  equation([sub("O", "ij"), new MathRun(" = "), new MathFraction({ numerator: [subSup("s", "1", "2"), new MathRun(" + "), subSup("s", "2", "2")], denominator: [new MathRun("2")] })]),
  spectrumTable,
  heading("两种共同表示的三个网格", 2),
  assignmentTable,
  para(run("跨尺寸重叠不做归一化修正，也不将跨表示自一致性用作校正因子。", { size: 17, color: palette.light }), { spacing: { before: 120, after: 100, line: 270 } }),
  pageBreak(),

  heading(titles[1]),
  citedBody("同一主无序剖面下，两种共同表示在 M=1200、2400、4800 上均为同谱秩主导；这只是当前控制下的数值关系。", 2),
  para(new ImageRun({ type: "png", data: fs.readFileSync(path.join(root, "matched-beta-control.png")), transformation: { width: 500, height: Math.round(500 * 1378 / 2042) } }), { alignment: AlignmentType.CENTER, keepNext: true }),
  para(run("图 1　嵌套采样、跨尺寸分配、跨表示自一致性及同N秩间控制。右下图显示下限1e-18，JSON保留原值。", { size: 16, italics: true }), { alignment: AlignmentType.CENTER }),
  body(`跨表示自一致性为 ${fmt(summary.min_representation_fidelity)}–${fmt(summary.max_representation_fidelity)}；原生秩间重叠最大 ${fmt(summary.max_native_off_diagonal)}，单元平均最大 ${fmt(summary.max_cell_average_off_diagonal)}。`),
  body(`线性点值秩间重叠最大 ${fmt(summary.max_linear_point_off_diagonal)}，继续保留嵌入诱导串扰的可能性，不把它误写成原始谱交换。`),
  pageBreak(),

  heading(titles[2]),
  comparisonTable,
  para(run("旧交换候选与共同β(x)控制属于不同无序实现。分配方向的变化只能说明实现依赖性，不能把两次计算直接相减并命名为尺寸效应或谱交叉。"), { indent: { firstLine: 400 }, spacing: { before: 120, after: 100, line: 270 } }),
  citedBody("本轮闭合的是共同β(x)定向控制，而不是普遍尺寸律。下一步应把同一协议扩展到预登记种子和强度，避免后验选择有利剖面。", 3),
  body("不宣称尺寸不变、真实态交换、避免交叉、次近对拓扑性或体winding。复现：python research/floquet-bdg-tbc/analyze_matched_beta_control.py。"),
  para(run("证据边界：两个新控制单元的描述性尺寸隔离；不做统计显著性、连续路径或热力学极限推断。", { size: 18, color: palette.accent })),
];

const document = new Document({
  creator: "TOE-SYLVA",
  title: "Floquet-BdG 共同无序剖面尺寸隔离",
  description: "共同嵌套无序剖面下的N=400/600定向尺寸对照。",
  features: { updateFields: true },
  styles: { paragraphStyles: [1, 2].map((level) => ({ id: `TOC${level}`, name: `TOC ${level}`, basedOn: "Normal", next: "Normal", quickFormat: true, run: { font, size: 19, color: palette.dark }, paragraph: { spacing: { after: 70, line: 240 }, indent: { left: (level - 1) * 360 } } })) },
  footnotes: {
    1: { children: [footnote("matched_beta_control_protocol.json. One fixed M=4800 master profile is coarsened by exact nested block means; no new category or bulk winding.")] },
    2: { children: [footnote("matched_beta_control_analysis.json. Both embeddings favor diagonal assignment on all three grids for this particular matched realization.")] },
    3: { children: [footnote("The previous swap candidate is a different disorder realization and cannot be subtracted from this control as a size effect.")] },
  },
  sections: [{
    properties: { page: { margin: { top: 900, bottom: 900, left: 1000, right: 1000 } } },
    headers: { default: new Header({ children: [para(run("TOE-SYLVA · Floquet-BdG · 共同无序剖面尺寸隔离", { size: 17, color: palette.primary }), { alignment: AlignmentType.CENTER })] }) },
    footers: { default: new Footer({ children: [para(new TextRun({ children: [PageNumber.CURRENT], font, size: 17 }), { alignment: AlignmentType.CENTER })] }) },
    children,
  }],
});
fs.writeFileSync(outputPath, await Packer.toBuffer(document));
