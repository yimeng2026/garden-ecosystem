import fs from "node:fs";
import path from "node:path";
import {
  AlignmentType, Document, Footer, FootnoteReferenceRun, Header, HeadingLevel,
  ImageRun, ImportedXmlComponent, Math as MathEquation, MathRun, Packer,
  PageBreak, PageNumber, Paragraph, ShadingType, Table, TableCell, TableRow,
  TextRun, WidthType,
} from "docx";

const outputPath = process.argv[2];
if (!outputPath) throw new Error("Usage: node build_n600_report.js /absolute/path/N600.docx");
const root = path.dirname(outputPath);
const data = JSON.parse(fs.readFileSync(path.join(root, "scale_diagnostic.json"), "utf8"));
const independent = JSON.parse(fs.readFileSync(path.join(root, "scale_independent_n600.json"), "utf8"));
const metrics = JSON.parse(fs.readFileSync(path.join(root, "n600_scale.json"), "utf8"));
const old = JSON.parse(fs.readFileSync(path.join(path.dirname(root), "floquet-bdg-localization-scale", "localization_scale.json"), "utf8"));
const oldCase = old.cases.find((caseData) => caseData.strength === 0.05 && caseData.seed === 0);
const row = data.rows.find((item) => item.n === 600);
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
const titles = ["一、N=600 体与端点状态", "二、覆盖尾部是否继续增长", "三、独立复核与后续边界"];
const endpointRows = [
  ["主 W0 原始值", "0.999895392848", fmt(row.zero.value, 12)],
  ["最小 0 体隙", "0.00187302", fmt(row.zero.min_bulk_gap)],
  ["端点权重", "0.344437", fmt(row.endpoint.zero.edge_weight)],
  ["最大分离比", "0.0245131", fmt(Math.max(...row.endpoint.zero.separation_ratios))],
  ["端点联合判据", "False", String(row.endpoint.zero.joint_pass)],
];
const coverageRows = [["L50", "L90", "固定20质量", "中心20%质量", "N·IPR"]];
for (const metric of ["L50", "L90", "mass20", "center20_mass", "n_subspace_ipr"]) {
  coverageRows.push([metric, ...oldCase.rows.map((item) => fmt(item[metric])), fmt(metrics[metric])]);
}
const children = [
  para(run("Floquet-BdG N=600 尾长增长诊断", { bold: true, size: 34, color: palette.dark }), { heading: HeadingLevel.TITLE, alignment: AlignmentType.CENTER, spacing: { before: 600, after: 220 } }),
  para(run("体 W0=1，端点仍未恢复，L50/L90 继续增长", { bold: true, size: 25, color: palette.primary }), { alignment: AlignmentType.CENTER, spacing: { after: 230 } }),
  para(run("主双网格 · 嵌套 RNG · 原始 expm＋Schur 独立复核", { size: 20, color: palette.light }), { alignment: AlignmentType.CENTER, spacing: { after: 260 } }),
  para(run("2026-11-11　N=600 不是自动恢复尺寸", { size: 19, color: palette.accent }), { alignment: AlignmentType.CENTER, spacing: { after: 300 } }),
  heading("目录"),
  para(run("以下页码为可见缓存；在 Word/WPS 中更新域可刷新。", { size: 17, italics: true, color: palette.light })),
  toc(titles.map((title, index) => ({ title, level: 1, page: index + 2 }))),
  pageBreak(),

  heading(titles[0]),
  citedBody("N=600 主双网格与原始独立复核均为 W0=1，但端点联合判据仍为 False。端点权重约 0.370，低于 0.5；分离度本身通过。", 1),
  equation("W0(N=600) = 1,　端点权重 = 0.370468 < 0.5"),
  makeTable(["项目", "N=320", "N=600"], endpointRows, [3000, 3200, 3306], 12),
  para(new ImageRun({ type: "png", data: fs.readFileSync(path.join(root, "n600-result.png")), transformation: { width: 500, height: Math.round(500 * 691 / 1527) } }), { alignment: AlignmentType.CENTER, keepNext: true }),
  para(run("图 1　主积分与独立复核一致，端点仍未恢复。", { size: 16, italics: true }), { alignment: AlignmentType.CENTER }),
  pageBreak(),

  heading(titles[1]),
  citedBody("L50 从 21→31→51→85，L90 从 38→70→115→164，固定 20 格点质量继续下降。N=600 未形成可复核的短尾平台。", 2),
  makeTable(["指标", "N=80", "N=160", "N=320", "N=600"], coverageRows, [1900, 1900, 1900, 1900, 1906], 11),
  para(new ImageRun({ type: "png", data: fs.readFileSync(path.join(root, "n600-coverage.png")), transformation: { width: 490, height: Math.round(490 * 782 / 1592) } }), { alignment: AlignmentType.CENTER, keepNext: true }),
  para(run("图 2　覆盖尾长继续增长，与 N=400 的局部阈值穿越不同。", { size: 16, italics: true }), { alignment: AlignmentType.CENTER }),
  pageBreak(),

  heading(titles[2]),
  citedBody("原始 expm＋Schur 行列式复核使用 dθ=0.25，得到 W0=1，与主双网格整数一致；最大半周期对称误差约 1.35×10⁻¹³。", 3),
  makeTable(["检查项", "主结果", "独立结果"], [
    ["winding", `${row.zero.status}/${row.zero.nearest_integer}`, `${independent.independent.status}/${independent.independent.nearest_integer}`],
    ["原始值", fmt(row.zero.value, 12), fmt(independent.independent.value, 12)],
    ["最小体隙", fmt(row.zero.min_bulk_gap), fmt(independent.independent.min_bulk_gap)],
    ["端点联合判据", String(row.endpoint.zero.joint_pass), String(independent.endpoint_joint_pass)],
  ], [2600, 3400, 3506], 11),
  makeTable(["案例", "已获得的证据", "不得外推"], [
    ["N=400", "r=0.1、seed=0 的局部阈值穿越", "不能代替 N.05s0 的尾长诊断"],
    ["N=600", "L50/L90 继续增长，端点未恢复", "不自动扩大为 N=640 或恢复证明"],
  ], [1800, 4300, 3406], 11),
  body("复现：run_scale_diagnostic.py 分批执行两条网格；verify_scale_diagnostic.py --n 600 --step 0.25 使用原始 expm＋Schur。原始数据：scale_diagnostic.json、scale_independent_n600.json、n600_scale.json。"),
];

