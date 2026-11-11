import fs from "node:fs";
import path from "node:path";
import {
  AlignmentType, Document, Footer, FootnoteReferenceRun, Header, HeadingLevel,
  ImageRun, ImportedXmlComponent, Math as MathEquation, MathRun, Packer,
  PageBreak, PageNumber, Paragraph, ShadingType, Table, TableCell, TableRow,
  TextRun, WidthType,
} from "docx";

const outputPath = process.argv[2];
if (!outputPath) throw new Error("Usage: node build_n320_report.js /absolute/path/N320.docx");
const root = path.dirname(outputPath);
const data = JSON.parse(fs.readFileSync(path.join(root, "n320_zero.json"), "utf8"));
const independent = JSON.parse(fs.readFileSync(path.join(root, "n320_independent.json"), "utf8"));
const summary = JSON.parse(fs.readFileSync(path.join(root, "n320_summary.json"), "utf8"));
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
const labels = { recovered: "端点恢复", not_recovered: "端点未恢复", uniform_control: "均匀控制" };
const titles = ["一、N=320 分组结果与 winding", "二、逐例体与端点对照", "三、独立复核与解释边界"];
const groupRows = summary.groups.map((row) => [labels[row.class], String(row.count), String(row.winding_valid), String(row.winding_one), String(row.endpoint_pass), fmt(row.min_gap)]);
const caseRows = data.rows.map((row) => [
  labels[row.endpoint_class], String(row.strength), String(row.seed), fmt(row.zero.value, 12), fmt(row.zero.min_bulk_gap),
  fmt(row.endpoint.zero.edge_weight), fmt(Math.max(...row.endpoint.zero.separation_ratios)), String(row.endpoint.zero.joint_pass),
]);
const independentRows = independent.checks.map((row) => [
  labels[row.case.endpoint_class], String(row.case.strength), String(row.case.seed),
  `${row.production_status}/${row.production_nearest_integer ?? "—"}`,
  `${row.independent.status}/${row.independent.nearest_integer ?? "—"}`, fmt(row.independent.value, 10),
]);
const children = [
  para(run("Floquet-BdG TBC N=320 定向对照", { bold: true, size: 34, color: palette.dark }), { heading: HeadingLevel.TITLE, alignment: AlignmentType.CENTER, spacing: { before: 600, after: 220 } }),
  para(run("恢复、未恢复与均匀控制的 0 隙体 winding", { bold: true, size: 25, color: palette.primary }), { alignment: AlignmentType.CENTER, spacing: { after: 230 } }),
  para(run("7 个定向算例 · 7 项原始 expm＋Schur 独立复核", { size: 20, color: palette.light }), { alignment: AlignmentType.CENTER, spacing: { after: 260 } }),
  para(run("2026-11-11　逐网格检查点；不宣称热力学极限", { size: 19, color: palette.accent }), { alignment: AlignmentType.CENTER, spacing: { after: 300 } }),
  heading("目录"),
  para(run("以下页码为可见缓存；在 Word/WPS 中更新域可刷新。", { size: 17, italics: true, color: palette.light })),
  toc(titles.map((title, index) => ({ title, level: 1, page: index + 2 }))),
  pageBreak(),

  heading(titles[0]),
  citedBody("自由传播采用经逐值验证的 eigh(iK) 加速，Schur 周期化、双网格、体隙和整数判据均不改变。七例主积分均为有效 W0=1。", 1),
  equation("W0(N=320) = 1　（7/7 个定向主积分结果有效）"),
  makeTable(["分组", "算例数", "主 W0 有效数", "W0=1 数", "端点通过数", "最小体隙"], groupRows, [1700, 1200, 1700, 1400, 1600, 1906], 11),
  para(new ImageRun({ type: "png", data: fs.readFileSync(path.join(root, "n320-winding.png")), transformation: { width: 510, height: Math.round(510 * 1010 / 1536) } }), { alignment: AlignmentType.CENTER, keepNext: true }),
  para(run("图 1　七例主积分与独立行列式复核；R 恢复、N 未恢复、U 均匀控制。", { size: 16, italics: true }), { alignment: AlignmentType.CENTER }),
  pageBreak(),

  heading(titles[1]),
  citedBody("三个恢复样本的体 winding 与端点候选一致；两个未恢复样本仍显示 W0=1 与端点权重不足并存。均匀控制的端点与体结果均通过。", 2),
  makeTable(["分组", "r", "seed", "W0 原始值", "最小体隙", "端点权重", "最大分离比", "端点通过"], caseRows, [1150, 500, 550, 2100, 1450, 1300, 1400, 1056], 9),
  para(new ImageRun({ type: "png", data: fs.readFileSync(path.join(root, "n320-endpoints.png")), transformation: { width: 500, height: Math.round(500 * 1010 / 1491) } }), { alignment: AlignmentType.CENTER, keepNext: true }),
  para(run("图 2　端点权重与分离度；两个未恢复样本仅在权重阈值下失败。", { size: 16, italics: true }), { alignment: AlignmentType.CENTER }),
  pageBreak(),

  heading(titles[2]),
  citedBody("全部七项独立行列式复核均使用原始 expm＋Schur 路径，整数与主结果一致。加速后端不是自身唯一验证。", 3),
  makeTable(["分组", "r", "seed", "主状态/整数", "独立状态/整数", "独立原始值"], independentRows, [1250, 550, 600, 2600, 2700, 1806], 10),
  makeTable(["判断层", "当前证据", "保留边界"], [
    ["恢复样本", "3/3 体 W0=1 且端点通过", "支持有限尺寸交叉，但不是普遍定理"],
    ["未恢复样本", "2/2 体 W0=1，端点权重未过 0.5", "体边对应仍未对所有样本闭合"],
    ["均匀控制", "2/2 体与端点均通过", "同一均匀链不是两个独立随机样本"],
    ["后续方向", "先估计 IPR、端点权重和尾部长度", "不直接盲目扫描 N=640"],
  ], [1900, 4200, 3406], 11),
  body("复现：python research/floquet-bdg-tbc/run_n320.py --merge-only；python research/floquet-bdg-tbc/verify_n320.py --merge-only。原始证据：n320_zero.json、n320_independent.json 及逐例独立文件。"),
];

