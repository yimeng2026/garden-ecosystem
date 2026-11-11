import fs from "node:fs";
import path from "node:path";
import {
  AlignmentType, Document, Footer, FootnoteReferenceRun, Header, HeadingLevel,
  ImageRun, ImportedXmlComponent, Math as MathEquation, MathRun, Packer,
  PageBreak, PageNumber, Paragraph, ShadingType, Table, TableCell, TableRow,
  TextRun, WidthType,
} from "docx";

const outputPath = process.argv[2];
if (!outputPath) throw new Error("Usage: node build_report.js /absolute/path/REPORT.docx");
const root = path.dirname(outputPath);
const data = JSON.parse(fs.readFileSync(path.join(root, "localization_scale.json"), "utf8"));
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
const labels = {"0.05,0": "N.05s0", "0.1,0": "N.1s0", "0.05,2": "R.05s2", "0.05,3": "R.05s3", "0.1,2": "R.1s2"};
const caseLabel = (caseData) => labels[`${caseData.strength},${caseData.seed}`] || `r${caseData.strength}s${caseData.seed}`;
const titles = ["一、覆盖定义与恢复分类", "二、未恢复样本的尾部证据", "三、已恢复对照与后续诊断"];
const assessmentRows = data.cases.map((caseData) => [
  caseLabel(caseData), caseData.assessment.status,
  caseData.rows.map((row) => row.L50).join("→"), caseData.rows.map((row) => row.L90).join("→"),
  caseData.assessment.next_size ?? "—", caseData.assessment.reason,
]);
const nonRecoveredRows = data.cases.filter((caseData) => caseData.assessment.status !== "measured_recovered").flatMap((caseData) => caseData.rows.map((row) => [
  caseLabel(caseData), String(row.n), String(row.L50), String(row.L90), fmt(row.mass20), fmt(row.center20_mass), fmt(row.n_subspace_ipr), fmt(row.envelope.r_squared),
]));
const recoveredRows = data.cases.filter((caseData) => caseData.assessment.status === "measured_recovered").map((caseData) => {
  const row = caseData.rows[2];
  return [caseLabel(caseData), String(row.L50), String(row.L90), fmt(row.mass20), fmt(row.n_subspace_ipr), fmt(row.envelope.r_squared)];
});
const children = [
  para(run("Floquet-BdG 局域与恢复尺度分析", { bold: true, size: 34, color: palette.dark }), { heading: HeadingLevel.TITLE, alignment: AlignmentType.CENTER, spacing: { before: 600, after: 220 } }),
  para(run("直接两端覆盖 · 固定宽度质量 · IPR · 包络优度", { bold: true, size: 25, color: palette.primary }), { alignment: AlignmentType.CENTER, spacing: { after: 230 } }),
  para(run("15 个 rank-2 子空间 profile · N=80／160／320", { size: 20, color: palette.light }), { alignment: AlignmentType.CENTER, spacing: { after: 260 } }),
  para(run("2026-11-11　N=400 与 N=600 仅为诊断尺寸", { size: 19, color: palette.accent }), { alignment: AlignmentType.CENTER, spacing: { after: 300 } }),
  heading("目录"),
  para(run("以下页码为可见缓存；在 Word/WPS 中更新域可刷新。", { size: 17, italics: true, color: palette.light })),
  toc(titles.map((title, index) => ({ title, level: 1, page: index + 2 }))),
  pageBreak(),

  heading(titles[0]),
  citedBody("原 profile 是基无关 rank-2 子空间分布。覆盖采用直接两端和，平台判据为最近两尺寸 L50 变化 ≤0.25、固定 20 格点质量比 ≥0.8、N=320 分离度 <0.1。", 1),
  equation("Cm = Σj=0…m−1 qj + Σj=N−m…N−1 qj,　Lp = min{m : Cm ≥ p}"),
  body("对 `(q+q[::-1])/2` 求累计会在 N/2 处恒得 0.5，不能作为 localization length。本文已改用直接两端覆盖，不把该中点恒等式误读为延展尺度。"),
  makeTable(["案例", "状态", "L50", "L90", "下一诊断尺寸", "解释"], assessmentRows, [1000, 1900, 1300, 1400, 1200, 2706], 10),
  para(new ImageRun({ type: "png", data: fs.readFileSync(path.join(root, "coverage-scale.png")), transformation: { width: 500, height: Math.round(500 * 822 / 1593) } }), { alignment: AlignmentType.CENTER, keepNext: true }),
  para(run("图 1　直接两端覆盖 L50 与 L90；稀疏点不构成连续相界。", { size: 16, italics: true }), { alignment: AlignmentType.CENTER }),
  pageBreak(),

  heading(titles[1]),
  citedBody("N.05s0 的 L50 持续增长且固定 20 格点端点质量下降，不能给出恢复区间。N.1s0 虽满足机械平台条件，L90 仍显著增长，N=400 只检验局部阈值穿越。", 2),
  makeTable(["案例", "N", "L50", "L90", "固定20质量", "中心20%质量", "N·IPR", "包络 R²"], nonRecoveredRows, [950, 500, 600, 650, 1500, 1600, 1200, 1506], 10),
  para(new ImageRun({ type: "png", data: fs.readFileSync(path.join(root, "scale-diagnostics.png")), transformation: { width: 490, height: Math.round(490 * 1201 / 1611) } }), { alignment: AlignmentType.CENTER, keepNext: true }),
  para(run("图 2　端点质量、N·IPR 与包络拟合优度的联合诊断。", { size: 16, italics: true }), { alignment: AlignmentType.CENTER }),
  pageBreak(),

  heading(titles[2]),
  citedBody("三个已恢复案例保留 measured_recovered，不要求它们同时满足全部平台子条件。包络 R²<0.5 时不使用指数恢复律。", 3),
  makeTable(["案例", "N=320 L50", "N=320 L90", "固定20质量", "N·IPR", "包络 R²"], recoveredRows, [1300, 1400, 1400, 2000, 1400, 2006], 11),
  makeTable(["后续案例", "下一尺寸", "要回答的问题", "不能预先声称"], [
    ["N.1s0", "N=400", "端点权重是否穿越 0.5", "不声称整体局域化或恢复完成"],
    ["N.05s0", "N=600", "L50 增长是否持续", "不给出恢复区间，不默认 N=640"],
  ], [1800, 1400, 3300, 3006], 11),
  body("复现：python research/floquet-bdg-localization-scale/run_verification.py。原始 profile：floquet-bdg-disorder/profiles.npz；分析数据：localization_scale.json、localization_scale.csv。所有后续计算继续使用逐网格检查点。"),
];

