import fs from "node:fs";
import path from "node:path";
import {
  AlignmentType, Document, Footer, FootnoteReferenceRun, Header, HeadingLevel,
  ImageRun, ImportedXmlComponent, Math as MathEquation, MathFraction, MathRun,
  MathSubScript, MathSuperScript, Packer, PageBreak, PageNumber, Paragraph,
  ShadingType, Table, TableCell, TableRow, TextRun, WidthType,
} from "docx";

const outputPath = process.argv[2];
if (!outputPath) throw new Error("Usage: node build_matched_beta_batch_a_report.js /absolute/path/report.docx");
const root = path.dirname(outputPath);
const analysis = JSON.parse(fs.readFileSync(path.join(root, "matched_beta_batch_a_analysis.json"), "utf8"));
const independent = JSON.parse(fs.readFileSync(path.join(root, "matched_beta_batch_a_independent.json"), "utf8"));
const summary = analysis.summary;
const font = { ascii: "Times New Roman", hAnsi: "Times New Roman", cs: "Times New Roman", eastAsia: "SimSun" };
const palette = { dark: "293B40", primary: "356A64", accent: "A25B3F", light: "687A7E", fill: "EDF3F1" };
const run = (text, options = {}) => new TextRun({ text: String(text), font, size: 20, ...options });
const para = (children, options = {}) => new Paragraph({ spacing: { after: 100, line: 270 }, ...options, children: Array.isArray(children) ? children : [children] });
const body = (text) => para(run(text), { indent: { firstLine: 400 } });
const afterTable = (text) => para(run(text), { indent: { firstLine: 400 }, spacing: { before: 120, after: 100, line: 270 } });
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
const pattern = (row, method) => row.methods[method].grids.map((grid) => grid.dominant_assignment === "diagonal" ? "D" : grid.dominant_assignment === "swapped" ? "S" : "T").join("／");
const spectrumRows = analysis.realizations.flatMap((row) => row.cells.map((cell) => [String(row.seed), String(row.strength), String(cell.n), fmt(cell.pairs[0].center), fmt(cell.pairs[1].center), fmt(cell.center_separation)]));
const spectrumTable = makeTable(["seed", "r", "N", "最近对中心", "次近对中心", "中心间隔"], spectrumRows, [600, 600, 650, 2600, 2600, 2856], 8);
const assignmentRows = analysis.realizations.map((row) => {
  const linear = row.methods.linear_point.grids.at(-1);
  const average = row.methods.cell_average.grids.at(-1);
  return [String(row.seed), String(row.strength), pattern(row, "linear_point"), pattern(row, "cell_average"), fmt(linear.diagonal_score), fmt(linear.swapped_score), fmt(average.diagonal_score), fmt(average.swapped_score)];
});
const assignmentTable = makeTable(["seed", "r", "LP三格", "CA三格", "LP同谱秩", "LP交换", "CA同谱秩", "CA交换"], assignmentRows, [450, 450, 900, 900, 1600, 1600, 2000, 2006], 7);
const strengthRows = analysis.strength_pair_comparisons.map((row) => [
  String(row.seed), fmt(row.n400_center_separation_delta), fmt(row.n600_center_separation_delta),
  String(row.assignment_transitions.linear_point.filter((item) => item.from !== item.to).length),
  String(row.assignment_transitions.cell_average.filter((item) => item.from !== item.to).length),
]);
const strengthTable = makeTable(["seed", "N=400中心间隔差", "N=600中心间隔差", "LP方向改变数", "CA方向改变数"], strengthRows, [700, 2800, 2800, 1800, 1806], 8);
const comparisonTable = makeTable(["证据来源", "线性点值", "单元平均", "计数与解释"], [
  ["旧交换候选（不同实现）", analysis.anchor_case_observation.old_assignments.linear_point, analysis.anchor_case_observation.old_assignments.cell_average, "只登记来源，不相减"],
  ["既有共同剖面锚点", analysis.anchor_case_observation.matched_control_assignments.linear_point, analysis.anchor_case_observation.matched_control_assignments.cell_average, "seed=6，不进入本批"],
  ["本批M=4800结果", `${summary.assignment_counts.linear_point.diagonal ?? 0}次同谱秩`, `${summary.assignment_counts.cell_average.diagonal ?? 0}次同谱秩`, "8个实现；非统计检验"],
], [2800, 1800, 1800, 3506], 8);
const titles = ["一、预登记协议与谱结构", "二、全网格分配与跨表示控制", "三、图证据与数值自洽", "四、强度配对与实现依赖边界"];
const children = [
  para(run("Floquet-BdG 共同无序剖面第一批尺寸隔离", { bold: true, size: 32, color: palette.dark }), { heading: HeadingLevel.TITLE, alignment: AlignmentType.CENTER, spacing: { before: 560, after: 220 } }),
  para(run("预登记种子与配对强度的完整保留", { bold: true, size: 25, color: palette.primary }), { alignment: AlignmentType.CENTER, spacing: { after: 230 } }),
  para(run("seed=0–3，r=0.05／0.1 · 8个实现 · 16个尺寸控制单元", { size: 20, color: palette.light }), { alignment: AlignmentType.CENTER, spacing: { after: 260 } }),
  para(run("2026-11-11　不新增类别，不补算体 winding，未计算 N=640", { size: 19, color: palette.accent }), { alignment: AlignmentType.CENTER, spacing: { after: 300 } }),
  heading("目录"),
  para(run("以下页码为可见缓存；在 Word/WPS 中更新域可刷新。", { size: 17, italics: true, color: palette.light })),
  toc(titles.map((title, index) => ({ title, level: 1, page: index + 2 }))),
  pageBreak(),

  heading(titles[0]),
  citedBody("每个 seed 只生成一个 M=4800 主剖面，两个强度复用它；N=400 和 N=600 均由同一主剖面的嵌套块平均得到。所有预登记结果保留，不筛选有利方向。", 1),
  equation([sub("β", "N,j"), new MathRun(" = "), new MathFraction({ numerator: [new MathRun("1")], denominator: [new MathRun("K")] }), sub("Σ", "k∈B_N,j"), sup("β", "*")]),
  para(run("K=4800/N；求和遍历第 j 个粗格点覆盖的主格点，星号表示主剖面。两个强度配对不是两个独立无序样本。", { size: 18, color: palette.light })),
  equation([sub("O", "ij"), new MathRun(" = "), new MathFraction({ numerator: [subSup("s", "1", "2"), new MathRun(" + "), subSup("s", "2", "2")], denominator: [new MathRun("2")] })]),
  spectrumTable,
  pageBreak(),

  heading(titles[1]),
  citedBody("D 表示同谱秩主导，S 表示交换主导；三格依次为 M=1200、2400、4800。LP 为线性点值，CA 为单元平均。得分均取 M=4800，不归一化。", 2),
  assignmentTable,
  afterTable(`两种表示各有24个网格结果。线性点值：同谱秩 ${summary.assignment_counts.linear_point.diagonal ?? 0}、交换 ${summary.assignment_counts.linear_point.swapped ?? 0}；单元平均：同谱秩 ${summary.assignment_counts.cell_average.diagonal ?? 0}、交换 ${summary.assignment_counts.cell_average.swapped ?? 0}。这些是描述性计数，不是统计显著性检验。`),
  body(`8个实现中，两种表示均在三个网格同谱秩主导的实现数为 ${summary.same_rank_all_grids_both_methods_count}；两种表示逐网格方向一致的实现数为 ${summary.method_agreement_all_grids_count}。`),
  pageBreak(),

  heading(titles[2]),
  citedBody(`独立重建16个谱后，主剖面和块平均最大误差为 ${independent.max_master_profile_absolute_error} 与 ${independent.max_coarsening_absolute_error}；前六谱距离及两对中心的最大误差分别不超过 ${independent.max_spectrum_absolute_error} 与 ${independent.max_pair_center_absolute_error}，验收容差为1e-12。`, 3),
  para(new ImageRun({ type: "png", data: fs.readFileSync(path.join(root, "matched-beta-batch-a.png")), transformation: { width: 500, height: Math.round(500 * 1383 / 2167) } }), { alignment: AlignmentType.CENTER, keepNext: true }),
  para(run("图 1　分配得分、全网格方向、中心间隔及秩间控制。右下图显示下限1e-25，JSON保留原值。", { size: 16, italics: true }), { alignment: AlignmentType.CENTER }),
  body(`跨表示自一致性范围为 ${fmt(summary.min_representation_fidelity)}–${fmt(summary.max_representation_fidelity)}；原生秩间重叠最大 ${fmt(summary.max_native_off_diagonal)}，单元平均最大 ${fmt(summary.max_cell_average_off_diagonal)}。`),
  body(`线性点值秩间重叠最大 ${fmt(summary.max_linear_point_off_diagonal)}，继续保留嵌入诱导串扰的可能性，不把它误写成原始谱交换。`),
  pageBreak(),

  heading(titles[3]),
  equation([sub("Δc", "N"), new MathRun(" = "), sub("c", "N"), new MathRun("(0.1) − "), sub("c", "N"), new MathRun("(0.05)")]),
  strengthTable,
  afterTable("强度配对均复用完全相同的主剖面。表中中心间隔差全部为正值，但分配方向没有改变；该观察只属于这四个配对实现，不晋升为普遍强度律。"),
  comparisonTable,
  afterTable("旧交换候选与共同剖面控制属于不同无序实现。既有 seed=6 锚点不进入本批计数，本批结果也不能与旧候选直接相减并命名为尺寸效应或谱交叉。"),
  citedBody("本批扩展的是实现依赖范围的描述性证据，不证明尺寸不变、真实态交换、避免交叉、次近对拓扑性、统计显著性或热力学极限。", 4),
  body("复现：python research/floquet-bdg-tbc/analyze_matched_beta_batch_a.py；独立复核：python research/floquet-bdg-tbc/verify_matched_beta_batch_a.py。"),
  para(run("证据边界：4个预登记种子、2个配对强度、2个尺寸；所有结果保留，但不作全域外推。", { size: 18, color: palette.accent })),
];

