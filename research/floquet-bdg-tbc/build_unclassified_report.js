import fs from "node:fs";
import path from "node:path";
import {
  AlignmentType, Document, Footer, FootnoteReferenceRun, Header, HeadingLevel,
  ImageRun, ImportedXmlComponent, Math as MathEquation, MathRun, Packer,
  PageBreak, PageNumber, Paragraph, ShadingType, Table, TableCell, TableRow,
  TextRun, WidthType,
} from "docx";

const outputPath = process.argv[2];
if (!outputPath) throw new Error("Usage: node build_unclassified_report.js /absolute/path/report.docx");
const root = path.dirname(outputPath);
const analysis = JSON.parse(fs.readFileSync(path.join(root, "unclassified_signature_analysis.json"), "utf8"));
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
const cell = (text, index, widths, header, size = 10) => new TableCell({
  children: [para(run(text, { size, bold: header }), { spacing: { after: 0, line: 170 } })],
  width: { size: widths[index], type: WidthType.DXA }, margins: { top: 25, bottom: 25, left: 45, right: 45 },
  shading: header ? { type: ShadingType.CLEAR, fill: palette.fill } : undefined,
});
const makeTable = (headers, rows, widths, size = 10) => new Table({
  width: { size: widths.reduce((a, b) => a + b, 0), type: WidthType.DXA }, columnWidths: widths,
  rows: [new TableRow({ tableHeader: true, cantSplit: true, children: headers.map((text, index) => cell(text, index, widths, true, size)) }), ...rows.map((row) => new TableRow({ cantSplit: true, children: row.map((text, index) => cell(text, index, widths, false, size)) }))],
});
const equation = (text) => para(new MathEquation({ children: [new MathRun(text)] }), { alignment: AlignmentType.CENTER, spacing: { before: 65, after: 80 } });
const footnote = (text) => para(run(text, { size: 15 }), { spacing: { after: 30, line: 190 } });
const fmt = (value, digits = 5) => Number(value).toPrecision(digits).replace(/\.0+$/, "");
const titles = ["一、未归类不是单一机制", "二、右端减弱为何未复现", "三、条件审计与后续边界"];
const rows = analysis.unclassified_cases.map((row) => {
  const item = row.comparison;
  return [String(row.seed), String(row.strength), fmt(item.right_delta), fmt(item.edge_delta), String(item.delta_L50), fmt(item.asymmetry_delta), row.blocking_conditions.join("；")];
});
const near = [caseData(5, 0.05), caseData(5, 0.1), caseData(2, 0.1)];
function caseData(seed, strength) {
  return analysis.unclassified_cases.find((row) => row.seed === seed && row.strength === strength) || analysis.cases.find((row) => row.seed === seed && row.strength === strength);
}
const nearRows = near.map((row) => [
  `${row.seed}／${row.strength}`, fmt(row.comparison.right_delta), fmt(row.comparison.edge_delta),
  String(row.comparison.delta_L50), fmt(row.comparison.asymmetry_delta),
  row.blocking_conditions ? row.blocking_conditions.join("；") : "参考签名",
]);
const children = [
  para(run("Floquet-BdG 未归类与未复现诊断", { bold: true, size: 34, color: palette.dark }), { heading: HeadingLevel.TITLE, alignment: AlignmentType.CENTER, spacing: { before: 600, after: 220 } }),
  para(run("右端减弱但更对称：近 miss 不等于参考机制", { bold: true, size: 25, color: palette.primary }), { alignment: AlignmentType.CENTER, spacing: { after: 230 } }),
  para(run("逐条件审计 · 不新增类别 · 不追加种子", { size: 20, color: palette.light }), { alignment: AlignmentType.CENTER, spacing: { after: 260 } }),
  para(run("2026-11-11　不补算体 winding，未计算 N=640", { size: 19, color: palette.accent }), { alignment: AlignmentType.CENTER, spacing: { after: 300 } }),
  heading("目录"),
  para(run("以下页码为可见缓存；在 Word/WPS 中更新域可刷新。", { size: 17, italics: true, color: palette.light })),
  toc(titles.map((title, index) => ({ title, level: 1, page: index + 2 }))),
  pageBreak(),

  heading(titles[0]),
  citedBody("未归类内部存在三种描述性组合：两个正向但尾部缩短或不对称上升、四个混合符号组合、一个右端减弱但更对称。它们不是新的分类学。", 1),
  makeTable(["seed", "r", "Δ右端", "Δ总端点", "ΔL50", "Δ不对称度", "未满足参考条件"], rows, [600, 650, 1350, 1450, 950, 1500, 3006], 8),
  para(new ImageRun({ type: "png", data: fs.readFileSync(path.join(root, "unclassified-signatures.png")), transformation: { width: 490, height: Math.round(490 * 1218 / 1919) } }), { alignment: AlignmentType.CENTER, keepNext: true }),
  para(run("图 1　未归类的符号组合、描述性计数和近 miss 条件。", { size: 16, italics: true }), { alignment: AlignmentType.CENTER }),
  pageBreak(),

  heading(titles[1]),
  citedBody("参考的右端减弱—尾部变宽要求同时满足：右端差为负、总端点差为负、L50 为正、不对称度差为正。seed=4–7 中没有单元同时满足，故复现数为 0。", 2),
  equation("R < 0, E < 0, ΔL50 > 0, ΔA > 0"),
  makeTable(["seed／r", "Δ右端", "Δ总端点", "ΔL50", "Δ不对称度", "阻断条件"], nearRows, [1300, 1600, 1700, 1300, 1600, 2006], 9),
  body("seed=5、r=0.05 的右端减弱且不对称度增加，但总端点仍增加，缺少 edge_delta_not_negative 条件。seed=5、r=0.1 的右端和总端点均下降、L50 增加，但不对称度下降，形成右端减弱但更对称，缺少 asymmetry_delta_not_positive 条件。"),
  body("两种尺寸的联合判据仍通过，不能称端点消失。近 miss 可指导结构分析，但不能通过修改参考定义制造复现。"),
  pageBreak(),

  heading(titles[2]),
  makeTable(["审计对象", "实测结果", "解释边界"], [
    ["正向—尾短", "2 个对照", "端点增加并不保证尾长或对称性同向变化"],
    ["混合组合", "4 个对照", "不能把不同符号组合合并为单一机制"],
    ["右端减弱但更对称", "1 个对照", "与参考的减弱—变宽机制不同，是近 miss"],
    ["未复现参考类别", "0 个新增案例", "不修改定义、不追加阈值来制造复现"],
  ], [2500, 2200, 4806], 10),
  body("原类别及原始计数完全保留，独立后端验证文件未改变。本轮只重算阻断条件和描述性组合。"),
  body("下一步先检查近 miss 的左右端空间分布和次近对角色，再判断它们是否属于其他可重复结构，而不是把单次符号组合当作相变。"),
  body("复现：python research/floquet-bdg-tbc/analyze_unclassified_signatures.py。全部阻断条件、原始类别、签名组合和来源哈希保存在 unclassified_signature_analysis.json。"),
  para(run("证据边界：已有数据的条件审计；不新增类别，不构成统计因果、材料预测或热力学极限证明。", { size: 18, color: palette.accent })),
];

