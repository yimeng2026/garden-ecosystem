import fs from "node:fs";
import path from "node:path";
import {
  AlignmentType, Document, Footer, FootnoteReferenceRun, Header, HeadingLevel,
  ImageRun, ImportedXmlComponent, Math as MathEquation, MathRun, Packer,
  PageBreak, PageNumber, Paragraph, ShadingType, Table, TableCell, TableRow,
  TextRun, WidthType,
} from "docx";

const outputPath = process.argv[2];
if (!outputPath) throw new Error("Usage: node build_finite_size_report.js /absolute/path/FINITE_SIZE.docx");
const root = path.dirname(outputPath);
const finite = JSON.parse(fs.readFileSync(path.join(root, "finite_size_zero.json"), "utf8"));
const independent = JSON.parse(fs.readFileSync(path.join(root, "finite_size_independent.json"), "utf8"));
const n80 = JSON.parse(fs.readFileSync(path.join(root, "disorder_results.json"), "utf8"));
const old = JSON.parse(fs.readFileSync(path.join(path.dirname(root), "floquet-bdg-disorder", "results.json"), "utf8"));
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
const oldRow = (n, strength, seed) => old.realizations.find((row) => row.n === n && row.strength === strength && row.seed === seed);
const n80Row = (strength, seed) => n80.realizations.find((row) => row.strength === strength && row.seed === seed && row.kind === "disorder");
const endpointRow = (n, strength, seed) => n === 80 ? n80Row(strength, seed) : oldRow(n, strength, seed);
const trend = (strength, n) => {
  const rows = [0, 1, 2, 3].map((seed) => endpointRow(n, strength, seed));
  const endpoint = (row) => n === 80 ? row.endpoint.zero : row.zero;
  return [
    String(strength), String(n), `${rows.filter((row) => endpoint(row).joint_pass).length}/4`,
    fmt(rows.map((row) => endpoint(row).edge_weight).sort((a, b) => a - b).slice(1, 3).reduce((a, b) => a + b, 0) / 2),
    fmt(rows.map((row) => Math.max(...endpoint(row).separation_ratios)).sort((a, b) => a - b).slice(1, 3).reduce((a, b) => a + b, 0) / 2),
  ];
};
const titles = ["一、N=160 定向 0 隙算例", "二、N=80／160／320 端点趋势", "三、独立复核与解释边界"];
const caseRows = finite.rows.map((row) => [
  String(row.strength), row.kind === "uniform_mean" ? "—" : String(row.seed), row.kind === "uniform_mean" ? "均匀均值" : "无序",
  fmt(row.zero.value, 12), String(row.zero.nearest_integer), fmt(row.zero.min_bulk_gap), String(row.endpoint.zero.joint_pass),
]);
const trendRows = [0.05, 0.1, 0.2].flatMap((strength) => [80, 160, 320].map((n) => trend(strength, n)));
const seedRows = [0.05, 0.1].flatMap((strength) => [0, 1, 2, 3].map((seed) => {
  const a = n80Row(strength, seed).zero;
  const b = finite.rows.find((row) => row.kind === "disorder" && row.strength === strength && row.seed === seed).zero;
  const c = oldRow(320, strength, seed).zero;
  return [String(strength), String(seed), `${a.status}/${a.nearest_integer ?? "—"}`, String(b.nearest_integer), String(c.joint_pass), fmt(c.edge_weight)];
}));
const independentRows = independent.checks.map((row) => [
  String(row.strength), String(row.seed), row.kind === "disorder" ? "无序" : "均值",
  `${row.production_status}/${row.production_nearest_integer ?? "—"}`,
  `${row.independent.status}/${row.independent.nearest_integer ?? "—"}`,
]);
const children = [
  para(run("Floquet-BdG TBC 有限尺寸对照", { bold: true, size: 34, color: palette.dark }), { heading: HeadingLevel.TITLE, alignment: AlignmentType.CENTER, spacing: { before: 600, after: 220 } }),
  para(run("N=160 的 0 隙体 winding 与端点候选", { bold: true, size: 26, color: palette.primary }), { alignment: AlignmentType.CENTER, spacing: { after: 230 } }),
  para(run("11 个定向算例 · 7 项独立复核 · N=80／160／320 端点趋势", { size: 20, color: palette.light }), { alignment: AlignmentType.CENTER, spacing: { after: 260 } }),
  para(run("2026-11-11　N=320 TBC winding 尚未计算", { size: 19, color: palette.accent }), { alignment: AlignmentType.CENTER, spacing: { after: 300 } }),
  heading("目录"),
  para(run("以下页码为可见缓存；在 Word/WPS 中更新域可刷新。", { size: 17, italics: true, color: palette.light })),
  toc(titles.map((title, index) => ({ title, level: 1, page: index + 2 }))),
  pageBreak(),

  heading(titles[0]),
  citedBody("三种均匀控制与两种无序强度各 4 个固定 seed 组成 11 个 N=160 的 0 隙算例。K 矩阵参数为 rβ，半 kick 角为 rβ，完整对称旋转角为 2rβ。", 1),
  equation("W0(N=160) = 1　（11/11 个定向主积分结果有效）"),
  makeTable(["r", "seed／控制", "类型", "W0 原始值", "整数", "最小体隙", "端点通过"], caseRows, [550, 1100, 1100, 2600, 600, 1900, 1656], 10),
  body("N=80 时 r=0.05、seed=2/3 的主积分未收敛，在 N=160 转为有效 1；该变化保留原始记录，不回写 N=80 状态。"),
  para(new ImageRun({ type: "png", data: fs.readFileSync(path.join(root, "finite-size-winding.png")), transformation: { width: 500, height: Math.round(500 * 963 / 1637) } }), { alignment: AlignmentType.CENTER, keepNext: true }),
  para(run("图 1　N=160 定向 winding 与最小体隙；菱形为独立复核。", { size: 16, italics: true }), { alignment: AlignmentType.CENTER }),
  pageBreak(),

  heading(titles[1]),
  citedBody("端点通过率、端点权重和分离度来自同一随机序列的开链观测。N=160 新旧端点记录已逐行核对一致；N=320 只引用端点数据，没有反推 TBC winding。", 2),
  makeTable(["r", "N", "0 模通过/4", "端点权重中位数", "分离度中位数"], trendRows, [700, 800, 2100, 3200, 2706], 11),
  para(new ImageRun({ type: "png", data: fs.readFileSync(path.join(root, "finite-size-endpoints.png")), transformation: { width: 490, height: Math.round(490 * 831 / 1598) } }), { alignment: AlignmentType.CENTER, keepNext: true }),
  para(run("图 2　端点恢复并不一致；三个测量点不表示连续相界。", { size: 16, italics: true }), { alignment: AlignmentType.CENTER }),
  makeTable(["r", "seed", "N=80 W0 状态/整数", "N=160 W0", "N=320 端点通过", "N=320 端点权重"], seedRows, [550, 550, 2600, 1300, 2200, 2306], 10),
  pageBreak(),

  heading(titles[2]),
  citedBody("独立行列式复核包括三种均匀控制、两种强度的代表无序样本，以及 N=80 的两个原未收敛样本；7 项整数全部一致。", 3),
  makeTable(["r", "seed", "类型", "主状态/整数", "独立状态/整数"], independentRows, [700, 700, 1100, 3500, 3506], 11),
  makeTable(["判断层", "当前证据", "保留边界"], [
    ["N=160 体 winding", "11/11 主结果为有效 W0=1", "不推广到未计算参数或尺寸"],
    ["N=160 无序端点", "r=0.05、0.1 的 0 模均 0/4 通过", "体整数与端点判据分离确实存在"],
    ["N=320 端点", "r=0.05 为 2/4；r=0.1 为 1/4；r=0.2 为 4/4", "N=320 TBC winding 尚未计算"],
    ["后续假说", "有限尺寸交叉可解释部分恢复", "尚不能证明热力学体边对应或排除失配"],
  ], [2100, 4200, 3206], 11),
  body("下一步定向计算 N=320 中端点已恢复的 r=0.05、seed=2/3 与 r=0.1、seed=2；未恢复 seed 继续作为对照，不能只扫描成功样本。"),
  body("复现：python research/floquet-bdg-tbc/run_finite_size.py --merge-only；python research/floquet-bdg-tbc/verify_finite_size.py --merge-only。原始数据：finite_size_zero.json、finite_size_independent.json、disorder_results.json 及 floquet-bdg-disorder/results.json。"),
];

