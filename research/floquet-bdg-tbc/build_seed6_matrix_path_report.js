import fs from "node:fs";
import path from "node:path";
import {
  AlignmentType, Document, Footer, FootnoteReferenceRun, Header, HeadingLevel,
  ImageRun, ImportedXmlComponent, Math as MathEquation, MathFraction, MathRun,
  MathSubScript, MathSuperScript, Packer, PageBreak, PageNumber, Paragraph,
  ShadingType, Table, TableCell, TableRow, TextRun, WidthType,
} from "docx";

const outputPath = process.argv[2];
if (!outputPath) throw new Error("Usage: node build_seed6_matrix_path_report.js /absolute/path/report.docx");
const root = path.dirname(outputPath);
const analysis = JSON.parse(fs.readFileSync(path.join(root, "seed6_matrix_path_analysis.json"), "utf8"));
const independent = JSON.parse(fs.readFileSync(path.join(root, "seed6_matrix_path_independent.json"), "utf8"));
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
const spectrumRows = analysis.cells.map((cell) => [String(cell.strength), String(cell.n), fmt(cell.pairs[0].center), fmt(cell.pairs[1].center), fmt(cell.center_separation), cell.new_for_path ? "内部新增" : "端点控制"]);
const spectrumTable = makeTable(["r", "N", "最近对中心", "次近对中心", "中心间隔", "角色"], spectrumRows, [850, 650, 2300, 2300, 2200, 1606], 7);
const extremaTable = makeTable(["方法", "项", "最小值及强度", "最大值及强度", "最大相邻跳变", "主通道"], analysis.entry_extrema.map((row) => {
  const counts = row.dominant_singular_channel_counts;
  const channel = `s₁:${counts["0"] ?? 0}／s₂:${counts["1"] ?? 0}`;
  return [row.method, row.entry, `${fmt(row.min)} @ ${row.min_strength}`, `${fmt(row.max)} @ ${row.max_strength}`, `${fmt(row.max_adjacent_absolute_jump)}（${row.max_jump_from}→${row.max_jump_to}）`, channel];
}), [1600, 700, 1900, 1900, 1900, 1906], 7);
const driverTable = makeTable(["方法", "得分组", "主导项计数（8条链接）", "得分比范围"], analysis.driver_summary.map((row) => [row.method, row.score_group, Object.entries(row.dominant_entry_counts).map(([key, value]) => `${key}:${value}`).join("；"), `${fmt(row.score_ratio_range[0])}–${fmt(row.score_ratio_range[1])}`]), [1800, 1300, 4300, 2506], 8);
const linkTable = makeTable(["N", "链接数", "同谱秩最小值及链接", "交换最大值及链接", "最大中心间隔变化"], analysis.link_summary.map((row) => [String(row.n), String(row.link_count), `${fmt(row.min_diagonal_score)}（${row.min_diagonal_from}→${row.min_diagonal_to}）`, `${fmt(row.max_swapped_score)}（${row.max_swapped_from}→${row.max_swapped_to}）`, fmt(row.max_absolute_center_separation_delta)]), [600, 800, 2700, 2700, 3106], 8);
const titles = ["一、离散路径协议与端点绑定", "二、矩阵项响应与主导通道", "三、图证据与独立复核", "四、同尺寸链接与解释边界"];
const children = [
  para(run("Floquet-BdG 固定种子矩阵路径", { bold: true, size: 32, color: palette.dark }), { heading: HeadingLevel.TITLE, alignment: AlignmentType.CENTER, spacing: { before: 560, after: 220 } }),
  para(run("端点分解不能替代逐链接检验", { bold: true, size: 25, color: palette.primary }), { alignment: AlignmentType.CENTER, spacing: { after: 230 } }),
  para(run("seed=6 · 9个强度点 · 8条相邻链接 · 18个路径单元", { size: 20, color: palette.light }), { alignment: AlignmentType.CENTER, spacing: { after: 260 } }),
  para(run(`${analysis.report_date}　不新增类别，不补算体 winding，未计算 N=640`, { size: 19, color: palette.accent }), { alignment: AlignmentType.CENTER, spacing: { after: 300 } }),
  heading("目录"),
  para(run("以下页码为可见缓存；在 Word/WPS 中更新域可刷新。", { size: 17, italics: true, color: palette.light })),
  toc(titles.map((title, index) => ({ title, level: 1, page: index + 2 }))),
  pageBreak(),

  heading(titles[0]),
  citedBody("固定 seed=6，在 r=0.1–0.2 间取9个等距点。14个内部尺寸单元为新增计算，4个端点单元仅用于路径一致性重算，不并入此前批次计数。", 1),
  equation([sub("O", "ij"), new MathRun(" = "), new MathFraction({ numerator: [subSup("s", "1", "2"), new MathRun(" + "), subSup("s", "2", "2")], denominator: [new MathRun("2")] })]),
  equation([new MathRun("Δ"), sub("O", "ij"), new MathRun(" = "), sub("O", "ij"), new MathRun("(r₂) − "), sub("O", "ij"), new MathRun("(r₁)")]),
  para(run("跨尺寸 Oij 不是同尺寸态追踪；相邻强度的同尺寸原生二维子空间重叠才是路径控制。两类证据均不归一化，不筛选有利路径段。", { size: 18, color: palette.light })),
  spectrumTable,
  pageBreak(),

  heading(titles[1]),
  citedBody("每个矩阵项保留最小值、最大值、最大相邻绝对跳变及主奇异通道计数。主导项仅表示最大绝对数值贡献，不是因果机制。", 2),
  extremaTable,
  heading("得分主导项的逐链接累计", 2),
  driverTable,
  afterTable("O00 在两种表示的全部8条链接中均主导对角增量；交换侧主导项随路径段变化，不能用端点比例替代逐链接分析。"),
  pageBreak(),

  heading(titles[2]),
  citedBody(`独立重建18个路径单元、54组矩阵、192条矩阵项差分及16条原生链接。谱、矩阵、奇异通道与链接的最大误差分别为 ${independent.max_spectrum_absolute_error}、${independent.max_matrix_absolute_error}、${independent.max_entry_delta_absolute_error} 和 ${independent.max_native_link_absolute_error}；主导项不一致数为 ${independent.driver_mismatch_count}。`, 3),
  para(new ImageRun({ type: "png", data: fs.readFileSync(path.join(root, "seed6-matrix-path.png")), transformation: { width: 500, height: Math.round(500 * 1404 / 2184) } }), { alignment: AlignmentType.CENTER, keepNext: true }),
  para(run("图 1　O00、O01、O10 及其主奇异通道随强度变化，以及同尺寸相邻子空间重叠。非单调段不等于谱交叉。", { size: 16, italics: true }), { alignment: AlignmentType.CENTER }),
  body(`跨表示自一致性为 ${fmt(summary.min_representation_fidelity)}–${fmt(summary.max_representation_fidelity)}；线性点值秩间重叠最大 ${fmt(summary.max_linear_point_off_diagonal)}，单元平均最大 ${fmt(summary.max_cell_average_off_diagonal)}，继续单列嵌入串扰。`),
  body(`端点矩阵、主奇异值与前六谱距离的最大绑定误差分别为 ${fmt(analysis.endpoint_binding.max_matrix_absolute_error)}、${fmt(analysis.endpoint_binding.max_singular_absolute_error)} 和 ${fmt(analysis.endpoint_binding.max_spectrum_absolute_error)}。`),
  pageBreak(),

  heading(titles[3]),
  linkTable,
  afterTable("同尺寸原生链接均保持同谱秩分配占优，但最小重叠出现在 r=0.1→0.1125；离散链接不构成连续路径证明，也不证明真实态交换或避免交叉。"),
  citedBody("路径结果只适用于 seed=6 和当前网格。任何局部极小值、非单调段或主导项变化都不能直接命名为谱交叉、统计显著性或因果机制。旧交换候选属于不同无序实现，不能与路径差分直接相减。", 4),
  body("后续若继续检验，应在相同预登记路径上增加中间点，核查局部跳变是否稳定，而不是选择有利路径段推广到其他种子。"),
  body("复现：python research/floquet-bdg-tbc/analyze_seed6_matrix_path.py；独立复核：python research/floquet-bdg-tbc/verify_seed6_matrix_path.py。"),
  para(run("证据边界：固定 seed=6 的9个强度点、8条离散链接；不新增类别，不作连续路径或热力学极限推断。", { size: 18, color: palette.accent })),
];

