import fs from "node:fs";
import path from "node:path";
import {
  AlignmentType, Document, Footer, FootnoteReferenceRun, Header, HeadingLevel,
  ImageRun, ImportedXmlComponent, Math as MathEquation, MathRun, Packer,
  PageBreak, PageNumber, Paragraph, ShadingType, Table, TableCell, TableRow,
  TextRun, WidthType,
} from "docx";

const outputPath = process.argv[2];
if (!outputPath) throw new Error("Usage: node build_pair_response_report.js /absolute/path/report.docx");
const root = path.dirname(outputPath);
const analysis = JSON.parse(fs.readFileSync(path.join(root, "pair_response_analysis.json"), "utf8"));
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
  width: { size: widths[index], type: WidthType.DXA }, margins: { top: 20, bottom: 20, left: 40, right: 40 },
  shading: header ? { type: ShadingType.CLEAR, fill: palette.fill } : undefined,
});
const makeTable = (headers, rows, widths, size = 10) => new Table({
  width: { size: widths.reduce((a, b) => a + b, 0), type: WidthType.DXA }, columnWidths: widths,
  rows: [new TableRow({ tableHeader: true, cantSplit: true, children: headers.map((text, index) => cell(text, index, widths, true, size)) }), ...rows.map((row) => new TableRow({ cantSplit: true, children: row.map((text, index) => cell(text, index, widths, false, size)) }))],
});
const equation = (text) => para(new MathEquation({ children: [new MathRun(text)] }), { alignment: AlignmentType.CENTER, spacing: { before: 55, after: 70 } });
const footnote = (text) => para(run(text, { size: 15 }), { spacing: { after: 30, line: 190 } });
const fmt = (value) => Number(value).toPrecision(5).replace(/\.0+$/, "");
const response = (seed, strength, pair) => analysis.responses.find((row) => row.seed === seed && row.strength === strength && row.pair_index === pair);
const sign = (value) => (value > 0) - (value < 0);
const relation = (first, second, key) => sign(first[key]) * sign(second[key]) > 0 ? "同号" : sign(first[key]) * sign(second[key]) < 0 ? "反号" : "含零";
const responseRows = analysis.cases.map((item) => {
  const first = response(item.seed, item.strength, 0), second = response(item.seed, item.strength, 1);
  return [`${item.seed}／${item.strength}`, fmt(first.edge_delta), fmt(second.edge_delta), relation(first, second, "edge_delta"), `${first.L50_delta >= 0 ? "+" : ""}${first.L50_delta}`, `${second.L50_delta >= 0 ? "+" : ""}${second.L50_delta}`, relation(first, second, "L50_delta")];
});
const responseTable = makeTable(["seed／r", "最近对Δedge", "次近对Δedge", "edge关系", "最近对ΔL50", "次近对ΔL50", "L50关系"], responseRows, [1000, 1600, 1600, 1100, 1200, 1200, 2206], 9);
const crossTable = (table) => makeTable(["最近对＼次近对", "−", "0", "+"], ["-1", "0", "1"].map((first) => [{ "-1": "−", "0": "0", "1": "+" }[first], String(table[first]["-1"]), String(table[first]["0"]), String(table[first]["1"])]), [3000, 2302, 2302, 2302], 10);
const titles = ["一、16个对照的逐对响应", "二、响应散点与符号列联", "三、结论、边界与态追踪问题"];
const children = [
  para(run("Floquet-BdG 最近对与次近对响应审计", { bold: true, size: 34, color: palette.dark }), { heading: HeadingLevel.TITLE, alignment: AlignmentType.CENTER, spacing: { before: 600, after: 220 } }),
  para(run("谱排序匹配不等于跨尺寸态追踪", { bold: true, size: 25, color: palette.primary }), { alignment: AlignmentType.CENTER, spacing: { after: 230 } }),
  para(run("8个既有种子 · 2个强度 · 16个尺寸对照", { size: 20, color: palette.light }), { alignment: AlignmentType.CENTER, spacing: { after: 260 } }),
  para(run("2026-11-11　不新增类别，不补算体 winding，未计算 N=640", { size: 19, color: palette.accent }), { alignment: AlignmentType.CENTER, spacing: { after: 300 } }),
  heading("目录"),
  para(run("以下页码为可见缓存；在 Word/WPS 中更新域可刷新。", { size: 17, italics: true, color: palette.light })),
  toc(titles.map((title, index) => ({ title, level: 1, page: index + 2 }))),
  pageBreak(),

  heading(titles[0]),
  citedBody("pair_index 只是在每个尺寸内按 |λ−1| 排序后的谱秩。相同 pair_index 不代表跨尺寸追踪到同一个物理态。本审计只使用冻结剖面，端点仍定义为每端 N/10 格。", 1),
  equation("edge = L + R,  A = |R − L| / edge,  ΔX = X(600) − X(400)"),
  para(run("符号关系只按精确符号分为同号、反号、含零，不增加数值阈值，不作统计显著性推断。", { size: 18, color: palette.light })),
  responseTable,
  para(run(`64条原始记录、32条尺寸响应；原指标最大复算误差 ${analysis.max_original_metric_recompute_error.toExponential(3)}。`, { size: 17, color: palette.light })),
  pageBreak(),

  heading(titles[1]),
  citedBody("两对分别展示，不把质量相加来挽救类别，也不把次近对命名为拓扑端点。", 2),
  para(new ImageRun({ type: "png", data: fs.readFileSync(path.join(root, "pair-response-audit.png")), transformation: { width: 500, height: Math.round(500 * 1436 / 1951) } }), { alignment: AlignmentType.CENTER, keepNext: true }),
  para(run("图 1　上排为逐案例响应散点，下排为精确符号列联；绿色为 r=0.05，棕色为 r=0.1。", { size: 16, italics: true }), { alignment: AlignmentType.CENTER }),
  body(`端点响应：同号 ${analysis.edge_relation_counts.same_nonzero}/16，反号 ${analysis.edge_relation_counts.opposite_nonzero}/16。尾长响应：同号 ${analysis.L50_relation_counts.same_nonzero}/16，反号 ${analysis.L50_relation_counts.opposite_nonzero}/16。两项均没有含零案例。`),
  body("端点与尾长呈现不同的符号结构。计数不是相关系数、统计显著性或因果证明。"),
  pageBreak(),

  heading(titles[2]),
  heading("Δedge 符号列联", 2),
  crossTable(analysis.edge_sign_crosstab),
  heading("ΔL50 符号列联", 2),
  crossTable(analysis.L50_sign_crosstab),
  body(`实测端点响应有 ${analysis.edge_relation_counts.opposite_nonzero}/16 反号、${analysis.edge_relation_counts.same_nonzero}/16 同号，因此不能预设最近对的端点变化会自动传给次近对。次近对在两种尺寸均满足既有 profile 联合诊断的对照数为 ${analysis.second_pair_joint_pass_contrasts}/16；这不是端点消失或拓扑否证。`),
  citedBody("原类别及其计数完全保留。即使某些对照同号，也不能将谱秩匹配解释为同一态的连续变化；反号不能被平均掉。", 3),
  body("下一步若要把响应升级为态机制，需要在不同尺寸间建立可复核的子空间对应，例如基于投影重叠的匹配，并检查排序交换与简并。当前数据只支持谱秩层面的描述。"),
  body("本轮没有计算新本征对、新种子或 N=640，没有证明体 winding、材料实现、统计规律或热力学极限。复现：python research/floquet-bdg-tbc/analyze_pair_responses.py。"),
  para(run("证据边界：既有冻结剖面的描述性审计；不新增分类，不后验移动阈值。", { size: 18, color: palette.accent })),
];