const document = new Document({
  creator: "TOE-SYLVA",
  title: "Floquet-BdG TBC 有限尺寸对照",
  description: "N=160 定向 0 隙、N=80／160／320 端点趋势与独立行列式复核。",
  features: { updateFields: true },
  styles: { paragraphStyles: [1, 2].map((level) => ({ id: `TOC${level}`, name: `TOC ${level}`, basedOn: "Normal", next: "Normal", quickFormat: true, run: { font, size: 19, color: palette.dark }, paragraph: { spacing: { after: 70, line: 240 }, indent: { left: (level - 1) * 360 } } })) },
  footnotes: {
    1: { children: [footnote("finite_size_zero.json. Eleven targeted N=160 zero-gap cases with corrected r*beta K-matrix convention and per-case checkpoints.")] },
    2: { children: [footnote("disorder_results.json and floquet-bdg-disorder/results.json. N=80/160/320 open-chain endpoint observations; N=320 TBC winding is not computed.")] },
    3: { children: [footnote("finite_size_independent.json and its two part files. Seven independent determinant-phase checks; all integer comparisons agree.")] },
  },
  sections: [{
    properties: { page: { margin: { top: 900, bottom: 900, left: 1000, right: 1000 } } },
    headers: { default: new Header({ children: [para(run("TOE-SYLVA · Floquet-BdG · 有限尺寸对照", { size: 17, color: palette.primary }), { alignment: AlignmentType.CENTER })] }) },
    footers: { default: new Footer({ children: [para(new TextRun({ children: [PageNumber.CURRENT], font, size: 17 }), { alignment: AlignmentType.CENTER })] }) },
    children,
  }],
});
fs.writeFileSync(outputPath, await Packer.toBuffer(document));
