import fs from "node:fs";
import path from "node:path";
import {
  AlignmentType, Document, Footer, FootnoteReferenceRun, Header, HeadingLevel,
  ImageRun, ImportedXmlComponent, Math as MathEquation, MathRun, Packer,
  PageBreak, PageNumber, Paragraph, ShadingType, Table, TableCell, TableRow,
  TextRun, WidthType,
} from "docx";

const outputPath = process.argv[2];
if (!outputPath) throw new Error("Usage: node build_scale_report.js /absolute/path/SCALE.docx");
const root = path.dirname(outputPath);
const data = JSON.parse(fs.readFileSync(path.join(root, "scale_diagnostic.json"), "utf8"));
const independent = JSON.parse(fs.readFileSync(path.join(root, "scale_independent_n400.json"), "utf8"));
const metrics = JSON.parse(fs.readFileSync(path.join(root, "n400_scale.json"), "utf8"));
const old = JSON.parse(fs.readFileSync(path.join(path.dirname(root), "floquet-bdg-localization-scale", "localization_scale.json"), "utf8"));
const oldCase = old.cases.find((caseData) => caseData.strength === 0.1 && caseData.seed === 0);
const row = data.rows[0];
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
const cell = (text, index, widths, header, size = 13) => new TableCell({
  children: [para(run(text, { size, bold: header }), { spacing: { after: 0, line: 190 } })],
  width: { size: widths[index], type: WidthType.DXA }, margins: { top: 30, bottom: 30, left: 60, right: 60 },
  shading: header ? { type: ShadingType.CLEAR, fill: palette.fill } : undefined,
});
const makeTable = (headers, rows, widths, size = 13) => new Table({
  width: { size: widths.reduce((a, b) => a + b, 0), type: WidthType.DXA }, columnWidths: widths,
  rows: [new TableRow({ tableHeader: true, cantSplit: true, children: headers.map((text, index) => cell(text, index, widths, true, size)) }), ...rows.map((row) => new TableRow({ cantSplit: true, children: row.map((text, index) => cell(text, index, widths, false, size)) }))],
});
const equation = (text) => para(new MathEquation({ children: [new MathRun(text)] }), { alignment: AlignmentType.CENTER, spacing: { before: 65, after: 80 } });
const footnote = (text) => para(run(text, { size: 15 }), { spacing: { after: 30, line: 190 } });
const fmt = (value, digits = 6) => value === null || value === undefined ? "—" : typeof value === "string" ? value : Number(value).toPrecision(digits).replace(/\.0+$/, "");
const titles = ["一、N=400 阈值穿越", "二、覆盖尾部与独立复核", "三、N=600 的诊断价值"];
const thresholdRows = [
  ["主 W0 原始值", "0.999895548527", fmt(row.zero.value, 12)],
  ["最小 0 体隙", "0.00347553", fmt(row.zero.min_bulk_gap)],
  ["端点权重", "0.495586", fmt(row.endpoint.zero.edge_weight)],
  ["最大分离比", "0.0167445", fmt(Math.max(...row.endpoint.zero.separation_ratios))],
  ["端点联合判据", "False", String(row.endpoint.zero.joint_pass)],
];
const coverageRows = [["L50", "L90", "固定20质量", "中心20%质量", "N·IPR"]];
for (const metric of ["L50", "L90", "mass20", "center20_mass", "n_subspace_ipr"]) {
  coverageRows.push([metric, ...oldCase.rows.map((item) => fmt(item[metric])), fmt(metrics[metric])]);
}
const children = [
  para(run("Floquet-BdG N=400 阈值边缘诊断", { bold: true, size: 34, color: palette.dark }), { heading: HeadingLevel.TITLE, alignment: AlignmentType.CENTER, spacing: { before: 600, after: 220 } }),
  para(run("体 winding 与端点阈值同时穿越，但长覆盖尾部仍需分辨", { bold: true, size: 24, color: palette.primary }), { alignment: AlignmentType.CENTER, spacing: { after: 230 } }),
  para(run("主双网格 · 嵌套 RNG · 原始 expm＋Schur 独立复核", { size: 20, color: palette.light }), { alignment: AlignmentType.CENTER, spacing: { after: 260 } }),
  para(run("2026-11-11　N=400 不是恢复保证", { size: 19, color: palette.accent }), { alignment: AlignmentType.CENTER, spacing: { after: 300 } }),
  heading("目录"),
  para(run("以下页码为可见缓存；在 Word/WPS 中更新域可刷新。", { size: 17, italics: true, color: palette.light })),
  toc(titles.map((title, index) => ({ title, level: 1, page: index + 2 }))),
  pageBreak(),

  heading(titles[0]),
  citedBody("主积分使用 dθ=0.05/0.025 双网格和 eigh(iK) 自由传播；Schur 周期化、体隙和整数判据均未改变。N=400 的端点联合判据首次由 False 转为 True。", 1),
  equation("W0(N=400) = 1,　端点权重 = 0.584262 > 0.5"),
  makeTable(["项目", "N=320", "N=400"], thresholdRows, [3000, 3200, 3306], 12),
  para(new ImageRun({ type: "png", data: fs.readFileSync(path.join(root, "n400-result.png")), transformation: { width: 500, height: Math.round(500 * 691 / 1527) } }), { alignment: AlignmentType.CENTER, keepNext: true }),
  para(run("图 1　主积分与独立复核一致，端点阈值同时穿越。", { size: 16, italics: true }), { alignment: AlignmentType.CENTER }),
  pageBreak(),

  heading(titles[1]),
  citedBody("N=400 的 L50 从 33 降为 24，但 L90 从 129 增至 133，包络 R² 约 0.332。局部阈值穿越不等于长覆盖尾部已经平台化。", 2),
  makeTable(["指标", "N=80", "N=160", "N=320", "N=400"], coverageRows, [1900, 1900, 1900, 1900, 1906], 11),
  para(new ImageRun({ type: "png", data: fs.readFileSync(path.join(root, "n400-coverage.png")), transformation: { width: 490, height: Math.round(490 * 782 / 1592) } }), { alignment: AlignmentType.CENTER, keepNext: true }),
  para(run("图 2　L50 下降与 L90 增长并存；不能用单一指数恢复律概括。", { size: 16, italics: true }), { alignment: AlignmentType.CENTER }),
  pageBreak(),

  heading(titles[2]),
  citedBody("原始 expm＋Schur 行列式复核使用 dθ=0.1，得到 W0=1，与主双网格整数一致；最大半周期对称误差约 1.48×10⁻¹³。", 3),
  makeTable(["检查项", "主结果", "独立结果"], [
    ["winding", `${row.zero.status}/${row.zero.nearest_integer}`, `${independent.independent.status}/${independent.independent.nearest_integer}`],
    ["原始值", fmt(row.zero.value, 12), fmt(independent.independent.value, 12)],
    ["最小体隙", fmt(row.zero.min_bulk_gap), fmt(independent.independent.min_bulk_gap)],
    ["端点联合判据", String(row.endpoint.zero.joint_pass), String(independent.endpoint_joint_pass)],
  ], [2600, 3400, 3506], 11),
  makeTable(["诊断", "回答的问题", "后续边界"], [
    ["N=400", "r=0.1、seed=0 是否穿越局部端点阈值", "不证明整体局域化或热力学体边对应"],
    ["N=600", "r=0.05、seed=0 的 L50 增长是否持续", "不改写 not_established，不预设恢复"],
  ], [1800, 4300, 3406], 11),
  body("复现：run_scale_diagnostic.py 分批执行两条网格；verify_scale_diagnostic.py 使用原始 expm＋Schur 独立复核。原始数据：scale_diagnostic.json、scale_independent_n400.json、n400_scale.json。"),
];

