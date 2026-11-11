import fs from "node:fs";
import path from "node:path";
import {
  AlignmentType, Document, Footer, FootnoteReferenceRun, Header, HeadingLevel,
  ImageRun, ImportedXmlComponent, Math as MathEquation, MathRun, Packer,
  PageBreak, PageNumber, Paragraph, ShadingType, Table, TableCell, TableRow,
  TextRun, WidthType,
} from "docx";

const outputPath = process.argv[2];
if (!outputPath) throw new Error("Usage: node build_endpoint_report.js /absolute/path/report.docx");
const root = path.dirname(outputPath);
const analysis = JSON.parse(fs.readFileSync(path.join(root, "endpoint_subspace_analysis.json"), "utf8"));
const font = { ascii: "Times New Roman", hAnsi: "Times New Roman", cs: "Times New Roman", eastAsia: "SimSun" };
const palette = { dark: "293B40", primary: "356A64", accent: "A25B3F", light: "687A7E", fill: "EDF3F1" };
const run = (text, options = {}) => new TextRun({ text: String(text), font, size: 20, ...options });
const para = (children, options = {}) => new Paragraph({ spacing: { after: 100, line: 270 }, ...options, children: Array.isArray(children) ? children : [children] });
const body = (text) => para(run(text), { indent: { firstLine: 400 } });
const citedBody = (text, id) => para([run(text), new FootnoteReferenceRun(id)], { indent: { firstLine: 400 } });
const heading = (text, level = 1) => para(run(text, { bold: true, size: level === 1 ? 29 : 24, color: palette.dark }), { heading: level === 1 ? HeadingLevel.HEADING_1 : HeadingLevel.HEADING_2, spacing: { before: 200, after: 110 }, keepNext: true });
const pageBreak = () => new Paragraph({ children: [new PageBreak()] });
const xmlEscape = (value) => String(value).replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;");
const toc = (entries) => {
  const cached = entries.map(({ title, level, page }) => `<w:p><w:pPr><w:pStyle w:val="TOC${level}"/><w:tabs><w:tab w:val="right" w:leader="dot" w:pos="9000"/></w:tabs><w:ind w:left="${Math.max(0, level - 1) * 360}"/></w:pPr><w:r><w:t>${xmlEscape(title)}</w:t></w:r><w:r><w:tab/></w:r><w:r><w:t>${page}</w:t></w:r></w:p>`).join("");
  return ImportedXmlComponent.fromXmlString(`<w:sdt xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:sdtPr><w:alias w:val="目录"/></w:sdtPr><w:sdtContent><w:p><w:r><w:fldChar w:fldCharType="begin" w:dirty="true"/><w:instrText xml:space="preserve"> TOC \\o &quot;1-2&quot; \\h \\z \\u </w:instrText><w:fldChar w:fldCharType="separate"/></w:r></w:p>${cached}<w:p><w:r><w:fldChar w:fldCharType="end"/></w:r></w:p></w:sdtContent></w:sdt>`).root[0];
};
const cell = (text, index, widths, header, size = 12) => new TableCell({
  children: [para(run(text, { size, bold: header }), { spacing: { after: 0, line: 190 } })],
  width: { size: widths[index], type: WidthType.DXA }, margins: { top: 35, bottom: 35, left: 60, right: 60 },
  shading: header ? { type: ShadingType.CLEAR, fill: palette.fill } : undefined,
});
const makeTable = (headers, rows, widths, size = 12) => new Table({
  width: { size: widths.reduce((a, b) => a + b, 0), type: WidthType.DXA }, columnWidths: widths,
  rows: [new TableRow({ tableHeader: true, cantSplit: true, children: headers.map((text, index) => cell(text, index, widths, true, size)) }), ...rows.map((row) => new TableRow({ cantSplit: true, children: row.map((text, index) => cell(text, index, widths, false, size)) }))],
});
const equation = (text) => para(new MathEquation({ children: [new MathRun(text)] }), { alignment: AlignmentType.CENTER, spacing: { before: 65, after: 80 } });
const footnote = (text) => para(run(text, { size: 15 }), { spacing: { after: 30, line: 190 } });
const fmt = (value, digits = 6) => Number(value).toPrecision(digits).replace(/\.0+$/, "");
const titles = ["一、最近／次近子空间判读", "二、两端不对称与备选解释", "三、复核边界与下一对照"];
const pairRows = [];
const endRows = [];
for (const item of analysis.cases) {
  for (const pair of item.pairs) {
    const label = pair.pair_index === 0 ? "最近对" : "次近对";
    pairRows.push([String(item.n), label, fmt(pair.edge_weight), fmt(pair.max_separation_ratio), String(pair.L50), String(pair.L90)]);
    endRows.push([String(item.n), label, fmt(pair.left_edge_weight), fmt(pair.right_edge_weight), fmt(pair.center20_mass)]);
  }
}
const children = [
  para(run("Floquet-BdG 端点子空间诊断", { bold: true, size: 34, color: palette.dark }), { heading: HeadingLevel.TITLE, alignment: AlignmentType.CENTER, spacing: { before: 600, after: 220 } }),
  para(run("N=400 右端主导；N=600 次近对更离域", { bold: true, size: 25, color: palette.primary }), { alignment: AlignmentType.CENTER, spacing: { after: 230 } }),
  para(run("秩二投影 · 最近／次近零能候选 · 原判据不回溯修改", { size: 20, color: palette.light }), { alignment: AlignmentType.CENTER, spacing: { after: 260 } }),
  para(run("2026-11-11　仅诊断候选子空间，未计算 N=640", { size: 19, color: palette.accent }), { alignment: AlignmentType.CENTER, spacing: { after: 300 } }),
  heading("目录"),
  para(run("以下页码为可见缓存；在 Word/WPS 中更新域可刷新。", { size: 17, italics: true, color: palette.light })),
  toc(titles.map((title, index) => ({ title, level: 1, page: index + 2 }))),
  pageBreak(),

  heading(titles[0]),
  citedBody("最近对与次近对均采用秩二 QR 投影子空间权重。第一对逐项复现既有 profile SHA-256、端点权重及 L50/L90；第二对只作机制诊断。", 1),
  equation("W₀(N) = 1,　E = wL + wR"),
  makeTable(["N", "子空间", "端点权重", "最大分离比", "L50", "L90"], pairRows, [650, 1400, 1800, 1900, 1300, 2456], 11),
  para(new ImageRun({ type: "png", data: fs.readFileSync(path.join(root, "endpoint-subspaces.png")), transformation: { width: 490, height: Math.round(490 * 1291 / 1838) } }), { alignment: AlignmentType.CENTER, keepNext: true }),
  para(run("图 1　最近对与次近对的两端覆盖和格点剖面。", { size: 16, italics: true }), { alignment: AlignmentType.CENTER }),
  pageBreak(),

  heading(titles[1]),
  citedBody("N=400 最近对的左／右端权重为 0.134974／0.449289，阈值通过由右端主导。次近对也偏向右端，但其最大分离比为 1，与第三近体距离重合，不是另一个隔离端点候选。", 2),
  makeTable(["N", "子空间", "左端权重", "右端权重", "中心20%质量"], endRows, [700, 1500, 2300, 2300, 2706], 11),
  body("单端权重不等于拓扑证明。N=400 的结果只能保留为局部判据穿越，不能升级为两端同时恢复或热力学体边对应。"),
  citedBody("N=600 次近对端点权重降至 0.0219004，L50 增至 169，中心 20% 质量增至 0.189476，最大分离比为 1。它更接近体谱且更离域，因此不能把最近对未通过简单解释为选错备用端点。", 3),
  equation("E600,次近 = 0.0219004,　L50 = 169,　separation = 1"),
  body("两个案例具有不同无序强度，不能把差异单独归因于链长 N。W₀=1 保留体不变量含义，但不自动恢复端点。"),
  pageBreak(),

  heading(titles[2]),
  makeTable(["检查项", "实测结果", "解释边界"], [
    ["N=400 最近对", "端点权重 0.584262，联合判据通过", "右端主导；不是两端恢复证明"],
    ["N=400 次近对", "右端 0.444069，分离比 1", "端部偏置不能替代谱隔离"],
    ["N=600 最近对", "端点权重 0.370468，判据未通过", "长尾增长；不回溯改判"],
    ["N=600 次近对", "更离域、更接近体谱", "不支持单纯选错子空间的充分解释"],
  ], [2200, 3900, 3406], 11),
  body("下一对照必须在同一无序强度、同一嵌套随机流下比较 profile 与候选子空间，区分无序强度效应和尺寸效应。在新对照完成前，不提出普适恢复标度，不自动扩大为 N=640。"),
  body("复现：python research/floquet-bdg-tbc/analyze_endpoint_subspaces.py。原始数组、首对 SHA-256 和既有 winding／端点状态保存在 endpoint_subspace_analysis.json。"),
  para(run("证据边界：本报告只研究当前有限二次模型的候选子空间，不构成材料预测、实验结论或热力学极限证明。", { size: 18, color: palette.accent })),
];

