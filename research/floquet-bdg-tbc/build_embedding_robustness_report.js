import fs from "node:fs";
import path from "node:path";
import {
  AlignmentType, Document, Footer, FootnoteReferenceRun, Header, HeadingLevel,
  ImageRun, ImportedXmlComponent, Math as MathEquation, MathRun, Packer,
  PageBreak, PageNumber, Paragraph, ShadingType, Table, TableCell, TableRow,
  TextRun, WidthType,
} from "docx";

const outputPath = process.argv[2];
if (!outputPath) throw new Error("Usage: node build_embedding_robustness_report.js /absolute/path/report.docx");
const root = path.dirname(outputPath);
const analysis = JSON.parse(fs.readFileSync(path.join(root, "embedding_robustness_analysis.json"), "utf8"));
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
const cell = (text, index, widths, header, size = 10) => new TableCell({
  children: [para(run(text, { size, bold: header }), { spacing: { after: 0, line: 165 } })],
  width: { size: widths[index], type: WidthType.DXA }, margins: { top: 20, bottom: 20, left: 35, right: 35 },
  shading: header ? { type: ShadingType.CLEAR, fill: palette.fill } : undefined,
});
const makeTable = (headers, rows, widths, size = 10) => new Table({
  width: { size: widths.reduce((a, b) => a + b, 0), type: WidthType.DXA }, columnWidths: widths,
  rows: [new TableRow({ tableHeader: true, cantSplit: true, children: headers.map((text, index) => cell(text, index, widths, true, size)) }), ...rows.map((row) => new TableRow({ cantSplit: true, children: row.map((text, index) => cell(text, index, widths, false, size)) }))],
});
const equation = (text) => para(new MathEquation({ children: [new MathRun(text)] }), { alignment: AlignmentType.CENTER, spacing: { before: 55, after: 70 } });
const footnote = (text) => para(run(text, { size: 15 }), { spacing: { after: 30, line: 190 } });
const fmt = (value) => Number(value).toPrecision(6).replace(/\.0+$/, "");
const comparisonRows = analysis.cases.flatMap((item) => item.method_comparisons.map((row) => [
  `${item.seed}／${item.strength}`, String(row.m), fmt(row.linear_diagonal_score), fmt(row.cell_average_diagonal_score), fmt(row.diagonal_score_change_cell_minus_linear), fmt(row.linear_swapped_score), fmt(row.cell_average_swapped_score), String(row.same_dominant_assignment),
]));
const comparisonTable = makeTable(["seed／r", "M", "线性同谱秩", "单元平均同谱秩", "单元平均−线性", "线性交换", "单元平均交换", "分配一致"], comparisonRows, [750, 550, 1450, 1450, 1400, 1350, 1350, 1606], 8);
const matrixTable = (item) => {
  const grid = item.methods.cell_average.grids[2];
  const rows = [0, 1].map((i) => [`第${i + 1}对`, ...[0, 1].map((j) => `O=${fmt(grid.overlap_matrix[i][j].overlap)}`)]);
  return makeTable(["N400＼N600", "第1对", "第2对"], rows, [1800, 4053, 4053], 10);
};
const titles = ["一、两种共同表示的逐网格比较", "二、分配方向与重叠幅度", "三、单元平均矩阵与解释边界"];
const children = [
  para(run("Floquet-BdG 共同表示稳健性", { bold: true, size: 34, color: palette.dark }), { heading: HeadingLevel.TITLE, alignment: AlignmentType.CENTER, spacing: { before: 600, after: 220 } }),
  para(run("方向一致不等于高保真态对应", { bold: true, size: 25, color: palette.primary }), { alignment: AlignmentType.CENTER, spacing: { after: 230 } }),
  para(run("线性点值 · 分片常数单元平均 · 同一本征矢", { size: 20, color: palette.light }), { alignment: AlignmentType.CENTER, spacing: { after: 260 } }),
  para(run("2026-11-11　不新增类别，不补算体 winding，未计算 N=640", { size: 19, color: palette.accent }), { alignment: AlignmentType.CENTER, spacing: { after: 300 } }),
  heading("目录"),
  para(run("以下页码为可见缓存；在 Word/WPS 中更新域可刷新。", { size: 17, italics: true, color: palette.light })),
  toc(titles.map((title, index) => ({ title, level: 1, page: index + 2 }))),
  pageBreak(),

  heading(titles[0]),
  citedBody("两种方法使用同一批本征矢、同一组 M=1200／2400／4800 和同一个主子空间重叠定义。线性点值沿用上一轮实现；单元平均把原始格点的复数旋量分量视为该单元上的常数，再做 QR。", 1),
  equation("E_cell(V)_(j,s) = V_(floor(j N/M),s),  Q = orth(E(V)),  O_ij = (s_1² + s_2²) / 2"),
  para(run("嵌套网格 M/N 为整数，因此每个原始值恰好进入 M/N 个目标单元。这里比较的是两种共同表示，不是选择更符合预期的方法。", { size: 18, color: palette.light })),
  comparisonTable,
  para(run(`线性结果最大复现差 ${analysis.max_linear_reproduction_error.toExponential(1)}；冻结剖面最大误差 ${analysis.max_profile_absolute_error.toExponential(3)}。`, { size: 17, color: palette.light })),
  pageBreak(),

  heading(titles[1]),
  citedBody("对数坐标只改变显示方式，不改变重叠数值。同谱秩与交换分配分别比较，不把次近对提升为拓扑端点。", 2),
  para(new ImageRun({ type: "png", data: fs.readFileSync(path.join(root, "embedding-robustness.png")), transformation: { width: 500, height: Math.round(500 * 1530 / 2151) } }), { alignment: AlignmentType.CENTER, keepNext: true }),
  para(run("图 1　两种嵌入的同谱秩与交换分配得分。绿色为线性点值，棕色为单元平均。", { size: 16, italics: true }), { alignment: AlignmentType.CENTER }),
  body(`18个方法×案例×网格组合中，同谱秩分配占优 ${analysis.summary.diagonal_dominant_count}/18；M=4800 上两种方法主导分配一致 ${analysis.summary.finest_same_assignment_count}/3。同谱秩得分最大绝对变化为 ${fmt(analysis.summary.max_absolute_diagonal_score_change)}。`),
  body("单元平均的同谱秩得分在9个比较中均略低。方向在当前两种方法下稳定，但幅度并非不变，绝对重叠仍然弱。"),
  pageBreak(),

  heading(titles[2]),
  ...analysis.cases.flatMap((item) => [heading(`seed=${item.seed}，r=${item.strength}：单元平均，M=4800`, 2), matrixTable(item)]),
  body("三个对照的最细网格单元平均同谱秩得分依次约为0.0456978、0.00118967、0.00516477。相对谱秩优势仍未形成高保真对应证据。"),
  citedBody("方法方向一致不支持表示不变性；数值相近也不等于物理态唯一确定。若方向改变，应先报告嵌入依赖，而不是挑选有利表示。", 3),
  body("本轮没有证明同一物理态、排序交换、网格收敛、次近对拓扑性、体 winding、材料实现或热力学极限。原类别及此前响应计数未改变。"),
  body("复现：python research/floquet-bdg-tbc/analyze_embedding_robustness.py。协议、两种完整矩阵、逐网格差值和来源哈希保存在 embedding_robustness_analysis.json。"),
  para(run("证据边界：六个既有单元、两种共同表示、三个网格的描述性稳健性检验。", { size: 18, color: palette.accent })),
];