const document = new Document({
  creator: "TOE-SYLVA",
  title: "Floquet-BdG 共同无序剖面第一批尺寸隔离",
  description: "四个预登记种子与两个配对强度下的共同嵌套无序尺寸控制。",
  features: { updateFields: true },
  styles: { paragraphStyles: [1, 2].map((level) => ({ id: `TOC${level}`, name: `TOC ${level}`, basedOn: "Normal", next: "Normal", quickFormat: true, run: { font, size: 19, color: palette.dark }, paragraph: { spacing: { after: 70, line: 240 }, indent: { left: (level - 1) * 360 } } })) },
  footnotes: {
    1: { children: [footnote("matched_beta_batch_a_protocol.json. Four preregistered seeds and two strengths share nested masters within each seed; all outcomes are retained.")] },
    2: { children: [footnote("matched_beta_batch_a_analysis.json. The complete matrices and all method-grid assignments are descriptive observations only.")] },
    3: { children: [footnote("matched_beta_batch_a_independent.json. Sixteen spectra are independently rebuilt; numerical comparisons use a 1e-12 tolerance.")] },
    4: { children: [footnote("matched_beta_control_analysis.json and swap_candidate_spectrum_analysis.json. The anchor is outside batch A; the old candidate is a different realization.")] },
  },
  sections: [{
    properties: { page: { margin: { top: 900, bottom: 900, left: 1000, right: 1000 } } },
    headers: { default: new Header({ children: [para(run("TOE-SYLVA · Floquet-BdG · 共同无序剖面第一批", { size: 17, color: palette.primary }), { alignment: AlignmentType.CENTER })] }) },
    footers: { default: new Footer({ children: [para(new TextRun({ children: [PageNumber.CURRENT], font, size: 17 }), { alignment: AlignmentType.CENTER })] }) },
    children,
  }],
});
fs.writeFileSync(outputPath, await Packer.toBuffer(document));