const document = new Document({
  creator: "TOE-SYLVA",
  title: "Floquet-BdG 局域与恢复尺度分析",
  description: "直接两端覆盖、固定宽度质量、IPR 与包络优度联合诊断；N=400 与 N=600 仅为诊断尺寸。",
  features: { updateFields: true },
  styles: { paragraphStyles: [1, 2].map((level) => ({ id: `TOC${level}`, name: `TOC ${level}`, basedOn: "Normal", next: "Normal", quickFormat: true, run: { font, size: 19, color: palette.dark }, paragraph: { spacing: { after: 70, line: 240 }, indent: { left: (level - 1) * 360 } } })) },
  footnotes: {
    1: { children: [footnote("floquet-bdg-disorder/profiles.npz and results.json. Fifteen normalized rank-two subspace profiles; N=320 edge weights are independently cross-checked.")] },
    2: { children: [footnote("localization_scale.json and scale_analysis.py. Direct two-end coverage; plateau criteria are mechanical diagnostics, not topological recovery proofs.")] },
    3: { children: [footnote("fit_envelope from floquet-bdg-localization/localization_analysis.py. Envelope parameters and R² are reported; poor fits do not support an exponential recovery law.")] },
  },
  sections: [{
    properties: { page: { margin: { top: 900, bottom: 900, left: 1000, right: 1000 } } },
    headers: { default: new Header({ children: [para(run("TOE-SYLVA · Floquet-BdG · 局域与恢复尺度", { size: 17, color: palette.primary }), { alignment: AlignmentType.CENTER })] }) },
    footers: { default: new Footer({ children: [para(new TextRun({ children: [PageNumber.CURRENT], font, size: 17 }), { alignment: AlignmentType.CENTER })] }) },
    children,
  }],
});
fs.writeFileSync(outputPath, await Packer.toBuffer(document));
