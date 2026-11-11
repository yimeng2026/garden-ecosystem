import fs from "node:fs";
import path from "node:path";
import {
  AlignmentType, Document, Footer, FootnoteReferenceRun, Header, HeadingLevel,
  ImageRun, ImportedXmlComponent, Math as MathEquation, MathFraction, MathRun,
  MathSubScript, MathSuperScript, Packer, PageBreak, PageNumber, Paragraph,
  ShadingType, Table, TableCell, TableRow, TextRun, WidthType,
} from "docx";

const outputPath = process.argv[2];
if (!outputPath) throw new Error("Usage: node build_overlap_matrix_response_report.js /absolute/path/report.docx");
const root = path.dirname(outputPath);
const analysis = JSON.parse(fs.readFileSync(path.join(root, "overlap_matrix_response_analysis.json"), "utf8"));
const independent = JSON.parse(fs.readFileSync(path.join(root, "overlap_matrix_response_independent.json"), "utf8"));
const summary = analysis.summary;
const controls = analysis.high_strength_controls;
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
const range = (values) => `${fmt(values[0])}–${fmt(values[1])}`;
const entry = (method, name) => analysis.entry_summary.find((row) => row.method === method && row.m === 4800 && row.entry === name);
const signText = (row) => `${row.delta_sign_counts.positive}+／${row.delta_sign_counts.negative}−`;
const channelText = (row) => `s₁:${row.dominant_singular_channel_counts["0"] ?? 0}／s₂:${row.dominant_singular_channel_counts["1"] ?? 0}`;
const entryTable = makeTable(["项", "LP比值", "LP符号", "LP分母范围", "CA比值", "CA符号", "CA分母范围"], ["O00", "O01", "O10", "O11"].map((name) => {
  const lp = entry("linear_point", name);
  const ca = entry("cell_average", name);
  return [name, range(lp.ratio_range), signText(lp), range(lp.before_overlap_range), range(ca.ratio_range), signText(ca), range(ca.before_overlap_range)];
}), [800, 1700, 950, 1800, 1700, 950, 2006], 7);
const driverRows = [];
for (const [group, entries] of [["diagonal", ["O00", "O11"]], ["swapped", ["O01", "O10"]]]) {
  for (const method of ["linear_point", "cell_average"]) {
    const rows = analysis.method_grid_transitions.filter((row) => row.method === method && row.m === 4800);
    const counts = entries.map((name) => `${name}:${rows.filter((row) => row[`dominant_${group}_entry`] === name).length}`).join("；");
    const ratios = rows.map((row) => row[`${group}_score_ratio`]).filter((value) => value !== null);
    driverRows.push([group, method, counts, range([Math.min(...ratios), Math.max(...ratios)])]);
  }
}
const driverTable = makeTable(["得分组", "方法", "主导项计数（8个种子）", "得分比范围"], driverRows, [1300, 1900, 4200, 2506], 8);
const channelTable = makeTable(["矩阵项", "LP第一／第二通道", "CA第一／第二通道"], ["O00", "O01", "O10", "O11"].map((name) => [name, channelText(entry("linear_point", name)), channelText(entry("cell_average", name))]), [1400, 4250, 4256], 8);
const denominatorTable = makeTable(["矩阵项", "LP原分母范围", "CA原分母范围"], ["O00", "O01", "O10", "O11"].map((name) => [name, range(entry("linear_point", name).before_overlap_range), range(entry("cell_average", name).before_overlap_range)]), [1400, 4250, 4256], 8);
const titles = ["一、矩阵项与差分定义", "二、主导矩阵项与主奇异通道", "三、图证据与独立复算", "四、近零分母与解释边界"];
const children = [
  para(run("Floquet-BdG 重叠矩阵响应分解", { bold: true, size: 32, color: palette.dark }), { heading: HeadingLevel.TITLE, alignment: AlignmentType.CENTER, spacing: { before: 560, after: 220 } }),
  para(run("从方向计数到矩阵项与主奇异通道", { bold: true, size: 25, color: palette.primary }), { alignment: AlignmentType.CENTER, spacing: { after: 230 } }),
  para(run("48个方法—网格配对 · 192个矩阵项 · 384个奇异通道", { size: 20, color: palette.light }), { alignment: AlignmentType.CENTER, spacing: { after: 260 } }),
  para(run(`${analysis.report_date}　不新增物理单元，不补算体 winding，未计算 N=640`, { size: 19, color: palette.accent }), { alignment: AlignmentType.CENTER, spacing: { after: 300 } }),
  heading("目录"),
  para(run("以下页码为可见缓存；在 Word/WPS 中更新域可刷新。", { size: 17, italics: true, color: palette.light })),
  toc(titles.map((title, index) => ({ title, level: 1, page: index + 2 }))),
  pageBreak(),

  heading(titles[0]),
  citedBody("直接读取三批源矩阵，比较 r=0.1→0.2 的同一主剖面配对，不新增 Floquet 单元。保留全部矩阵项、差分、比值和主奇异通道，不归一化重叠。", 1),
  equation([sub("O", "ij"), new MathRun(" = "), new MathFraction({ numerator: [subSup("s", "1", "2"), new MathRun(" + "), subSup("s", "2", "2")], denominator: [new MathRun("2")] })]),
  equation([new MathRun("Δ"), sub("O", "ij"), new MathRun(" = "), sub("O", "ij"), new MathRun("(0.2) − "), sub("O", "ij"), new MathRun("(0.1)")]),
  para(run("“主导项”仅表示最大绝对数值贡献，不是因果物理机制。下表列出 M=4800 的比值、差分符号与原分母范围。", { size: 18, color: palette.light })),
  entryTable,
  pageBreak(),

  heading(titles[1]),
  citedBody("对角得分变化由 O00 与 O11 的差分共同决定，交换得分变化由 O01 与 O10 决定。每个矩阵项再分解为第一和第二主奇异值通道。", 2),
  driverTable,
  afterTable("M=4800 上，O00 在两种表示的全部8个种子中均为对角得分增量主导项；交换侧则由 O01 和 O10 分担主导作用。分配方向不变不等于各项不变。"),
  channelTable,
  afterTable("O01、O10、O11 在两种表示的全部8个种子中均由第一主奇异值通道主导；O00 以第一通道为主，但保留第二通道的反例。"),
  pageBreak(),

  heading(titles[2]),
  citedBody(`独立复算覆盖48个方法—网格配对、192个矩阵项和384个主奇异通道。差分、比值、log₂比值与主导项的最大误差为 ${independent.max_delta_absolute_error}、${independent.max_ratio_absolute_error}、${independent.max_log2_ratio_absolute_error} 和 ${independent.driver_mismatch_count}。`, 3),
  para(new ImageRun({ type: "png", data: fs.readFileSync(path.join(root, "overlap-matrix-response.png")), transformation: { width: 500, height: Math.round(500 * 1378 / 2130) } }), { alignment: AlignmentType.CENTER, keepNext: true }),
  para(run("图 1　矩阵项log₂比值、差分符号、主导矩阵项与主奇异通道。极大比值须结合原分母解释。", { size: 16, italics: true }), { alignment: AlignmentType.CENTER }),
  body(`96个跨表示差分符号比较中，一致 ${summary.representation_sign_agreement_count} 个，不一致 ${summary.representation_sign_disagreement_count} 个；这不证明表示不变性。`),
  body(`r=0.2 跨表示自一致性为 ${range(controls.representation_fidelity_range)}；线性点值秩间重叠最大 ${fmt(controls.max_linear_point_off_diagonal)}，单元平均最大 ${fmt(controls.max_cell_average_off_diagonal)}，继续单列嵌入串扰。`),
  pageBreak(),

  heading(titles[3]),
  denominatorTable,
  afterTable("近零分母会放大比值。O01、O10、O11 的极端放大倍数必须与 ΔO、原分母和主奇异值共同阅读，不能直接当成同等大小的物理效应。"),
  citedBody("矩阵项分解可以定位数值来源，但不能外推为普遍尺寸律、真实态交换、谱交叉、统计显著性或因果机制。旧交换候选仍属于不同无序实现，不能与本次差分直接相减。", 4),
  body("后续若提出机制解释，应在固定尺寸连续路径上追踪同一矩阵项及主奇异通道，而不是仅凭横断面的比值命名过程。"),
  body("复现：python research/floquet-bdg-tbc/analyze_overlap_matrix_response.py；独立复核：python research/floquet-bdg-tbc/verify_overlap_matrix_response.py。"),
  para(run("证据边界：8组同主剖面高强度配对的描述性矩阵分解；不筛选案例，不新增类别，不作热力学极限推断。", { size: 18, color: palette.accent })),
];

