import fs from "node:fs";
import path from "node:path";
import {
  AlignmentType, Document, Footer, FootnoteReferenceRun, Header, HeadingLevel,
  ImageRun, ImportedXmlComponent, Math as MathEquation, MathFraction, MathRun,
  MathSubScript, MathSuperScript, Packer, PageBreak, PageNumber, Paragraph,
  ShadingType, Table, TableCell, TableRow, TextRun, WidthType,
} from "docx";

const outputPath = process.argv[2];
if (!outputPath) throw new Error("Usage: node build_matched_beta_batch_c_report.js /absolute/path/report.docx");
const root = path.dirname(outputPath);
const analysis = JSON.parse(fs.readFileSync(path.join(root, "matched_beta_batch_c_analysis.json"), "utf8"));
const independent = JSON.parse(fs.readFileSync(path.join(root, "matched_beta_batch_c_independent.json"), "utf8"));
const summary = analysis.summary;
const pairSummary = analysis.high_strength_summary;
const combined = analysis.combined_with_batches_a_b;
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
const countText = (counts) => `同谱秩 ${counts.diagonal ?? 0}、交换 ${counts.swapped ?? 0}、平局 ${counts.tie_exact ?? 0}`;
const countShort = (counts) => `${counts.diagonal ?? 0}／${counts.swapped ?? 0}`;
const spectrumRows = analysis.realizations.flatMap((row) => row.cells.map((cell) => [String(row.seed), String(row.strength), String(cell.n), fmt(cell.pairs[0].center), fmt(cell.pairs[1].center), fmt(cell.center_separation)]));
const spectrumTable = makeTable(["seed", "r", "N", "最近对中心", "次近对中心", "中心间隔"], spectrumRows, [600, 600, 650, 2600, 2600, 2856], 8);
const assignmentRows = analysis.realizations.map((row) => {
  const linear = row.methods.linear_point.grids.at(-1);
  const average = row.methods.cell_average.grids.at(-1);
  return [String(row.seed), pattern(row, "linear_point"), pattern(row, "cell_average"), fmt(linear.diagonal_score), fmt(linear.swapped_score), fmt(average.diagonal_score), fmt(average.swapped_score)];
});
const assignmentTable = makeTable(["seed", "LP三格", "CA三格", "LP同谱秩", "LP交换", "CA同谱秩", "CA交换"], assignmentRows, [550, 1050, 1050, 1850, 1700, 1850, 1856], 7);
const strengthRows = analysis.strength_pair_comparisons.map((row) => [
  String(row.seed), fmt(row.n400_center_separation_delta), fmt(row.n600_center_separation_delta),
  String(row.assignment_transitions.linear_point.filter((item) => item.from !== item.to).length),
  String(row.assignment_transitions.cell_average.filter((item) => item.from !== item.to).length),
]);
const strengthTable = makeTable(["seed", "N=400中心间隔差", "N=600中心间隔差", "LP方向改变数", "CA方向改变数"], strengthRows, [700, 2800, 2800, 1800, 1806], 8);
const strengthCountTable = makeTable(["强度", "LP同谱秩／交换", "CA同谱秩／交换", "实现数"], [0.05, 0.1, 0.2].map((strength) => {
  const row = combined.by_strength[String(strength)];
  return [`r=${strength}`, countShort(row.assignment_counts.linear_point), countShort(row.assignment_counts.cell_average), String(row.realization_count)];
}), [1500, 3200, 3200, 2006], 8);
const titles = ["一、预登记高强度协议与谱结构", "二、第三批全网格分配", "三、图证据与独立谱复核", "四、高强度配对与三批联合边界"];
const children = [
  para(run("Floquet-BdG 共同无序剖面第三批高强度配对", { bold: true, size: 32, color: palette.dark }), { heading: HeadingLevel.TITLE, alignment: AlignmentType.CENTER, spacing: { before: 560, after: 220 } }),
  para(run("方向不变不等于数值结构不变", { bold: true, size: 25, color: palette.primary }), { alignment: AlignmentType.CENTER, spacing: { after: 230 } }),
  para(run("8个主剖面 · r=0.1→0.2 · 16个新增尺寸单元", { size: 20, color: palette.light }), { alignment: AlignmentType.CENTER, spacing: { after: 260 } }),
  para(run(`${analysis.report_date}　不新增类别，不补算体 winding，未计算 N=640`, { size: 19, color: palette.accent }), { alignment: AlignmentType.CENTER, spacing: { after: 300 } }),
  heading("目录"),
  para(run("以下页码为可见缓存；在 Word/WPS 中更新域可刷新。", { size: 17, italics: true, color: palette.light })),
  toc(titles.map((title, index) => ({ title, level: 1, page: index + 2 }))),
  pageBreak(),

  heading(titles[0]),
  citedBody("既有8个主剖面统一新增 r=0.2，与此前 r=0.1 结果配对。此前数据只读不重算；所有预登记结果保留，不根据本批结果选择下一强度。", 1),
  equation([sub("β", "N,j"), new MathRun(" = "), new MathFraction({ numerator: [new MathRun("1")], denominator: [new MathRun("K")] }), sub("Σ", "k∈B_N,j"), sup("β", "*")]),
  para(run("K=4800/N；求和遍历第 j 个粗格点覆盖的主格点，星号表示主剖面。两个强度使用完全相同的主剖面，不是独立无序样本。", { size: 18, color: palette.light })),
  equation([sub("O", "ij"), new MathRun(" = "), new MathFraction({ numerator: [subSup("s", "1", "2"), new MathRun(" + "), subSup("s", "2", "2")], denominator: [new MathRun("2")] })]),
  spectrumTable,
  pageBreak(),

  heading(titles[1]),
  citedBody("D 表示同谱秩主导，S 表示交换主导；三格依次为 M=1200、2400、4800。LP 为线性点值，CA 为单元平均。得分均取 M=4800，不归一化。", 2),
  assignmentTable,
  afterTable(`第三批两种表示各有24个网格结果。线性点值：${countText(summary.assignment_counts.linear_point)}；单元平均：${countText(summary.assignment_counts.cell_average)}。这些是描述性计数，不是统计显著性检验。`),
  body(`r=0.1→0.2 时，线性点值同谱秩得分比范围为 ${fmt(pairSummary.assignment_transition_counts.linear_point.diagonal_score_ratio_range[0])}–${fmt(pairSummary.assignment_transition_counts.linear_point.diagonal_score_ratio_range[1])}，交换得分比范围为 ${fmt(pairSummary.assignment_transition_counts.linear_point.swapped_score_ratio_range[0])}–${fmt(pairSummary.assignment_transition_counts.linear_point.swapped_score_ratio_range[1])}。方向不变并不排除幅度变化。`),
  pageBreak(),

  heading(titles[2]),
  citedBody(`独立重建16个新谱后，主剖面与块平均最大误差为 ${independent.max_master_profile_absolute_error} 和 ${independent.max_coarsening_absolute_error}；前六谱距离及两对中心的最大误差分别不超过 ${independent.max_spectrum_absolute_error} 和 ${independent.max_pair_center_absolute_error}，验收容差为1e-12。`, 3),
  para(new ImageRun({ type: "png", data: fs.readFileSync(path.join(root, "matched-beta-batch-c.png")), transformation: { width: 500, height: Math.round(500 * 1352 / 2157) } }), { alignment: AlignmentType.CENTER, keepNext: true }),
  para(run("图 1　r=0.2分配得分与方向、相对r=0.1的中心间隔变化，以及三种强度的联合分配计数。", { size: 16, italics: true }), { alignment: AlignmentType.CENTER }),
  body(`三批联合跨表示自一致性范围为 ${fmt(combined.min_representation_fidelity)}–${fmt(combined.max_representation_fidelity)}；第三批原生秩间重叠最大 ${fmt(summary.max_native_off_diagonal)}，单元平均最大 ${fmt(summary.max_cell_average_off_diagonal)}。`),
  body(`第三批线性点值秩间重叠最大 ${fmt(summary.max_linear_point_off_diagonal)}，继续保留嵌入诱导串扰的可能性，不把它误写成原始谱交换。`),
  pageBreak(),

  heading(titles[3]),
  equation([sub("Δc", "N"), new MathRun(" = "), sub("c", "N"), new MathRun("(0.2) − "), sub("c", "N"), new MathRun("(0.1)")]),
  strengthTable,
  afterTable(`N=400中心间隔变化范围为 ${fmt(pairSummary.n400_center_separation_delta_range[0])} 至 ${fmt(pairSummary.n400_center_separation_delta_range[1])}；N=600为 ${fmt(pairSummary.n600_center_separation_delta_range[0])} 至 ${fmt(pairSummary.n600_center_separation_delta_range[1])}。该配对观察不晋升为普遍强度律。`),
  strengthCountTable,
  afterTable(`A+B+C共有 ${combined.realization_count} 个唯一实现和 ${combined.control_cells} 个尺寸单元。联合线性点值：${countText(combined.assignment_counts.linear_point)}；单元平均：${countText(combined.assignment_counts.cell_average)}。`),
  citedBody("联合中心间隔尺寸差仍有正有负。旧交换候选与共同剖面控制属于不同无序实现，不能与联合结果直接相减并命名为尺寸效应或谱交叉。", 4),
  body("联合结果不证明尺寸不变、普遍强度律、真实态交换、避免交叉、次近对拓扑性、统计显著性或热力学极限。复现：python research/floquet-bdg-tbc/analyze_matched_beta_batch_c.py。"),
  para(run("证据边界：8个预登记主剖面在 r=0.2 的新配对，以及三批24个唯一实现的描述性覆盖。", { size: 18, color: palette.accent })),
];

