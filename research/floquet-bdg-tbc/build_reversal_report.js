import fs from "node:fs";
import path from "node:path";
import {
  AlignmentType, Document, Footer, FootnoteReferenceRun, Header, HeadingLevel,
  ImageRun, ImportedXmlComponent, Math as MathEquation, MathRun, Packer,
  PageBreak, PageNumber, Paragraph, ShadingType, Table, TableCell, TableRow,
  TextRun, WidthType,
} from "docx";

const outputPath = process.argv[2];
if (!outputPath) throw new Error("Usage: node build_reversal_report.js /absolute/path/report.docx");
const root = path.dirname(outputPath);
const analysis = JSON.parse(fs.readFileSync(path.join(root, "reversal_unit_analysis.json"), "utf8"));
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
const cell = (text, index, widths, header, size = 11) => new TableCell({
  children: [para(run(text, { size, bold: header }), { spacing: { after: 0, line: 180 } })],
  width: { size: widths[index], type: WidthType.DXA }, margins: { top: 30, bottom: 30, left: 55, right: 55 },
  shading: header ? { type: ShadingType.CLEAR, fill: palette.fill } : undefined,
});
const makeTable = (headers, rows, widths, size = 11) => new Table({
  width: { size: widths.reduce((a, b) => a + b, 0), type: WidthType.DXA }, columnWidths: widths,
  rows: [new TableRow({ tableHeader: true, cantSplit: true, children: headers.map((text, index) => cell(text, index, widths, true, size)) }), ...rows.map((row) => new TableRow({ cantSplit: true, children: row.map((text, index) => cell(text, index, widths, false, size)) }))],
});
const equation = (text) => para(new MathEquation({ children: [new MathRun(text)] }), { alignment: AlignmentType.CENTER, spacing: { before: 65, after: 80 } });
const footnote = (text) => para(run(text, { size: 15 }), { spacing: { after: 30, line: 190 } });
const fmt = (value, digits = 5) => Number(value).toPrecision(digits).replace(/\.0+$/, "");
const titles = ["一、左右端差值与不对称性", "二、两类不同反转机制", "三、参照边界与后续检验"];
const rows = analysis.cases.map((item) => {
  const row = item.comparison;
  return [String(item.seed), String(item.strength), fmt(row.left_delta), fmt(row.right_delta), fmt(row.edge_delta), String(row.delta_L50), fmt(row.asymmetry_delta)];
});
const detailRows = [];
for (const item of analysis.cases.filter((entry) => entry.seed !== 0)) {
  const row = item.comparison;
  detailRows.push([`${item.seed}／${item.strength}`, "左端", fmt(row.n400_first.left_edge_weight), fmt(row.n600_first.left_edge_weight), fmt(row.left_delta)]);
  detailRows.push([`${item.seed}／${item.strength}`, "右端", fmt(row.n400_first.right_edge_weight), fmt(row.n600_first.right_edge_weight), fmt(row.right_delta)]);
  detailRows.push([`${item.seed}／${item.strength}`, "不对称度", fmt(row.n400_asymmetry), fmt(row.n600_asymmetry), fmt(row.asymmetry_delta)]);
  detailRows.push([`${item.seed}／${item.strength}`, "L50", String(row.n400_first.L50), String(row.n600_first.L50), String(row.delta_L50)]);
}
const children = [
  para(run("Floquet-BdG 反转单元机制诊断", { bold: true, size: 34, color: palette.dark }), { heading: HeadingLevel.TITLE, alignment: AlignmentType.CENTER, spacing: { before: 600, after: 220 } }),
  para(run("右端驱动—对称化，与右端减弱—尾部变宽", { bold: true, size: 25, color: palette.primary }), { alignment: AlignmentType.CENTER, spacing: { after: 230 } }),
  para(run("已验证 16 组 profile 的定向分解 · 不追加种子", { size: 20, color: palette.light }), { alignment: AlignmentType.CENTER, spacing: { after: 260 } }),
  para(run("2026-11-11　不补算体 winding，未计算 N=640", { size: 19, color: palette.accent }), { alignment: AlignmentType.CENTER, spacing: { after: 300 } }),
  heading("目录"),
  para(run("以下页码为可见缓存；在 Word/WPS 中更新域可刷新。", { size: 17, italics: true, color: palette.light })),
  toc(titles.map((title, index) => ({ title, level: 1, page: index + 2 }))),
  pageBreak(),

  heading(titles[0]),
  citedBody("本轮只使用已独立验证的 16 组 profile，重算左右端、覆盖与不对称指标。机制标签仅是描述，不是普适命名或因果证明。", 1),
  equation("ΔE = ΔL + ΔR"),
  makeTable(["seed", "r", "Δ左端", "Δ右端", "Δ总端点", "ΔL50", "Δ不对称度"], rows, [700, 750, 1650, 1650, 1650, 1200, 1906], 10),
  para(new ImageRun({ type: "png", data: fs.readFileSync(path.join(root, "reversal-units.png")), transformation: { width: 490, height: Math.round(490 * 1301 / 2004) } }), { alignment: AlignmentType.CENTER, keepNext: true }),
  para(run("图 1　端部权重、左右不对称度、差值分解与 L50。", { size: 16, italics: true }), { alignment: AlignmentType.CENTER }),
  pageBreak(),

  heading(titles[1]),
  citedBody("seed=1、r=0.05 的右端驱动更显著，L50 从 66 缩短到 35，不对称度下降。谱隔离比没有同步大幅改善，因此不能把变化完全归因于谱隔离；它更像端部空间重新分配与两端趋于对称。", 2),
  makeTable(["seed／r", "指标", "N=400", "N=600", "差值"], detailRows, [1500, 1800, 2300, 2300, 1606], 10),
  citedBody("seed=2、r=0.1 的右端减少约 0.0759，总端点权重下降约 0.0362，L50 从 15 增至 27，不对称度上升。这是尾部变宽和右端减弱的组合。", 3),
  equation("ΔR = −0.0759138,　ΔL50 = +12"),
  body("两种尺寸的端点权重分别约为 0.8217 和 0.7856，联合判据均通过，因此不是端点消失。N=600 的分离比更小，却出现端点权重下降，再次说明谱隔离与端部局域是不同指标。"),
  pageBreak(),

  heading(titles[2]),
  makeTable(["参照单元", "实测分解", "解释边界"], [
    ["r=0.05、seed=0", "尾长增长，端点未恢复", "不能用 seed=0 代表全部随机实现"],
    ["r=0.1、seed=0", "正向端点差主要来自左端", "右端基本持平，不是两端共同增强"],
    ["r=0.05、seed=1", "右端驱动，不对称度下降", "右端驱动—对称化，仅作结构描述"],
    ["r=0.1、seed=2", "右端减弱，L50 增加", "尾部变宽，不是端点消失"],
  ], [2300, 3800, 3406], 11),
  body("不同随机实现的尺寸效应在方向、主导端和对称性上并不相同。下一步应检验这些结构描述是否在更多预登记种子中形成可重复类别，而不是把单次反转当作相变。"),
  body("不补算体 winding，不把局部通过或符号变化升级为拓扑恢复。未计算 N=640。"),
  body("复现：python research/floquet-bdg-tbc/analyze_reversal_units.py。原始对照、次近对摘要、重算误差和来源哈希保存在 reversal_unit_analysis.json。"),
  para(run("证据边界：已有数据的定向解释性分解；不构成普适机制、统计因果、材料预测或热力学极限证明。", { size: 18, color: palette.accent })),
];

