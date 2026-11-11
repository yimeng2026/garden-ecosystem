import fs from "node:fs";
import path from "node:path";
import {
  AlignmentType, Document, Footer, FootnoteReferenceRun, Header, HeadingLevel,
  ImageRun, ImportedXmlComponent, Math as MathEquation, MathFraction, MathRun,
  MathSubScript, MathSuperScript, Packer, PageBreak, PageNumber, Paragraph,
  ShadingType, Table, TableCell, TableRow, TextRun, WidthType,
} from "docx";

const outputPath = process.argv[2];
if (!outputPath) throw new Error("Usage: node build_seed6_matrix_midpoint_report.js /absolute/path/report.docx");
const root = path.dirname(outputPath);
const analysis = JSON.parse(fs.readFileSync(path.join(root, "seed6_matrix_midpoint_analysis.json"), "utf8"));
const independent = JSON.parse(fs.readFileSync(path.join(root, "seed6_matrix_midpoint_independent.json"), "utf8"));
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
const newCells = analysis.cells.filter((cell) => cell.new_for_path);
const spectrumTable = makeTable(["r", "N", "最近对中心", "次近对中心", "中心间隔"], newCells.map((cell) => [String(cell.strength), String(cell.n), fmt(cell.pairs[0].center), fmt(cell.pairs[1].center), fmt(cell.center_separation)]), [900, 700, 2700, 2700, 2906], 8);
const jumpTable = makeTable(["方法", "项", "原最大跳变及链接", "细化最大跳变及链接", "改变"], analysis.jump_comparisons.map((row) => [row.method, row.entry, `${fmt(row.old_max_adjacent_absolute_jump)}（${row.old_jump_from}→${row.old_jump_to}）`, `${fmt(row.refined_max_adjacent_absolute_jump)}（${row.refined_jump_from}→${row.refined_jump_to}）`, String(row.jump_changed)]), [1600, 700, 2900, 2900, 1806], 7);
const driverTable = makeTable(["方法", "得分组", "原计数（8链接）", "细化计数（12链接）", "改变"], analysis.driver_comparisons.map((row) => [row.method, row.score_group, Object.entries(row.old_dominant_entry_counts).map(([key, value]) => `${key}:${value}`).join("；"), Object.entries(row.refined_dominant_entry_counts).map(([key, value]) => `${key}:${value}`).join("；"), String(row.driver_counts_changed)]), [1600, 1100, 2700, 2700, 1806], 7);
const linkTable = makeTable(["N", "链接数", "同谱秩最小值及链接", "交换最大值及链接", "最大中心间隔变化"], analysis.link_summary.map((row) => [String(row.n), String(row.link_count), `${fmt(row.min_diagonal_score)}（${row.min_diagonal_from}→${row.min_diagonal_to}）`, `${fmt(row.max_swapped_score)}（${row.max_swapped_from}→${row.max_swapped_to}）`, fmt(row.max_absolute_center_separation_delta)]), [600, 800, 2700, 2700, 3106], 8);
const shiftedExtrema = analysis.entry_extrema.filter((row) => analysis.protocol_new_midpoint_strengths.includes(row.min_strength) || analysis.protocol_new_midpoint_strengths.includes(row.max_strength));
const titles = ["一、中点协议与原路径绑定", "二、跳变与主导项的步长对照", "三、图证据与独立复核", "四、原生链接与解释边界"];
const children = [
  para(run("Floquet-BdG 固定种子跳变窗口中点复核", { bold: true, size: 32, color: palette.dark }), { heading: HeadingLevel.TITLE, alignment: AlignmentType.CENTER, spacing: { before: 560, after: 220 } }),
  para(run("跳变减小不等于路径已经收敛", { bold: true, size: 25, color: palette.primary }), { alignment: AlignmentType.CENTER, spacing: { after: 230 } }),
  para(run("4个预登记中点 · 8个新尺寸单元 · 13点路径", { size: 20, color: palette.light }), { alignment: AlignmentType.CENTER, spacing: { after: 260 } }),
  para(run(`${analysis.report_date}　不新增类别，不补算体 winding，未计算 N=640`, { size: 19, color: palette.accent }), { alignment: AlignmentType.CENTER, spacing: { after: 300 } }),
  heading("目录"),
  para(run("以下页码为可见缓存；在 Word/WPS 中更新域可刷新。", { size: 17, italics: true, color: palette.light })),
  toc(titles.map((title, index) => ({ title, level: 1, page: index + 2 }))),
  pageBreak(),

  heading(titles[0]),
  citedBody("在 r=0.125–0.15 与 r=0.175–0.2 两个既定窗口各插入2个中点，不根据结果增删。原9点与新增4点组成13点路径、12条相邻链接。", 1),
  equation([sub("O", "ij"), new MathRun(" = "), new MathFraction({ numerator: [subSup("s", "1", "2"), new MathRun(" + "), subSup("s", "2", "2")], denominator: [new MathRun("2")] })]),
  equation([new MathRun("Δ"), sub("O", "ij"), new MathRun(" = "), sub("O", "ij"), new MathRun("(r₂) − "), sub("O", "ij"), new MathRun("(r₁)")]),
  para(run(`原18个单元的谱误差为 ${fmt(analysis.original_path_binding.max_spectrum_absolute_error)}；原54组矩阵的重叠误差为 ${fmt(analysis.original_path_binding.max_matrix_absolute_error)}，主奇异值误差为 ${fmt(analysis.original_path_binding.max_singular_absolute_error)}。复用单元不计入新增实现。`, { size: 18, color: palette.light })),
  spectrumTable,
  pageBreak(),

  heading(titles[1]),
  citedBody(`8个矩阵项中，${summary.jump_change_count} 个最大跳变位置或数值发生变化；4组主导项计数中有 ${summary.driver_comparison_change_count} 组改变。主导项仅表示最大绝对数值贡献，不是因果机制。`, 2),
  jumpTable,
  heading("主导项计数对照", 2),
  driverTable,
  afterTable("新增中点可以减小部分最大跳变，但也改变主导项与极值位置。更平滑的外观不能直接当成收敛证明。"),
  pageBreak(),

  heading(titles[2]),
  citedBody(`独立重建26个路径单元、78组矩阵、288条矩阵项差分及24条原生链接。谱、矩阵、差分与原生链接最大误差分别为 ${independent.max_spectrum_absolute_error}、${independent.max_matrix_absolute_error}、${independent.max_entry_delta_absolute_error} 和 ${independent.max_native_link_absolute_error}；主导项不一致数为 ${independent.driver_mismatch_count}。`, 3),
  para(new ImageRun({ type: "png", data: fs.readFileSync(path.join(root, "seed6-matrix-midpoint.png")), transformation: { width: 500, height: Math.round(500 * 1439 / 2191) } }), { alignment: AlignmentType.CENTER, keepNext: true }),
  para(run("图 1　13点路径、局部极值、原8链接与细化12链接的最大跳变，以及同尺寸原生重叠。竖虚线为新增中点。", { size: 16, italics: true }), { alignment: AlignmentType.CENTER }),
  body(`跨表示自一致性为 ${fmt(summary.min_representation_fidelity)}–${fmt(summary.max_representation_fidelity)}；线性点值秩间重叠最大 ${fmt(summary.max_linear_point_off_diagonal)}，单元平均最大 ${fmt(summary.max_cell_average_off_diagonal)}，继续单列嵌入串扰。`),
  body(`新增中点参与极值位置的矩阵项共有 ${summary.new_extrema_midpoint_count} 个：${shiftedExtrema.map((row) => `${row.method} ${row.entry}（最小值 ${fmt(row.min)} @ ${row.min_strength}）`).join("；")}。`),
  pageBreak(),

  heading(titles[3]),
  linkTable,
  afterTable("两种尺寸的原生最小重叠仍位于 r=0.1→0.1125，未因中点插入而移动；全部原生链接仍为同谱秩占优，但这仍不是连续路径证明。"),
  citedBody("中点结果只适用于 seed=6 和当前网格。局部极值、跳变减小或主导项变化都不能直接命名为谱交叉、真实态交换、统计显著性或因果机制。旧交换候选属于不同无序实现，不能与路径差分直接相减。", 4),
  body("后续若继续细化，应针对同一跳变窗口保持完整预登记点集，并同时检查主导项、极值位置和链接重叠，而不是只挑选曲线更平滑的指标。"),
  body("复现：python research/floquet-bdg-tbc/analyze_seed6_matrix_midpoint.py；独立复核：python research/floquet-bdg-tbc/verify_seed6_matrix_midpoint.py。"),
  para(run("证据边界：4个预登记中点、13点离散路径；不新增类别，不作连续路径或热力学极限推断。", { size: 18, color: palette.accent })),
];