const document = new Document({
  creator: "TOE-SYLVA",
  title: "Floquet-BdG 未归类与未复现诊断",
  description: "未归类单元和右端减弱近 miss 的逐条件审计。",
  features: { updateFields: true },
  styles: { paragraphStyles: [1, 2].map((level) => ({ id: `TOC${level}`, name: `TOC ${level}`, basedOn: "Normal", next: "Normal", quickFormat: true, run: { font, size: 19, color: palette.dark }, paragraph: { spacing: { after: 70, line: 240 }, indent: { left: (level - 1) * 360 } } })) },
  footnotes: {
    1: { children: [footnote("repeated_category_analysis.json. Seven unclassified contrasts contain different sign combinations and are not a single mechanism.")] },
    2: { children: [footnote("The reference right-weakening signature requires four simultaneous conditions. No new seed satisfies all four; near misses must not be promoted by changing definitions.")] },
    3: { children: [footnote("unclassified_signature_analysis.json. Original categories and original independent verification files remain unchanged.")] },
  },
  sections: [{
    properties: { page: { margin: { top: 900, bottom: 900, left: 1000, right: 1000 } } },
    headers: { default: new Header({ children: [para(run("TOE-SYLVA · Floquet-BdG · 未归类与未复现诊断", { size: 17, color: palette.primary }), { alignment: AlignmentType.CENTER })] }) },
    footers: { default: new Footer({ children: [para(new TextRun({ children: [PageNumber.CURRENT], font, size: 17 }), { alignment: AlignmentType.CENTER })] }) },
    children,
  }],
});
fs.writeFileSync(outputPath, await Packer.toBuffer(document));
