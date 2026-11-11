import fs from "node:fs";
import path from "node:path";
import {
  AlignmentType, Document, Footer, FootnoteReferenceRun, Header, HeadingLevel,
  ImageRun, ImportedXmlComponent, Math as MathEquation, MathFraction, MathRun,
  MathSubScript, MathSuperScript, Packer, PageBreak, PageNumber, Paragraph,
  ShadingType, Table, TableCell, TableRow, TextRun, WidthType,
} from "docx";

const outputPath = process.argv[2];
if (!outputPath) throw new Error("Usage: node build_seed01_matrix_midpoint_report.js /absolute/path/report.docx");
const root = path.dirname(outputPath);
const analysis = JSON.parse(fs.readFileSync(path.join(root, "seed01_matrix_midpoint_analysis.json"), "utf8"));
const independent = JSON.parse(fs.readFileSync(path.join(root, "seed01_matrix_midpoint_independent.json"), "utf8"));
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
const summaryTable = makeTable(["seed", "新单元", "跳变改变数（8项）", "主导改变数（4组）", "新中点极值数", "分配改变数"], analysis.summary_by_seed.map((row) => [String(row.seed), String(row.new_control_cells), String(row.jump_change_count), String(row.driver_comparison_change_count), String(row.new_extrema_midpoint_count), String(row.method_grid_assignment_change_count)]), [650, 900, 2200, 2200, 2000, 1956], 8);
const newCells = analysis.cells.filter((cell) => analysis.protocol_new_midpoint_strengths.includes(cell.strength));
const spectrumTable = makeTable(["seed", "r", "N", "最近对中心", "次近对中心", "中心间隔"], newCells.map((cell) => [String(cell.seed), String(cell.strength), String(cell.n), fmt(cell.pairs[0].center), fmt(cell.pairs[1].center), fmt(cell.center_separation)]), [500, 800, 550, 2400, 2400, 3256], 7);
const jumpTable = makeTable(["seed", "方法", "项", "原最大跳变及链接", "细化最大跳变及链接", "改变"], analysis.jump_comparisons.map((row) => [String(row.seed), row.method, row.entry, `${fmt(row.original_max_adjacent_absolute_jump)}（${row.original_jump_from}→${row.original_jump_to}）`, `${fmt(row.refined_max_adjacent_absolute_jump)}（${row.refined_jump_from}→${row.refined_jump_to}）`, String(row.jump_changed)]), [500, 1200, 600, 2600, 2600, 2406], 7);
const agreementTable = makeTable(["方法", "项", "最小值强度（0／1／6）", "最大值强度（0／1／6）", "最大跳变链接（0／1／6）"], analysis.cross_seed_extremum_agreement.map((row) => [row.method, row.entry, JSON.stringify(row.min_strength_by_seed), JSON.stringify(row.max_strength_by_seed), JSON.stringify(row.max_jump_link_by_seed)]), [1500, 650, 2400, 2400, 2956], 7);
const driverTable = makeTable(["seed", "方法", "得分组", "原计数（8链接）", "细化计数（12链接）"], analysis.driver_comparisons.map((row) => [String(row.seed), row.method, row.score_group, Object.entries(row.original_dominant_entry_counts).map(([key, value]) => `${key}:${value}`).join("；"), Object.entries(row.refined_dominant_entry_counts).map(([key, value]) => `${key}:${value}`).join("；")]), [500, 1500, 1100, 3200, 3606], 7);
const linkTable = makeTable(["seed", "N", "同谱秩最小值及链接", "交换最大值及链接", "最大中心间隔变化"], analysis.link_summary.map((row) => [String(row.seed), String(row.n), `${fmt(row.min_diagonal_score)}（${row.min_diagonal_from}→${row.min_diagonal_to}）`, `${fmt(row.max_swapped_score)}（${row.max_swapped_from}→${row.max_swapped_to}）`, fmt(row.max_absolute_center_separation_delta)]), [500, 550, 2900, 2900, 3056], 7);
const titles = ["一、跨种子协议与端点绑定", "二、步长与实现依赖对照", "三、图证据与独立复核", "四、主导项、原生链接与边界"];
const children = [
  para(run("Floquet-BdG 跨种子跳变窗口中点对照", { bold: true, size: 32, color: palette.dark }), { heading: HeadingLevel.TITLE, alignment: AlignmentType.CENTER, spacing: { before: 560, after: 220 } }),
  para(run("步长依赖与实现依赖不能混同", { bold: true, size: 25, color: palette.primary }), { alignment: AlignmentType.CENTER, spacing: { after: 230 } }),
  para(run("seed=0／1 · 52个新尺寸单元 · 同一13点协议", { size: 20, color: palette.light }), { alignment: AlignmentType.CENTER, spacing: { after: 260 } }),
  para(run(`${analysis.report_date}　不新增类别，不补算体 winding，未计算 N=640`, { size: 19, color: palette.accent }), { alignment: AlignmentType.CENTER, spacing: { after: 300 } }),
  heading("目录"),
  para(run("以下页码为可见缓存；在 Word/WPS 中更新域可刷新。", { size: 17, italics: true, color: palette.light })),
  toc(titles.map((title, index) => ({ title, level: 1, page: index + 2 }))),
  pageBreak(),

  heading(titles[0]),
  citedBody("seed=0、1 分别比较原9点／8链接与细化13点／12链接，再与既有 seed=6 对照。每个种子使用自己的主无序剖面，不根据结果增删种子或强度。", 1),
  summaryTable,
  equation([sub("O", "ij"), new MathRun(" = "), new MathFraction({ numerator: [subSup("s", "1", "2"), new MathRun(" + "), subSup("s", "2", "2")], denominator: [new MathRun("2")] })]),
  para(run(`端点矩阵、主奇异值与前六谱距离的最大绑定误差分别为 ${fmt(analysis.endpoint_binding.max_matrix_absolute_error)}、${fmt(analysis.endpoint_binding.max_singular_absolute_error)} 和 ${fmt(analysis.endpoint_binding.max_spectrum_absolute_error)}。`, { size: 18, color: palette.light })),
  spectrumTable,
  pageBreak(),

  heading(titles[1]),
  citedBody("每个种子分别计算最大跳变，再比较极值与最大跳变链接是否跨种子一致。主导项只表示最大绝对数值贡献，不是因果机制。", 2),
  jumpTable,
  heading("跨种子极值与跳变位置", 2),
  agreementTable,
  afterTable(`三个种子间，最小值强度完全一致仅 ${summary.same_min_strength_across_all_count} 项，最大值强度完全一致 ${summary.same_max_strength_across_all_count} 项，最大跳变链接完全一致 ${summary.same_max_jump_link_across_all_count} 项。实现依赖不能被步长细化消除。`),
  pageBreak(),

  heading(titles[2]),
  citedBody(`独立重建52个路径单元、156组矩阵、576条矩阵项差分及48条原生链接。谱、矩阵、差分与原生链接最大误差分别为 ${independent.max_spectrum_absolute_error}、${independent.max_matrix_absolute_error}、${independent.max_entry_delta_absolute_error} 和 ${independent.max_native_link_absolute_error}；主导项不一致数为 ${independent.driver_mismatch_count}。`, 3),
  para(new ImageRun({ type: "png", data: fs.readFileSync(path.join(root, "seed01-matrix-midpoint.png")), transformation: { width: 500, height: Math.round(500 * 1415 / 2174) } }), { alignment: AlignmentType.CENTER, keepNext: true }),
  para(run("图 1　三个无序实现的 O00、O01、O10 路径、步长改变计数及同尺寸原生重叠。数值贡献不作因果命名。", { size: 16, italics: true }), { alignment: AlignmentType.CENTER }),
  body(`跨表示自一致性总范围为 ${fmt(summary.min_representation_fidelity)}–${fmt(summary.max_representation_fidelity)}；线性点值秩间重叠最大 ${fmt(summary.max_linear_point_off_diagonal)}，单元平均最大 ${fmt(summary.max_cell_average_off_diagonal)}，继续单列嵌入串扰。`),
  body("seed=1 的最大跳变链接未变，但主导项计数仍改变；seed=0 与 seed=6 的跳变位置均有变化。任何单一指标的稳定都不能推广为全路径稳定。"),
  pageBreak(),

  heading(titles[3]),
  driverTable,
  linkTable,
  afterTable("不同种子的主导项和原生最小重叠位置并不完全一致。跨种子一致或不一致只描述当前实现，不构成普遍性或统计显著性结论。"),
  citedBody("中点插入和跨种子对照可以区分步长依赖与实现依赖，但不能外推为其他种子、普遍尺寸律、真实态交换、谱交叉、统计显著性或热力学极限结论。旧交换候选属于不同无序实现，不能与路径差分直接相减。", 4),
  body("复现：python research/floquet-bdg-tbc/analyze_seed01_matrix_midpoint.py；独立复核：python research/floquet-bdg-tbc/verify_seed01_matrix_midpoint.py。"),
  para(run("证据边界：seed=0、1 的同一13点协议与 seed=6 对照；不新增类别，不作连续路径或热力学极限推断。", { size: 18, color: palette.accent })),
];