const document = new Document({
  creator: "TOE-SYLVA",
  title: "Floquet-BdG TBC N=320 定向对照",
  description: "七个 N=320 定向 0 隙算例、恢复与未恢复对照及原始独立行列式复核。",
  features: { updateFields: true },
  styles: { paragraphStyles: [1, 2].map((level) => ({ id: `TOC${level}`, name: `TOC ${level}`, basedOn: "Normal", next: "Normal", quickFormat: true, run: { font, size: 19, color: palette.dark }, paragraph: { spacing: { after: 70, line: 240 }, indent: { left: (level - 1) * 360 } } })) },
  footnotes: {
    1: { children: [footnote("n320_zero.json and spectral_benchmark.json. Seven targeted cases; Hermitian free-evolution acceleration is checked against expm while Schur and all convergence criteria remain unchanged.")] },
    2: { children: [footnote("n320_zero.json and existing open-chain endpoint observations. Recovered, non-recovered, and uniform-control classes are kept separate.")] },
    3: { children: [footnote("n320_independent.json and all seven per-case independent files. Original expm+Schur determinant-phase checks agree with every production integer.")] },
  },
  sections: [{
    properties: { page: { margin: { top: 900, bottom: 900, left: 1000, right: 1000 } } },
    headers: { default: new Header({ children: [para(run("TOE-SYLVA · Floquet-BdG · N=320 定向对照", { size: 17, color: palette.primary }), { alignment: AlignmentType.CENTER })] }) },
    footers: { default: new Footer({ children: [para(new TextRun({ children: [PageNumber.CURRENT], font, size: 17 }), { alignment: AlignmentType.CENTER })] }) },
    children,
  }],
});
fs.writeFileSync(outputPath, await Packer.toBuffer(document));
