import fs from "node:fs";
import path from "node:path";
import {
  AlignmentType, Document, Footer, FootnoteReferenceRun, Header, HeadingLevel,
  ImageRun, ImportedXmlComponent, Math as MathEquation, MathRun, Packer,
  PageBreak, PageNumber, Paragraph, ShadingType, Table, TableCell, TableRow,
  TextRun, WidthType,
} from "docx";

const outputPath = process.argv[2];
if (!outputPath) throw new Error("Usage: node build_multi_seed_report.js /absolute/path/report.docx");
const root = path.dirname(outputPath);
const analysis = JSON.parse(fs.readFileSync(path.join(root, "multi_seed_profile_control.json"), "utf8"));
const independent = JSON.parse(fs.readFileSync(path.join(root, "multi_seed_independent.json"), "utf8"));
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
  width: { size: widths[index], type: WidthType.DXA }, margins: { top: 25, bottom: 25, left: 50, right: 50 },
  shading: header ? { type: ShadingType.CLEAR, fill: palette.fill } : undefined,
});
const makeTable = (headers, rows, widths, size = 11) => new Table({
  width: { size: widths.reduce((a, b) => a + b, 0), type: WidthType.DXA }, columnWidths: widths,
  rows: [new TableRow({ tableHeader: true, cantSplit: true, children: headers.map((text, index) => cell(text, index, widths, true, size)) }), ...rows.map((row) => new TableRow({ cantSplit: true, children: row.map((text, index) => cell(text, index, widths, false, size)) }))],
});
const equation = (text) => para(new MathEquation({ children: [new MathRun(text)] }), { alignment: AlignmentType.CENTER, spacing: { before: 65, after: 80 } });
const footnote = (text) => para(run(text, { size: 15 }), { spacing: { after: 30, line: 190 } });
const fmt = (value, digits = 5) => Number(value).toPrecision(digits).replace(/\.0+$/, "");
const titles = ["一、四组对照方向与反转", "二、逐种子尺寸差与交互项", "三、稳定方向与证据边界"];
const summaryRows = [];
for (const [group, summaries] of Object.entries(analysis.sign_summaries)) {
  for (const metric of ["delta_L50", "delta_edge_weight"]) {
    const row = summaries[metric];
    summaryRows.push([group, metric, `${row.positive}／${row.negative}／${row.zero}`, fmt(row.median), fmt(row.minimum), fmt(row.maximum)]);
  }
}
const sizeInteractionRows = [
  ...analysis.contrasts.size_at_fixed_strength.map((row) => [String(row.seed), String(row.strength), String(row.delta_L50), fmt(row.delta_edge_weight), "尺寸差"]),
  ...analysis.contrasts.interaction.map((row) => [String(row.seed), "0.1−0.05", String(row.delta_L50), fmt(row.delta_edge_weight), "交互项"]),
];
const strengthRows = analysis.contrasts.strength_at_fixed_size.map((row) => [String(row.seed), String(row.n), String(row.delta_L50), fmt(row.delta_edge_weight)]);
const maxError = Math.max(...independent.cases.flatMap((item) => item.pairs.map((pair) => pair.max_profile_absolute_error)));
const children = [
  para(run("Floquet-BdG 多种子稳健性对照", { bold: true, size: 34, color: palette.dark }), { heading: HeadingLevel.TITLE, alignment: AlignmentType.CENTER, spacing: { before: 600, after: 220 } }),
  para(run("强度效应较一致，尺寸效应与交互项反复变号", { bold: true, size: 25, color: palette.primary }), { alignment: AlignmentType.CENTER, spacing: { after: 230 } }),
  para(run("4 个预登记种子 × N=400／600 × r=0.05／0.1", { size: 20, color: palette.light }), { alignment: AlignmentType.CENTER, spacing: { after: 260 } }),
  para(run("2026-11-11　16 个单元全保留，不补算体 winding", { size: 19, color: palette.accent }), { alignment: AlignmentType.CENTER, spacing: { after: 300 } }),
  heading("目录"),
  para(run("以下页码为可见缓存；在 Word/WPS 中更新域可刷新。", { size: 17, italics: true, color: palette.light })),
  toc(titles.map((title, index) => ({ title, level: 1, page: index + 2 }))),
  pageBreak(),

  heading(titles[0]),
  citedBody("方向计数 `+／−／0` 是四个种子的描述，不是置信区间，也不是统计显著性。尺寸端点权重并非全员同号，尺寸效应的符号反转不能普适化。", 1),
  makeTable(["对照", "指标", "+／−／0", "中位数", "最小值", "最大值"], summaryRows, [1800, 1900, 1250, 1600, 1400, 1556], 10),
  para(new ImageRun({ type: "png", data: fs.readFileSync(path.join(root, "multi-seed-control.png")), transformation: { width: 490, height: Math.round(490 * 1289 / 1845) } }), { alignment: AlignmentType.CENTER, keepNext: true }),
  para(run("图 1　四个预登记种子的全部对照方向与反转。", { size: 16, italics: true }), { alignment: AlignmentType.CENTER }),
  pageBreak(),

  heading(titles[1]),
  citedBody("r=0.05 与 r=0.1 的尺寸端点权重差均为 3 正 1 负，L50 均为 2 正 2 负；尺寸效应并不稳定。两种强度下，尺寸差的中心 20% 质量均在 4/4 种子中下降，但这不是衰减指数或热力学标度。", 2),
  equation("IE(s) = ΔE0.1(s) − ΔE0.05(s)"),
  makeTable(["seed", "强度／差分", "ΔL50", "Δ端点权重", "类型"], sizeInteractionRows, [800, 1700, 1900, 2800, 2306], 10),
  body("交互项端点权重为 2 正、2 负，说明 seed=0 的符号反转不能代表其他随机实现。全部原始 L90 和中心 20% 质量差保留在 JSON 中。"),
  pageBreak(),

  heading(titles[2]),
  citedBody("强度升高端点权重在 4/4 种子中增加，N=400 和 N=600 分别成立。L50 在 N=400 的 4/4 种子中缩短，在 N=600 的 3/4 种子中缩短；seed=1 的 N=600 反例为 ΔL50=+1，必须保留。", 3),
  makeTable(["seed", "N", "ΔL50", "Δ端点权重"], strengthRows, [1200, 1800, 2800, 3706], 11),
  body("因此，强度效应是本网格中较稳定的观察方向，尺寸效应则不稳定。后续应针对方向不稳定或反转的单元分析谱隔离与端部不对称，而不是追加种子直到出现想要的结果。"),
  body("不补算体 winding，尤其不把单个种子的局部通过升级为拓扑恢复。未计算 N=640；新的体积分只能使用同尺寸、同强度、同种子的预登记候选。"),
  body(`独立 SciPy 后端与直接 Gram 投影复核了全部 16 个单元、两对候选模，最大剖面绝对误差为 ${maxError.toExponential(3)}。`),
  para(run("证据边界：四种子的 profile 试点；方向计数不是置信区间，不构成统计因果、材料预测或热力学极限证明。", { size: 18, color: palette.accent })),
];