const document = new Document({
  creator: "TOE-SYLVA",
  title: "Floquet-BdG 重叠矩阵响应分解",
  description: "矩阵项、差分、比值与主奇异通道的配对数值分解。",
  features: { updateFields: true },
  styles: { paragraphStyles: [1, 2].map((level) => ({ id: `TOC${level}`, name: `TOC ${level}`, basedOn: "Normal", next: "Normal", quickFormat: true, run: { font, size: 19, color: palette.dark }, paragraph: { spacing: { after: 70, line: 240 }, indent: { left: (level - 1) * 360 } } })) },
  footnotes: {
    1: { children: [footnote("overlap_matrix_response_protocol.json and matched_beta_batch_a/b/c_analysis.json. All matrix entries and singular channels are read from existing evidence; no new Floquet cells are computed.")] },
    2: { children: [footnote("overlap_matrix_response_analysis.json. Driver labels denote largest absolute numerical contributions, not causal physical mechanisms.")] },
    3: { children: [footnote("overlap_matrix_response_independent.json. Every entry, ratio, singular-channel delta and driver is independently rechecked from stored source matrices.")] },
    4: { children: [footnote("matched_beta_batch_c_analysis.json and swap_candidate_spectrum_analysis.json. The old swap candidate is a different disorder realization and cannot be subtracted from this paired response.")] },
  },
  sections: [{
    properties: { page: { margin: { top: 900, bottom: 900, left: 1000, right: 1000 } } },
    headers: { default: new Header({ children: [para(run("TOE-SYLVA · Floquet-BdG · 重叠矩阵响应分解", { size: 17, color: palette.primary }), { alignment: AlignmentType.CENTER })] }) },
    footers: { default: new Footer({ children: [para(new TextRun({ children: [PageNumber.CURRENT], font, size: 17 }), { alignment: AlignmentType.CENTER })] }) },
    children,
  }],
});
fs.writeFileSync(outputPath, await Packer.toBuffer(document));