const document = new Document({
  creator: "TOE-SYLVA",
  title: "Floquet-BdG 共同无序剖面第三批高强度配对",
  description: "八个主剖面在r=0.2的新配对及三批联合描述性审计。",
  features: { updateFields: true },
  styles: { paragraphStyles: [1, 2].map((level) => ({ id: `TOC${level}`, name: `TOC ${level}`, basedOn: "Normal", next: "Normal", quickFormat: true, run: { font, size: 19, color: palette.dark }, paragraph: { spacing: { after: 70, line: 240 }, indent: { left: (level - 1) * 360 } } })) },
  footnotes: {
    1: { children: [footnote("matched_beta_batch_c_protocol.json. Eight preregistered masters are evaluated at r=0.2 and paired with prior r=0.1 evidence without modifying prior results.")] },
    2: { children: [footnote("matched_beta_batch_c_analysis.json. All method-grid outcomes, score ratios and center-separation changes are retained without overlap normalization.")] },
    3: { children: [footnote("matched_beta_batch_c_independent.json. Sixteen new spectra are independently rebuilt; numerical comparisons use a 1e-12 tolerance.")] },
    4: { children: [footnote("matched_beta_batch_a_analysis.json, matched_beta_batch_b_analysis.json and swap_candidate_spectrum_analysis.json. Three-batch keys are unique; the old swap candidate is a different realization.")] },
  },
  sections: [{
    properties: { page: { margin: { top: 900, bottom: 900, left: 1000, right: 1000 } } },
    headers: { default: new Header({ children: [para(run("TOE-SYLVA · Floquet-BdG · 第三批高强度配对", { size: 17, color: palette.primary }), { alignment: AlignmentType.CENTER })] }) },
    footers: { default: new Footer({ children: [para(new TextRun({ children: [PageNumber.CURRENT], font, size: 17 }), { alignment: AlignmentType.CENTER })] }) },
    children,
  }],
});
fs.writeFileSync(outputPath, await Packer.toBuffer(document));