const document = new Document({
  creator: "TOE-SYLVA",
  title: "Floquet-BdG 跨种子跳变窗口中点对照",
  description: "跨种子中点路径、步长稳定性与实现依赖对照。",
  features: { updateFields: true },
  styles: { paragraphStyles: [1, 2].map((level) => ({ id: `TOC${level}`, name: `TOC ${level}`, basedOn: "Normal", next: "Normal", quickFormat: true, run: { font, size: 19, color: palette.dark }, paragraph: { spacing: { after: 70, line: 240 }, indent: { left: (level - 1) * 360 } } })) },
  footnotes: {
    1: { children: [footnote("seed01_matrix_midpoint_protocol.json and seed6_matrix_midpoint_analysis.json. Two new 13-point paths with a stored seed-6 reference; no seed or strength is selected after inspecting outcomes.")] },
    2: { children: [footnote("seed01_matrix_midpoint_analysis.json. Extrema, jumps, drivers and cross-seed agreements are numerical descriptions, not causal mechanisms.")] },
    3: { children: [footnote("seed01_matrix_midpoint_independent.json. Fifty-two cells, 156 matrices, 48 native links and all entry deltas are independently rebuilt.")] },
    4: { children: [footnote("matched_beta_batch_a_analysis.json, matched_beta_batch_c_analysis.json and swap_candidate_spectrum_analysis.json. Endpoints bind to prior evidence; the old candidate is a different realization.")] },
  },
  sections: [{
    properties: { page: { margin: { top: 900, bottom: 900, left: 1000, right: 1000 } } },
    headers: { default: new Header({ children: [para(run("TOE-SYLVA · Floquet-BdG · 跨种子中点对照", { size: 17, color: palette.primary }), { alignment: AlignmentType.CENTER })] }) },
    footers: { default: new Footer({ children: [para(new TextRun({ children: [PageNumber.CURRENT], font, size: 17 }), { alignment: AlignmentType.CENTER })] }) },
    children,
  }],
});
fs.writeFileSync(outputPath, await Packer.toBuffer(document));