const document = new Document({
  creator: "TOE-SYLVA",
  title: "Floquet-BdG 最近对与次近对响应审计",
  description: "全部16个尺寸对照的谱排序匹配响应和符号列联。",
  features: { updateFields: true },
  styles: { paragraphStyles: [1, 2].map((level) => ({ id: `TOC${level}`, name: `TOC ${level}`, basedOn: "Normal", next: "Normal", quickFormat: true, run: { font, size: 19, color: palette.dark }, paragraph: { spacing: { after: 70, line: 240 }, indent: { left: (level - 1) * 360 } } })) },
  footnotes: {
    1: { children: [footnote("pair_response_protocol.json and repeated_category_analysis.json. Original endpoint definitions and all frozen categories are preserved.")] },
    2: { children: [footnote("pair_response_analysis.json. Sixteen contrasts are rank-matched only; counts carry no statistical-significance or causal claim.")] },
    3: { children: [footnote("The second pair has zero joint-profile passes across the sixteen contrasts. This is neither endpoint disappearance nor a bulk-topology falsification.")] },
  },
  sections: [{
    properties: { page: { margin: { top: 900, bottom: 900, left: 1000, right: 1000 } } },
    headers: { default: new Header({ children: [para(run("TOE-SYLVA · Floquet-BdG · 最近对与次近对响应审计", { size: 17, color: palette.primary }), { alignment: AlignmentType.CENTER })] }) },
    footers: { default: new Footer({ children: [para(new TextRun({ children: [PageNumber.CURRENT], font, size: 17 }), { alignment: AlignmentType.CENTER })] }) },
    children,
  }],
});
fs.writeFileSync(outputPath, await Packer.toBuffer(document));