const document = new Document({
  creator: "TOE-SYLVA",
  title: "Floquet-BdG 固定种子矩阵路径",
  description: "固定seed的细化强度路径、矩阵项与原生相邻链接。",
  features: { updateFields: true },
  styles: { paragraphStyles: [1, 2].map((level) => ({ id: `TOC${level}`, name: `TOC ${level}`, basedOn: "Normal", next: "Normal", quickFormat: true, run: { font, size: 19, color: palette.dark }, paragraph: { spacing: { after: 70, line: 240 }, indent: { left: (level - 1) * 360 } } })) },
  footnotes: {
    1: { children: [footnote("seed6_matrix_path_protocol.json. Nine preregistered strengths and eight links; four endpoint cells are controls, not new realizations.")] },
    2: { children: [footnote("seed6_matrix_path_analysis.json. Entry and channel dominance denotes numerical contribution only, never causal proof.")] },
    3: { children: [footnote("seed6_matrix_path_independent.json. Eighteen cells, fifty-four matrices, sixteen native links and all entry deltas are independently rebuilt.")] },
    4: { children: [footnote("matched_beta_batch_b_analysis.json, matched_beta_batch_c_analysis.json and swap_candidate_spectrum_analysis.json. Endpoints bind to prior evidence; the old candidate is a different realization.")] },
  },
  sections: [{
    properties: { page: { margin: { top: 900, bottom: 900, left: 1000, right: 1000 } } },
    headers: { default: new Header({ children: [para(run("TOE-SYLVA · Floquet-BdG · 固定种子矩阵路径", { size: 17, color: palette.primary }), { alignment: AlignmentType.CENTER })] }) },
    footers: { default: new Footer({ children: [para(new TextRun({ children: [PageNumber.CURRENT], font, size: 17 }), { alignment: AlignmentType.CENTER })] }) },
    children,
  }],
});
fs.writeFileSync(outputPath, await Packer.toBuffer(document));
