import fs from "node:fs";
import path from "node:path";
import {
  AlignmentType, Document, Footer, FootnoteReferenceRun, Header, HeadingLevel,
  ImageRun, ImportedXmlComponent, Math as MathEquation, MathFraction, MathRun,
  MathSubScript, Packer,
  PageBreak, PageNumber, Paragraph, ShadingType, Table, TableCell, TableRow,
  TextRun, WidthType,
} from "docx";

const outputPath = process.argv[2];
if (!outputPath) throw new Error("Usage: node build_swap_candidate_spectrum_report.js /absolute/path/report.docx");
const root = path.dirname(outputPath);
const analysis = JSON.parse(fs.readFileSync(path.join(root, "swap_candidate_spectrum_analysis.json"), "utf8"));
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
const equation = (children) => para(new MathEquation({ children: Array.isArray(children) ? children : [new MathRun(children)] }), { alignment: AlignmentType.CENTER, spacing: { before: 55, after: 70 } });
const sub = (base, subscript) => new MathSubScript({ children: [new MathRun(base)], subScript: [new MathRun(subscript)] });
const footnote = (text) => para(run(text, { size: 15 }), { spacing: { after: 30, line: 190 } });
const fmt = (value) => Number(value).toPrecision(5).replace(/\.0+$/, "");
const spectrumRows = analysis.cells.flatMap((item) => item.spectrum.map((row) => [String(item.n), String(row.rank), fmt(row.eigenvalue_real), fmt(row.eigenvalue_imag), fmt(row.phase), fmt(row.distance)]));
const spectrumTable = makeTable(["N", "谱秩", "λ实部", "λ虚部", "相位", "|λ−1|"], spectrumRows, [800, 700, 1800, 1800, 2400, 2406], 8);
const pairRows = analysis.cells.flatMap((item) => item.pairs.map((pair) => [String(item.n), String(pair.pair_index), fmt(pair.center), fmt(pair.within_distance_difference), fmt(pair.max_separation_ratio), String(pair.diagnostic_joint_pass)]));
const pairTable = makeTable(["N", "对", "距离中心", "对内距离差", "既有分离比", "profile联合诊断"], pairRows, [700, 600, 1800, 1800, 1600, 3406], 8);
const overlapRows = ["linear_point", "cell_average"].map((method) => {
  const row = analysis.candidate_overlap[method];
  const values = [0, 1].flatMap((i) => [0, 1].map((j) => fmt(row.overlap_matrix[i][j].overlap)));
  return [method === "linear_point" ? "线性点值" : "单元平均", ...values, fmt(row.diagonal_score), fmt(row.swapped_score)];
});
const overlapTable = makeTable(["方法", "O00", "O01", "O10", "O11", "同谱秩得分", "交换得分"], overlapRows, [1300, 1100, 1100, 1100, 1100, 2100, 2106], 9);
const titles = ["一、前六谱距离与对内TBC简并", "二、中心间隔与交换矩阵", "三、为什么不是谱交叉证明"];
const children = [
  para(run("Floquet-BdG 交换候选谱结构", { bold: true, size: 34, color: palette.dark }), { heading: HeadingLevel.TITLE, alignment: AlignmentType.CENTER, spacing: { before: 600, after: 220 } }),
  para(run("交叉重叠略高不等于物理态交换", { bold: true, size: 25, color: palette.primary }), { alignment: AlignmentType.CENTER, spacing: { after: 230 } }),
  para(run("seed=6，r=0.05 · 两个既有尺寸 · 前六谱距离", { size: 20, color: palette.light }), { alignment: AlignmentType.CENTER, spacing: { after: 260 } }),
  para(run("2026-11-11　不新增类别，不补算体 winding，未计算 N=640", { size: 19, color: palette.accent }), { alignment: AlignmentType.CENTER, spacing: { after: 300 } }),
  heading("目录"),
  para(run("以下页码为可见缓存；在 Word/WPS 中更新域可刷新。", { size: 17, italics: true, color: palette.light })),
  toc(titles.map((title, index) => ({ title, level: 1, page: index + 2 }))),
  pageBreak(),

  heading(titles[0]),
  citedBody("按 |λ−1| 升序排列，报告前六个距离和相位。对内距离差用于数值复现 TBC 简并；10⁻¹⁰ 仅是复现容差，不是物理近简并阈值。", 1),
  equation([
    sub("c", "p"), new MathRun(" = "),
    new MathFraction({ numerator: [sub("d", "2p"), new MathRun(" + "), sub("d", "2p+1")], denominator: [new MathRun("2")] }),
    new MathRun(",　"), sub("δ", "p"), new MathRun(" = |"), sub("d", "2p+1"), new MathRun(" − "), sub("d", "2p"), new MathRun("|"),
  ]),
  spectrumTable,
  heading("两对中心与既有诊断", 2),
  pairTable,
  pageBreak(),

  heading(titles[1]),
  citedBody("对内 TBC 简并与两对中心间隔是不同问题。谱秩由排序构造，不是参数路径上的态追踪。", 2),
  equation([
    new MathRun("Δc = |"), sub("c", "1"), new MathRun(" − "), sub("c", "0"), new MathRun("|,　"),
    sub("R", "c"), new MathRun(" = "),
    new MathFraction({ numerator: [new MathRun("Δc")], denominator: [new MathRun("max("), sub("c", "0"), new MathRun(", "), sub("c", "1"), new MathRun(")")] }),
  ]),
  body(`N=400 的中心间隔为 ${fmt(analysis.cells[0].center_separation)}，相对中心间隔为 ${fmt(analysis.cells[0].center_separation_ratio)}；N=600 分别为 ${fmt(analysis.cells[1].center_separation)} 和 ${fmt(analysis.cells[1].center_separation_ratio)}。中心间隔的尺寸差为 ${fmt(analysis.size_comparison.center_separation_delta)}。`),
  para(new ImageRun({ type: "png", data: fs.readFileSync(path.join(root, "swap-candidate-spectrum.png")), transformation: { width: 500, height: Math.round(500 * 1335 / 2036) } }), { alignment: AlignmentType.CENTER, keepNext: true }),
  para(run("图 1　前六谱距离、两对中心、既有分离比与交换矩阵。", { size: 16, italics: true }), { alignment: AlignmentType.CENTER }),
  body("次近对的既有分离比在两种尺寸均为1，profile 联合诊断均不通过。交换候选不能被解释为新的孤立拓扑端点。"),
  pageBreak(),

  heading(titles[2]),
  body("两种方法的 O01 都分别大于 O00 和 O11，使交换平均分略高。该矩阵关系在三个网格和两种共同表示上成立，但主角度仍大，且次近对没有额外谱隔离。"),
  overlapTable,
  body("对内 TBC 简并与两对中心间隔是不同问题。静态尺寸中的谱秩按定义排序，不能观察到排序自己发生交换；两个尺寸之间也没有连续参数路径，因此不能证明谱交叉或避免交叉。"),
  citedBody("当前结果只支持：交换候选来自特定交叉重叠项，而不是已经证明的物理态交换、近简并相变或体 winding 改变。", 3),
  body("后续若要检验态交换，应在固定尺寸上构造连续参数路径并追踪子空间，而不是把两个静态尺寸的谱秩差异当成路径证据。"),
  body("复现：python research/floquet-bdg-tbc/analyze_swap_candidate_spectrum.py。原始谱值、距离中心、间隔、重叠矩阵和来源哈希保存在 swap_candidate_spectrum_analysis.json。"),
  para(run("证据边界：两个既有尺寸单元的定向谱结构审计；不新增近简并阈值或态交换结论。", { size: 18, color: palette.accent })),
];