const document = new Document({
  creator: "TOE-SYLVA",
  title: "Floquet-BdG 端点子空间诊断",
  description: "N=400 与 N=600 最近及次近零能候选子空间的 profile 和体边判据。",
  features: { updateFields: true },
  styles: { paragraphStyles: [1, 2].map((level) => ({ id: `TOC${level}`, name: `TOC ${level}`, basedOn: "Normal", next: "Normal", quickFormat: true, run: { font, size: 19, color: palette.dark }, paragraph: { spacing: { after: 70, line: 240 }, indent: { left: (level - 1) * 360 } } })) },
  footnotes: {
    1: { children: [footnote("endpoint_subspace_analysis.json. Rank-two QR projectors reproduce the frozen first-pair profile hashes, endpoint weights, coverage lengths, and original winding integers.")] },
    2: { children: [footnote("N=400 first and second pairs. The original local threshold crossing is preserved, but the aggregate edge weight is dominated by the right end.")] },
    3: { children: [footnote("N=600 second pair. The third-nearest bulk-distance denominator gives separation ratio 1; the second pair is more delocalized and is not promoted to an endpoint candidate.")] },
  },
  sections: [{
    properties: { page: { margin: { top: 900, bottom: 900, left: 1000, right: 1000 } } },
    headers: { default: new Header({ children: [para(run("TOE-SYLVA · Floquet-BdG · 端点子空间诊断", { size: 17, color: palette.primary }), { alignment: AlignmentType.CENTER })] }) },
    footers: { default: new Footer({ children: [para(new TextRun({ children: [PageNumber.CURRENT], font, size: 17 }), { alignment: AlignmentType.CENTER })] }) },
    children,
  }],
});
fs.writeFileSync(outputPath, await Packer.toBuffer(document));
