import fs from "node:fs";
import path from "node:path";
import {
  AlignmentType, Document, Footer, FootnoteReferenceRun, Header, HeadingLevel,
  ImageRun, ImportedXmlComponent, Math as MathEquation, MathRun, Packer,
  PageBreak, PageNumber, Paragraph, ShadingType, Table, TableCell, TableRow,
  TextRun, WidthType,
} from "docx";

const outputPath = process.argv[2];
if (!outputPath) throw new Error("Usage: node build_near_miss_report.js /absolute/path/report.docx");
const root = path.dirname(outputPath);
const analysis = JSON.parse(fs.readFileSync(path.join(root, "near_miss_spatial_analysis.json"), "utf8"));
const font = { ascii: "Times New Roman", hAnsi: "Times New Roman", cs: "Times New Roman", eastAsia: "SimSun" };
const palette = { dark: "293B40", primary: "356A64", accent: "A25B3F", light: "687A7E", fill: "EDF3F1" };
const run = (text, options = {}) => new TextRun({ text: String(text), font, size: 20, ...options });
const para = (children, options = {}) => new Paragraph({ spacing: { after: 100, line: 270 }, ...options, children: Array.isArray(children) ? children : [children] });
const body = (text) => para(run(text), { indent: { firstLine: 400 } });
const citedBody = (text, id) => para([run(text), new FootnoteReferenceRun(id)], { indent: { firstLine: 400 } });
const heading = (text, level = 1) => para(run(text, { bold: true, size: level === 1 ? 29 : 24, color: palette.dark }), { heading: level === 1 ? HeadingLevel.HEADING_1 : HeadingLevel.HEADING_2, spacing: { before: 180, after: 110 }, keepNext: true });
const pageBreak = () => new Paragraph({ children: [new PageBreak()] });
const xmlEscape = (value) => String(value).replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;");
const toc = (entries) => {
  const cached = entries.map(({ title, level, page }) => `<w:p><w:pPr><w:pStyle w:val="TOC${level}"/><w:tabs><w:tab w:val="right" w:leader="dot" w:pos="9000"/></w:tabs><w:ind w:left="${Math.max(0, level - 1) * 360}"/></w:pPr><w:r><w:t>${xmlEscape(title)}</w:t></w:r><w:r><w:tab/></w:r><w:r><w:t>${page}</w:t></w:r></w:p>`).join("");
  return ImportedXmlComponent.fromXmlString(`<w:sdt xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:sdtPr><w:alias w:val="目录"/></w:sdtPr><w:sdtContent><w:p><w:r><w:fldChar w:fldCharType="begin" w:dirty="true"/><w:instrText xml:space="preserve"> TOC \\o &quot;1-2&quot; \\h \\z \\u </w:instrText><w:fldChar w:fldCharType="separate"/></w:r></w:p>${cached}<w:p><w:r><w:fldChar w:fldCharType="end"/></w:r></w:p></w:sdtContent></w:sdt>`).root[0];
};
const cell = (text, index, widths, header, size = 10) => new TableCell({
  children: [para(run(text, { size, bold: header }), { spacing: { after: 0, line: 170 } })],
  width: { size: widths[index], type: WidthType.DXA }, margins: { top: 25, bottom: 25, left: 40, right: 40 },
  shading: header ? { type: ShadingType.CLEAR, fill: palette.fill } : undefined,
});
const makeTable = (headers, rows, widths, size = 10) => new Table({
  width: { size: widths.reduce((a, b) => a + b, 0), type: WidthType.DXA }, columnWidths: widths,
  rows: [new TableRow({ tableHeader: true, cantSplit: true, children: headers.map((text, index) => cell(text, index, widths, true, size)) }), ...rows.map((row) => new TableRow({ cantSplit: true, children: row.map((text, index) => cell(text, index, widths, false, size)) }))],
});
const equation = (text) => para(new MathEquation({ children: [new MathRun(text)] }), { alignment: AlignmentType.CENTER, spacing: { before: 60, after: 75 } });
const footnote = (text) => para(run(text, { size: 15 }), { spacing: { after: 30, line: 190 } });
const fmt = (value) => Number(value).toPrecision(5).replace(/\.0+$/, "");
const delta = (label, pair) => analysis.size_deltas.find((row) => row.label === label && row.pair_index === pair);
const rows = (pair) => analysis.cases.map((item) => {
  const row = delta(item.label, pair);
  return [`${item.seed}／${item.strength}`, fmt(row.left10pct), fmt(row.left_inner40), fmt(row.central40), fmt(row.right_inner40), fmt(row.right10pct), fmt(row.edge10pct), fmt(row.asymmetry10pct), `${row.L50 >= 0 ? "+" : ""}${row.L50}`];
});
const table = (pair) => makeTable(["seed／r", "Δ左外10%", "Δ左内40", "Δ中央40", "Δ右内40", "Δ右外10%", "Δedge10%", "ΔA10%", "ΔL50"], rows(pair), [850, 1150, 1100, 1100, 1100, 1150, 1150, 1100, 1206], 8);
const low = delta("near_miss_low", 0), high = delta("near_miss_high", 0), reference = delta("reference_weakening", 0);
const titles = ["一、最近对的左右端来源", "二、固定窗口与次近对图", "三、次近对及解释边界"];
const children = [
  para(run("Floquet-BdG 近 miss 空间分布与次近对", { bold: true, size: 34, color: palette.dark }), { heading: HeadingLevel.TITLE, alignment: AlignmentType.CENTER, spacing: { before: 600, after: 220 } }),
  para(run("原10%端点定义与固定40窗口严格分离", { bold: true, size: 25, color: palette.primary }), { alignment: AlignmentType.CENTER, spacing: { after: 230 } }),
  para(run("两个近 miss · 一个参考 · 最近对与次近对", { size: 20, color: palette.light }), { alignment: AlignmentType.CENTER, spacing: { after: 260 } }),
  para(run("2026-11-11　不新增类别，不补算体 winding，未计算 N=640", { size: 19, color: palette.accent }), { alignment: AlignmentType.CENTER, spacing: { after: 300 } }),
  heading("目录"),
  para(run("以下页码为可见缓存；在 Word/WPS 中更新域可刷新。", { size: 17, italics: true, color: palette.light })),
  toc(titles.map((title, index) => ({ title, level: 1, page: index + 2 }))),
  pageBreak(),

  heading(titles[0]),
  citedBody("只使用已冻结且经过独立复核的 N=400／600 剖面。原类别采用每端10%窗口：N=400 为40格，N=600 为60格；所有尺寸差均为 N=600 减 N=400。", 1),
  equation("e(N) = N/10,  E(N) = L(N) + R(N),  A(N) = |R(N) − L(N)| / E(N)"),
  equation("ΔX = X(600) − X(400)"),
  table(0),
  body(`seed=5、r=0.05：Δ左外10%=${fmt(low.left10pct)}，Δ右外10%=${fmt(low.right10pct)}，故 Δedge10%=${fmt(low.edge10pct)} 仍为正。左端增量超过右端减量，解释了右端减弱但总端点未减弱。`),
  body(`seed=5、r=0.1：Δ左外10%=${fmt(high.left10pct)}，Δ右外10%=${fmt(high.right10pct)}，Δedge10%=${fmt(high.edge10pct)}，ΔA10%=${fmt(high.asymmetry10pct)}。总端点下降而左外增加，形成右端减弱但更对称。`),
  body(`参考 seed=2、r=0.1 同样左增右减，但 ΔA10%=${fmt(reference.asymmetry10pct)}，绝对不对称度上升。它与高强度近 miss 的差异不需要任何新阈值。`),
  para(run(`冻结指标复算最大误差：${analysis.max_original_metric_recompute_error.toExponential(3)}。`, { size: 17, color: palette.light })),
  pageBreak(),

  heading(titles[1]),
  citedBody("固定40窗口只作补充空间诊断：左外40、左内40、中央40、右内40、右外40。signedA40 是带符号量，不能替代原类别的绝对不对称度 A10%。", 2),
  para(new ImageRun({ type: "png", data: fs.readFileSync(path.join(root, "near-miss-spatial.png")), transformation: { width: 500, height: Math.round(500 * 1673 / 2014) } }), { alignment: AlignmentType.CENTER, keepNext: true }),
  para(run("图 1　三行分别为低强度近 miss、高强度近 miss 与参考；左列为最近对，右列为次近对。柱上 Δ 为 N=600−N=400。", { size: 16, italics: true }), { alignment: AlignmentType.CENTER }),
  body(`低强度近 miss 的固定 Δedge40=${fmt(low.edge40)}，与原 Δedge10%=${fmt(low.edge10pct)} 符号不同。这是因为 N=600 的原端点包含第40至59格，而固定40不包含；两套指标各自成立，但不可混用或借此改类。`),
  pageBreak(),

  heading(titles[2]),
  table(1),
  body("三例次近对的 ΔL50 分别为 +88、+81、+17。次近对端部符号并不与最近对一一同步：低强度近 miss 的次近对总端点下降，高强度近 miss 和参考的次近对总端点上升。不能假定最近对的变化会自动传给全部近零谱子空间。"),
  citedBody("次近对不与最近对相加来挽救类别，也不因在谱排序中位于第二就命名为拓扑端点。谱隔离比与联合诊断状态原样保留。", 3),
  body("本轮结论是：两个近 miss 的原10%端点分解都显示左外质量增加。低强度时左增抵消并超过右减；高强度时左增与右减共同降低总外端质量，同时降低绝对不对称度。未复现既不是简单的右端未减弱，也不是端点消失。"),
  body("没有计算新本征对或新种子，没有改变原类别、独立后端数据或阈值。结果只限这三个对照和两种尺寸，不构成统计因果、普适机制、体 winding、材料预测或热力学极限证明。"),
  body("复现：python research/floquet-bdg-tbc/analyze_near_miss_spatial.py。协议、固定40窗口、原10%指标、逐对尺寸差、类别与来源哈希保存在 near_miss_spatial_analysis.json。"),
  para(run("证据边界：既有冻结剖面的描述性空间分解；不新增分类，不后验移动阈值。", { size: 18, color: palette.accent })),
];