const document = new Document({
  creator: "TOE-SYLVA",
  title: "Floquet-BdG N=600 尾长增长诊断",
  description: "N=600 体 winding、未恢复端点、覆盖尾长与独立行列式复核。",
  features: { updateFields: true },
  styles: { paragraphStyles: [1, 2].map((level) => ({ id: `TOC${level}`, name: `TOC ${level}`, basedOn: "Normal", next: "Normal", quickFormat: true, run: { font, size: 19, color: palette.dark }, paragraph: { spacing: { after: 70, line: 240 }, indent: { left: (level - 1) * 360 } } })) },
  footnotes: {
    1: { children: [footnote("scale_diagnostic.json and resumable per-theta checkpoints. N=600 keeps nested RNG and both main grids; endpoint joint status remains false.")] },
    2: { children: [footnote("n600_scale.json and floquet-bdg-localization-scale/localization_scale.json. Direct two-end coverage and fixed-width masses continue to grow; no short-tail plateau is inferred.")] },
    3: { children: [footnote("scale_independent_n600.json. Original expm+Schur determinant phase with dθ=0.25; independent integer and chiral checks agree with the production result.")] },
  },
  sections: [{
    properties: { page: { margin: { top: 900, bottom: 900, left: 1000, right: 1000 } } },
    headers: { default: new Header({ children: [para(run("TOE-SYLVA · Floquet-BdG · N=600 尾长诊断", { size: 17, color: palette.primary }), { alignment: AlignmentType.CENTER })] }) },
    footers: { default: new Footer({ children: [para(new TextRun({ children: [PageNumber.CURRENT], font, size: 17 }), { alignment: AlignmentType.CENTER })] }) },
    children,
  }],
});
fs.writeFileSync(outputPath, await Packer.toBuffer(document));