const document = new Document({
  creator: "TOE-SYLVA",
  title: "Floquet-BdG N=400 阈值边缘诊断",
  description: "N=400 体 winding、端点阈值、覆盖尾长及独立行列式复核。",
  features: { updateFields: true },
  styles: { paragraphStyles: [1, 2].map((level) => ({ id: `TOC${level}`, name: `TOC ${level}`, basedOn: "Normal", next: "Normal", quickFormat: true, run: { font, size: 19, color: palette.dark }, paragraph: { spacing: { after: 70, line: 240 }, indent: { left: (level - 1) * 360 } } })) },
  footnotes: {
    1: { children: [footnote("scale_diagnostic.json and resumable per-theta checkpoints. Main grids remain dθ=0.05/0.025; nested RNG preserves the first 320 values exactly.")] },
    2: { children: [footnote("n400_scale.json and floquet-bdg-localization-scale/localization_scale.json. Direct two-end coverage, fixed-width masses and envelope R² are kept separate.")] },
    3: { children: [footnote("scale_independent_n400.json. Original expm+Schur determinant phase with dθ=0.1; independent integer and chiral checks agree with the production result.")] },
  },
  sections: [{
    properties: { page: { margin: { top: 900, bottom: 900, left: 1000, right: 1000 } } },
    headers: { default: new Header({ children: [para(run("TOE-SYLVA · Floquet-BdG · N=400 阈值诊断", { size: 17, color: palette.primary }), { alignment: AlignmentType.CENTER })] }) },
    footers: { default: new Footer({ children: [para(new TextRun({ children: [PageNumber.CURRENT], font, size: 17 }), { alignment: AlignmentType.CENTER })] }) },
    children,
  }],
});
fs.writeFileSync(outputPath, await Packer.toBuffer(document));
