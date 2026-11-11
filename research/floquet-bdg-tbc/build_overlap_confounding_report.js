import fs from "node:fs";
import path from "node:path";
import {
  AlignmentType, Document, Footer, FootnoteReferenceRun, Header, HeadingLevel,
  ImageRun, ImportedXmlComponent, Math as MathEquation, MathFraction, MathRun,
  MathSubScript, MathSuperScript, Packer, PageBreak, PageNumber, Paragraph,
  ShadingType, Table, TableCell, TableRow, TextRun, WidthType,
} from "docx";

const outputPath = process.argv[2];
if (!outputPath) throw new Error("Usage: node build_overlap_confounding_report.js /absolute/path/report.docx");
const root = path.dirname(outputPath);
const analysis = JSON.parse(fs.readFileSync(path.join(root, "overlap_confounding_analysis.json"), "utf8"));
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
  children: [para(run(text, { size, bold: header }), { spacing: { after: 0, line: 155 } })],
  width: { size: widths[index], type: WidthType.DXA }, margins: { top: 20, bottom: 20, left: 35, right: 35 },
  shading: header ? { type: ShadingType.CLEAR, fill: palette.fill } : undefined,
});
const makeTable = (headers, rows, widths, size = 9) => new Table({
  width: { size: widths.reduce((a, b) => a + b, 0), type: WidthType.DXA }, columnWidths: widths,
  rows: [new TableRow({ tableHeader: true, cantSplit: true, children: headers.map((text, index) => cell(text, index, widths, true, size)) }), ...rows.map((row) => new TableRow({ cantSplit: true, children: row.map((text, index) => cell(text, index, widths, false, size)) }))],
});
const equation = (children) => para(new MathEquation({ children: Array.isArray(children) ? children : [new MathRun(children)] }), { alignment: AlignmentType.CENTER, spacing: { before: 55, after: 70 } });
const sub = (base, subscript) => new MathSubScript({ children: [new MathRun(base)], subScript: [new MathRun(subscript)] });
const subSup = (base, subscript, superScript) => new MathSuperScript({ children: [sub(base, subscript)], superScript: [new MathRun(superScript)] });
const footnote = (text) => para(run(text, { size: 15 }), { spacing: { after: 30, line: 190 } });
const fmt = (value) => Number(value).toPrecision(6).replace(/\.0+$/, "");
const summaryRows = [
  ["同尺寸秩间", `${summary.same_n_rank_control_count}+${summary.native_same_n_rank_control_count}原生`, `原生≤${fmt(summary.max_native_same_n_off_diagonal)}；线性=${fmt(summary.max_linear_point_same_n_off_diagonal)}`, "线性嵌入门槛未通过"],
  ["跨表示自一致", String(summary.representation_fidelity_count), `${fmt(summary.min_representation_fidelity)}–${fmt(summary.max_representation_fidelity)}`, "不作归一化校正"],
  ["β(x) 失配", String(summary.beta_profile_comparison_count), `RMS=${fmt(summary.min_beta_rms_absolute_difference)}–${fmt(summary.max_beta_rms_absolute_difference)}`, "同seed≠同无序实现"],
  ["跨尺寸复现", String(summary.method_grid_count), `最大差=${fmt(analysis.max_cross_size_reproduction_error)}；90对角／6交换`, "不推出尺寸因果"],
];
const summaryTable = makeTable(["诊断", "数量", "实测", "边界"], summaryRows, [1800, 1450, 4200, 2456], 8);
const caseRows = analysis.cases.map((item) => {
  const diagnostic = item.diagnostics[item.diagnostics.length - 1];
  const fidelity = Math.min(...diagnostic.representation_fidelity.map((row) => row.forward));
  const linear = item.methods.linear_point.grids[item.methods.linear_point.grids.length - 1];
  const average = item.methods.cell_average.grids[item.methods.cell_average.grids.length - 1];
  return [
    `s${item.seed}/r${item.strength}`, fmt(linear.diagonal_score), fmt(average.diagonal_score), fmt(fidelity),
    fmt(diagnostic.beta_profile_methods.linear_point.rms_absolute_difference),
    fmt(diagnostic.beta_profile_methods.cell_average.rms_absolute_difference),
    linear.dominant_assignment === average.dominant_assignment ? "是" : "否",
  ];
});
const caseTable = makeTable(["对照", "线性同谱秩", "单元同谱秩", "表示最小", "βRMS线性", "βRMS单元", "一致"], caseRows, [1200, 1500, 1500, 1400, 1400, 1400, 1506], 8);
const titles = ["一、指标与全样本裁决", "二、图证据：串扰与无序失配", "三、逐案例与未竟控制"];
const children = [
  para(run("Floquet-BdG 重叠差异混杂审计", { bold: true, size: 34, color: palette.dark }), { heading: HeadingLevel.TITLE, alignment: AlignmentType.CENTER, spacing: { before: 600, after: 220 } }),
  para(run("尺寸、谱秩、共同表示与无序实现必须分开", { bold: true, size: 24, color: palette.primary }), { alignment: AlignmentType.CENTER, spacing: { after: 230 } }),
  para(run("16个既有对照 · 32个尺寸单元 · 96个β(x)比较", { size: 20, color: palette.light }), { alignment: AlignmentType.CENTER, spacing: { after: 260 } }),
  para(run("2026-11-11　不新增类别，不补算体 winding，未计算 N=640", { size: 19, color: palette.accent }), { alignment: AlignmentType.CENTER, spacing: { after: 300 } }),
  heading("目录"),
  para(run("以下页码为可见缓存；在 Word/WPS 中更新域可刷新。", { size: 17, italics: true, color: palette.light })),
  toc(titles.map((title, index) => ({ title, level: 1, page: index + 2 }))),
  pageBreak(),

  heading(titles[0]),
  citedBody("跨尺寸重叠继续使用二维主子空间奇异值。新增对照只用于辨识数值串扰、表示依赖与无序剖面失配，不把得分升级为物理态保真度。", 1),
  equation([sub("O", "ij"), new MathRun(" = "), new MathFraction({ numerator: [subSup("s", "1", "2"), new MathRun(" + "), subSup("s", "2", "2")], denominator: [new MathRun("2")] })]),
  equation([sub("F", "repr"), new MathRun(" = O("), subSup("Q", "N,pair", "lin"), new MathRun(", "), subSup("Q", "N,pair", "cell"), new MathRun(")")]),
  body("本轮不做归一化修正：不把跨尺寸得分除以跨表示自一致性，也不将任何比值解释为尺寸无关的物理重叠。"),
  summaryTable,
  para(run(`冻结剖面最大误差 ${analysis.max_profile_absolute_error.toExponential(3)}；跨尺寸矩阵最大复现差 ${analysis.max_cross_size_reproduction_error.toExponential(3)}。`, { size: 17, color: palette.light })),
  pageBreak(),

  heading(titles[1]),
  citedBody("线性点值嵌入的秩间重叠超过预登记10⁻¹²门槛；这不是原始本征矢失去正交性，而是嵌入诱导的谱秩串扰。", 2),
  para(new ImageRun({ type: "png", data: fs.readFileSync(path.join(root, "overlap-confounding-audit.png")), transformation: { width: 500, height: Math.round(500 * 1379 / 1998) } }), { alignment: AlignmentType.CENTER, keepNext: true }),
  para(run("图 1　原始跨尺寸得分、跨表示范围、β(x) RMS差与嵌入后秩间控制。右下图显示下限1e-18，JSON保留原值。", { size: 16, italics: true }), { alignment: AlignmentType.CENTER }),
  body(`原生QR与单元平均的秩间重叠分别不超过 ${fmt(summary.max_native_same_n_off_diagonal)} 和 ${fmt(summary.max_cell_average_same_n_off_diagonal)}；线性嵌入达到 ${fmt(summary.max_linear_point_same_n_off_diagonal)}。`),
  body(`96个β(x)比较的RMS均不低于 ${fmt(summary.min_beta_rms_absolute_difference)}，最大绝对相关系数为 ${fmt(summary.max_absolute_beta_pearson_correlation)}。同一seed并不提供同一无序实现。`),
  pageBreak(),

  heading(titles[2]),
  para(run("M=4800；表示最小值为每个案例跨N、跨两对的最小跨表示自一致性。", { size: 17, color: palette.light })),
  caseTable,
  body("现有跨尺寸差异不能归因于尺寸单独作用：尺寸、无序实现与共同表示选择仍然混杂。线性嵌入的秩间门槛失败也必须保留，不能通过后验改阈值消除。"),
  citedBody("下一步应预先固定同一个连续或嵌套无序剖面β(x)，在N=400与N=600上采样，再重算相同诊断；这才构成尺寸隔离控制。", 3),
  body("未完成该控制前，不宣称尺寸因果、普适标度、真实态交换、次近对拓扑性或体winding。复现：python research/floquet-bdg-tbc/analyze_overlap_confounding.py。"),
  para(run("证据边界：16个既有对照的直接计算；不新增物理单元，不做统计显著性或热力学极限推断。", { size: 18, color: palette.accent })),
];

