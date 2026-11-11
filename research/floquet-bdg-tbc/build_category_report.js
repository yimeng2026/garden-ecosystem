import fs from "node:fs";
import path from "node:path";
import {
  AlignmentType, Document, Footer, FootnoteReferenceRun, Header, HeadingLevel,
  ImageRun, ImportedXmlComponent, Math as MathEquation, MathRun, Packer,
  PageBreak, PageNumber, Paragraph, ShadingType, Table, TableCell, TableRow,
  TextRun, WidthType,
} from "docx";

const outputPath = process.argv[2];
if (!outputPath) throw new Error("Usage: node build_category_report.js /absolute/path/report.docx");
const root = path.dirname(outputPath);
const analysis = JSON.parse(fs.readFileSync(path.join(root, "repeated_category_analysis.json"), "utf8"));
const independent = JSON.parse(fs.readFileSync(path.join(root, "category_new_cells_independent.json"), "utf8"));
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
const titles = ["一、类别计数与结构分布", "二、逐种子分类结果", "三、复现候选与未复现边界"];
const categories = Object.keys(analysis.category_counts);
const countRows = categories.map((category) => [category, String(analysis.by_strength["0.05"][category]), String(analysis.by_strength["0.1"][category]), String(analysis.category_counts[category]), String(analysis.new_seed_category_counts[category])]);
const caseRows = analysis.cases.map((row) => {
  const item = row.comparison;
  return [String(row.seed), String(row.strength), fmt(item.left_delta), fmt(item.right_delta), String(item.delta_L50), fmt(item.asymmetry_delta), row.category];
});
const maxError = Math.max(...independent.cases.flatMap((item) => item.pairs.map((pair) => pair.max_profile_absolute_error)));
const children = [
  para(run("Floquet-BdG 端部机制类别检验", { bold: true, size: 34, color: palette.dark }), { heading: HeadingLevel.TITLE, alignment: AlignmentType.CENTER, spacing: { before: 600, after: 220 } }),
  para(run("对称化出现复现候选，减弱型暂未复现", { bold: true, size: 25, color: palette.primary }), { alignment: AlignmentType.CENTER, spacing: { after: 230 } }),
  para(run("seed=0–7 · 16 个尺寸对照 · 冻结类别条件", { size: 20, color: palette.light }), { alignment: AlignmentType.CENTER, spacing: { after: 260 } }),
  para(run("2026-11-11　不追加阈值，不补算体 winding", { size: 19, color: palette.accent }), { alignment: AlignmentType.CENTER, spacing: { after: 300 } }),
  heading("目录"),
  para(run("以下页码为可见缓存；在 Word/WPS 中更新域可刷新。", { size: 17, italics: true, color: palette.light })),
  toc(titles.map((title, index) => ({ title, level: 1, page: index + 2 }))),
  pageBreak(),

  heading(titles[0]),
  citedBody("新增预登记 seed=4–7 与既有 seed=0–3 合并评估。类别由冻结的符号条件给出，未归类单元全部保留，不追加阈值，也不强行命名。", 1),
  makeTable(["类别", "r=0.05", "r=0.1", "合计", "seed=4–7"], countRows, [5000, 1200, 1200, 1000, 1106], 9),
  equation("R > L > 0, ΔA < 0　与　R < 0, E < 0, ΔL50 > 0, ΔA > 0"),
  para(new ImageRun({ type: "png", data: fs.readFileSync(path.join(root, "repeated-categories.png")), transformation: { width: 490, height: Math.round(490 * 826 / 1999) } }), { alignment: AlignmentType.CENTER, keepNext: true }),
  para(run("图 1　类别计数及右端差—不对称度差分布。", { size: 16, italics: true }), { alignment: AlignmentType.CENTER }),
  pageBreak(),

  heading(titles[1]),
  citedBody("16 个对照全部列出。类别是组织后续分析的结构标签，不是拓扑相变、统计因果或热力学判据。", 2),
  makeTable(["seed", "r", "Δ左端", "Δ右端", "ΔL50", "Δ不对称度", "类别"], caseRows, [600, 650, 1350, 1350, 950, 1500, 3106], 8),
  body("原始左右端、L90、次近对摘要及全部剖面保存在 repeated_category_analysis.json 中。"),
  pageBreak(),

  heading(titles[2]),
  citedBody("右端驱动—对称化在 seed=4–7 中复现 2 例，右端减弱—尾部变宽为 0 例。前者只能称为可重复候选，后者目前不能称为可重复类别。", 3),
  makeTable(["类别", "seed=4–7", "全部 8 种子", "本轮判定"], [
    ["右端驱动—对称化", "2", "3", "出现复现候选，仍需区分强度和种子"],
    ["右端减弱—尾部变宽", "0", "1", "未复现，不宣称可重复"],
    ["左端驱动阈值", "1", "2", "保留为另一类结构描述"],
    ["尾长增长且端点未恢复", "2", "3", "继续作为未恢复边界"],
    ["未归类", "3", "7", "不强行命名，不追加阈值"],
  ], [3100, 1600, 1600, 3206], 10),
  body("新种子中出现至少一个参考结构，支持‘可重复候选’这一弱表述；但不同强度、不同种子仍不等价，未复现同样是有效结果。"),
  body("不补算体 winding，不把类别或局部通过升级为拓扑恢复。未计算 N=640。"),
  body(`新增 16 个单元已用 SciPy 后端与直接 Gram 投影独立复核，最大剖面绝对误差为 ${maxError.toExponential(3)}。原始 seed=0–3 的独立验证保持不变。`),
  para(run("证据边界：八种子的描述性类别检验；不构成普适机制、统计因果、材料预测或热力学极限证明。", { size: 18, color: palette.accent })),
];

const document = new Document({
  creator: "TOE-SYLVA",
  title: "Floquet-BdG 端部机制类别检验",
  description: "八种子的端部结构类别及其可重复性。",
  features: { updateFields: true },
  styles: { paragraphStyles: [1, 2].map((level) => ({ id: `TOC${level}`, name: `TOC ${level}`, basedOn: "Normal", next: "Normal", quickFormat: true, run: { font, size: 19, color: palette.dark }, paragraph: { spacing: { after: 70, line: 240 }, indent: { left: (level - 1) * 360 } } })) },
  footnotes: {
    1: { children: [footnote("repeated_category_protocol.json and category_new_cells.json. New seed=4..7 cells are evaluated with frozen sign conditions; no post-hoc threshold selection.")] },
    2: { children: [footnote("repeated_category_analysis.json. All sixteen size contrasts and all unclassified cases are retained.")] },
    3: { children: [footnote("category_new_cells_independent.json. SciPy eig and direct Gram projectors reproduce the new cells; earlier seed=0..3 verification is unchanged.")] },
  },
  sections: [{
    properties: { page: { margin: { top: 900, bottom: 900, left: 1000, right: 1000 } } },
    headers: { default: new Header({ children: [para(run("TOE-SYLVA · Floquet-BdG · 端部机制类别检验", { size: 17, color: palette.primary }), { alignment: AlignmentType.CENTER })] }) },
    footers: { default: new Footer({ children: [para(new TextRun({ children: [PageNumber.CURRENT], font, size: 17 }), { alignment: AlignmentType.CENTER })] }) },
    children,
  }],
});
fs.writeFileSync(outputPath, await Packer.toBuffer(document));