const document = new Document({
  creator: "TOE-SYLVA",
  title: "Floquet-BdG 交换候选谱结构",
  description: "seed=6 r=0.05 的谱距离、中心间隔与交换重叠来源。",
  features: { updateFields: true },
  styles: { paragraphStyles: [1, 2].map((level) => ({ id: `TOC${level}`, name: `TOC ${level}`, basedOn: "Normal", next: "Normal", quickFormat: true, run: { font, size: 19, color: palette.dark }, paragraph: { spacing: { after: 70, line: 240 }, indent: { left: (level - 1) * 360 } } })) },
  footnotes: {
    1: { children: [footnote("swap_candidate_spectrum_protocol.json. The 1e-10 tolerance is for numerical reproduction only, not physical near-degeneracy classification.")] },
    2: { children: [footnote("swap_candidate_spectrum_analysis.json. Pairwise TBC degeneracy and pair-center separation are distinct; rank order is constructed by sorting.")] },
    3: { children: [footnote("embedding_census_analysis.json. The O01 cross term drives the swapped-score advantage without proving a physical state exchange or spectral crossing.")] },
  },
  sections: [{
    properties: { page: { margin: { top: 900, bottom: 900, left: 1000, right: 1000 } } },
    headers: { default: new Header({ children: [para(run("TOE-SYLVA · Floquet-BdG · 交换候选谱结构", { size: 17, color: palette.primary }), { alignment: AlignmentType.CENTER })] }) },
    footers: { default: new Footer({ children: [para(new TextRun({ children: [PageNumber.CURRENT], font, size: 17 }), { alignment: AlignmentType.CENTER })] }) },
    children,
  }],
});
fs.writeFileSync(outputPath, await Packer.toBuffer(document));