const document = new Document({
  creator: "TOE-SYLVA",
  title: "Floquet-BdG 重叠差异混杂审计",
  description: "尺寸、谱秩、共同表示和无序剖面失配的全样本审计。",
  features: { updateFields: true },
  styles: { paragraphStyles: [1, 2].map((level) => ({ id: `TOC${level}`, name: `TOC ${level}`, basedOn: "Normal", next: "Normal", quickFormat: true, run: { font, size: 19, color: palette.dark }, paragraph: { spacing: { after: 70, line: 240 }, indent: { left: (level - 1) * 360 } } })) },
  footnotes: {
    1: { children: [footnote("overlap_confounding_protocol.json. All sixteen existing contrasts; no normalization correction or new physics cells.")] },
    2: { children: [footnote("overlap_confounding_analysis.json. Native QR and cell-average preserve the rank control; linear interpolation can induce off-diagonal leakage.")] },
    3: { children: [footnote("A common beta(x) sampling control is required before attributing cross-size differences to N alone.")] },
  },
  sections: [{
    properties: { page: { margin: { top: 900, bottom: 900, left: 1000, right: 1000 } } },
    headers: { default: new Header({ children: [para(run("TOE-SYLVA · Floquet-BdG · 重叠差异混杂审计", { size: 17, color: palette.primary }), { alignment: AlignmentType.CENTER })] }) },
    footers: { default: new Footer({ children: [para(new TextRun({ children: [PageNumber.CURRENT], font, size: 17 }), { alignment: AlignmentType.CENTER })] }) },
    children,
  }],
});
fs.writeFileSync(outputPath, await Packer.toBuffer(document));