const document = new Document({
  creator: "TOE-SYLVA",
  title: "Floquet-BdG 固定种子跳变窗口中点复核",
  description: "两个跳变窗口的中点细化、步长稳定性与原生链接对照。",
  features: { updateFields: true },
  styles: { paragraphStyles: [1, 2].map((level) => ({ id: `TOC${level}`, name: `TOC ${level}`, basedOn: "Normal", next: "Normal", quickFormat: true, run: { font, size: 19, color: palette.dark }, paragraph: { spacing: { after: 70, line: 240 }, indent: { left: (level - 1) * 360 } } })) },
  footnotes: {
    1: { children: [footnote("seed6_matrix_midpoint_protocol.json and seed6_matrix_path_analysis.json. Four preregistered midpoints; original cells and matrices are bound, not recounted as new realizations.")] },
    2: { children: [footnote("seed6_matrix_midpoint_analysis.json. Jump and driver changes are numerical step-size effects, not causal mechanisms.")] },
    3: { children: [footnote("seed6_matrix_midpoint_independent.json. Twenty-six cells, seventy-eight matrices, twenty-four native links and all entry deltas are independently rebuilt.")] },
    4: { children: [footnote("swap_candidate_spectrum_analysis.json. The old swap candidate is a different disorder realization and cannot be subtracted from this path.")] },
  },
  sections: [{
    properties: { page: { margin: { top: 900, bottom: 900, left: 1000, right: 1000 } } },
    headers: { default: new Header({ children: [para(run("TOE-SYLVA · Floquet-BdG · 跳变窗口中点复核", { size: 17, color: palette.primary }), { alignment: AlignmentType.CENTER })] }) },
    footers: { default: new Footer({ children: [para(new TextRun({ children: [PageNumber.CURRENT], font, size: 17 }), { alignment: AlignmentType.CENTER })] }) },
    children,
  }],
});
fs.writeFileSync(outputPath, await Packer.toBuffer(document));