const document = new Document({
  creator: "TOE-SYLVA",
  title: "Floquet-BdG 反转单元机制诊断",
  description: "尺寸与无序强度对照中的端部不对称和谱隔离机制。",
  features: { updateFields: true },
  styles: { paragraphStyles: [1, 2].map((level) => ({ id: `TOC${level}`, name: `TOC ${level}`, basedOn: "Normal", next: "Normal", quickFormat: true, run: { font, size: 19, color: palette.dark }, paragraph: { spacing: { after: 70, line: 240 }, indent: { left: (level - 1) * 360 } } })) },
  footnotes: {
    1: { children: [footnote("multi_seed_profile_control.json and multi_seed_independent.json. Existing verified profiles are reused; only decomposition metrics are recomputed.")] },
    2: { children: [footnote("Seed=1, r=0.05. The right-end increase dominates and the left/right asymmetry decreases. This is a structural description, not a universal law.")] },
    3: { children: [footnote("Seed=2, r=0.1. Both sizes still pass the joint endpoint criterion. Broadening and right-end weakening do not imply endpoint loss.")] },
  },
  sections: [{
    properties: { page: { margin: { top: 900, bottom: 900, left: 1000, right: 1000 } } },
    headers: { default: new Header({ children: [para(run("TOE-SYLVA · Floquet-BdG · 反转单元机制诊断", { size: 17, color: palette.primary }), { alignment: AlignmentType.CENTER })] }) },
    footers: { default: new Footer({ children: [para(new TextRun({ children: [PageNumber.CURRENT], font, size: 17 }), { alignment: AlignmentType.CENTER })] }) },
    children,
  }],
});
fs.writeFileSync(outputPath, await Packer.toBuffer(document));