const document = new Document({
  creator: "TOE-SYLVA",
  title: "Floquet-BdG 多种子稳健性对照",
  description: "四个预登记种子下尺寸与无序强度 profile 对照的稳定性。",
  features: { updateFields: true },
  styles: { paragraphStyles: [1, 2].map((level) => ({ id: `TOC${level}`, name: `TOC ${level}`, basedOn: "Normal", next: "Normal", quickFormat: true, run: { font, size: 19, color: palette.dark }, paragraph: { spacing: { after: 70, line: 240 }, indent: { left: (level - 1) * 360 } } })) },
  footnotes: {
    1: { children: [footnote("multi_seed_protocol.json and multi_seed_profile_control.json. All sixteen preregistered cells are retained; no post-hoc seed or threshold selection.")] },
    2: { children: [footnote("The interaction is evaluated for each seed before sign counting. The two-positive/two-negative result is descriptive only.")] },
    3: { children: [footnote("multi_seed_independent.json. SciPy eig and direct Gram projectors reproduce all sixteen cells and both candidate pairs; no new winding integral is inferred.")] },
  },
  sections: [{
    properties: { page: { margin: { top: 900, bottom: 900, left: 1000, right: 1000 } } },
    headers: { default: new Header({ children: [para(run("TOE-SYLVA · Floquet-BdG · 多种子稳健性对照", { size: 17, color: palette.primary }), { alignment: AlignmentType.CENTER })] }) },
    footers: { default: new Footer({ children: [para(new TextRun({ children: [PageNumber.CURRENT], font, size: 17 }), { alignment: AlignmentType.CENTER })] }) },
    children,
  }],
});
fs.writeFileSync(outputPath, await Packer.toBuffer(document));