const document = new Document({
  creator: "TOE-SYLVA",
  title: "Floquet-BdG 共同表示稳健性",
  description: "线性点值与分片常数单元平均嵌入的跨尺寸子空间比较。",
  features: { updateFields: true },
  styles: { paragraphStyles: [1, 2].map((level) => ({ id: `TOC${level}`, name: `TOC ${level}`, basedOn: "Normal", next: "Normal", quickFormat: true, run: { font, size: 19, color: palette.dark }, paragraph: { spacing: { after: 70, line: 240 }, indent: { left: (level - 1) * 360 } } })) },
  footnotes: {
    1: { children: [footnote("embedding_robustness_protocol.json. Both methods reuse the same eigenvectors, grids and principal-subspace metric.")] },
    2: { children: [footnote("embedding_robustness_analysis.json. Previous linear results are reproduced exactly and frozen profile errors remain below 1e-10.")] },
    3: { children: [footnote("All eighteen method-case-grid combinations favor diagonal assignment, but this is not representation invariance or physical state tracking.")] },
  },
  sections: [{
    properties: { page: { margin: { top: 900, bottom: 900, left: 1000, right: 1000 } } },
    headers: { default: new Header({ children: [para(run("TOE-SYLVA · Floquet-BdG · 共同表示稳健性", { size: 17, color: palette.primary }), { alignment: AlignmentType.CENTER })] }) },
    footers: { default: new Footer({ children: [para(new TextRun({ children: [PageNumber.CURRENT], font, size: 17 }), { alignment: AlignmentType.CENTER })] }) },
    children,
  }],
});
fs.writeFileSync(outputPath, await Packer.toBuffer(document));