const document = new Document({
  creator: "TOE-SYLVA",
  title: "Floquet-BdG 近 miss 空间分布与次近对",
  description: "两个近 miss 与一个参考的左右端和次近对描述性诊断。",
  features: { updateFields: true },
  styles: { paragraphStyles: [1, 2].map((level) => ({ id: `TOC${level}`, name: `TOC ${level}`, basedOn: "Normal", next: "Normal", quickFormat: true, run: { font, size: 19, color: palette.dark }, paragraph: { spacing: { after: 70, line: 240 }, indent: { left: (level - 1) * 360 } } })) },
  footnotes: {
    1: { children: [footnote("repeated_category_analysis.json and independent profile evidence. Original endpoint widths and category definitions are preserved exactly.")] },
    2: { children: [footnote("near_miss_spatial_protocol.json. Fixed40 windows are supplementary; their signed asymmetry is not the original absolute endpoint asymmetry.")] },
    3: { children: [footnote("near_miss_spatial_analysis.json. Second-pair results are descriptive and carry no winding or topological-endpoint claim.")] },
  },
  sections: [{
    properties: { page: { margin: { top: 900, bottom: 900, left: 1000, right: 1000 } } },
    headers: { default: new Header({ children: [para(run("TOE-SYLVA · Floquet-BdG · 近 miss 空间分布与次近对", { size: 17, color: palette.primary }), { alignment: AlignmentType.CENTER })] }) },
    footers: { default: new Footer({ children: [para(new TextRun({ children: [PageNumber.CURRENT], font, size: 17 }), { alignment: AlignmentType.CENTER })] }) },
    children,
  }],
});
fs.writeFileSync(outputPath, await Packer.toBuffer(document));
