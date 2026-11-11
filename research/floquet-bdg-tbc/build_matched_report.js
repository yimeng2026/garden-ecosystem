import fs from "node:fs";
import path from "node:path";
import {
  AlignmentType, Document, Footer, FootnoteReferenceRun, Header, HeadingLevel,
  ImageRun, ImportedXmlComponent, Math as MathEquation, MathRun, Packer,
  PageBreak, PageNumber, Paragraph, ShadingType, Table, TableCell, TableRow,
  TextRun, WidthType,
} from "docx";

const outputPath = process.argv[2];
if (!outputPath) throw new Error("Usage: node build_matched_report.js /absolute/path/report.docx");
const root = path.dirname(outputPath);
const analysis = JSON.parse(fs.readFileSync(path.join(root, "matched_profile_control.json"), "utf8"));
const independent = JSON.parse(fs.readFileSync(path.join(root, "matched_profile_independent.json"), "utf8"));
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
const cell = (text, index, widths, header, size = 12) => new TableCell({
  children: [para(run(text, { size, bold: header }), { spacing: { after: 0, line: 190 } })],
  width: { size: widths[index], type: WidthType.DXA }, margins: { top: 35, bottom: 35, left: 60, right: 60 },
  shading: header ? { type: ShadingType.CLEAR, fill: palette.fill } : undefined,
});
const makeTable = (headers, rows, widths, size = 12) => new Table({
  width: { size: widths.reduce((a, b) => a + b, 0), type: WidthType.DXA }, columnWidths: widths,
  rows: [new TableRow({ tableHeader: true, cantSplit: true, children: headers.map((text, index) => cell(text, index, widths, true, size)) }), ...rows.map((row) => new TableRow({ cantSplit: true, children: row.map((text, index) => cell(text, index, widths, false, size)) }))],
});
const equation = (text) => para(new MathEquation({ children: [new MathRun(text)] }), { alignment: AlignmentType.CENTER, spacing: { before: 65, after: 80 } });
const footnote = (text) => para(run(text, { size: 15 }), { spacing: { after: 30, line: 190 } });
const fmt = (value, digits = 6) => Number(value).toPrecision(digits).replace(/\.0+$/, "");
const titles = ["一、四格实测与固定强度对照", "二、固定尺寸强度与交互项", "三、新候选与预登记下一步"];
const caseRows = analysis.cases.map((item) => {
  const pair = item.pairs[0];
  return [String(item.n), String(item.strength), fmt(pair.edge_weight), String(pair.L50), String(pair.L90), String(pair.diagnostic_joint_pass)];
});
const sizeRows = analysis.contrasts.size_at_fixed_strength.map((row) => [String(row.strength), String(row.delta_L50), String(row.delta_L90), fmt(row.delta_edge_weight), fmt(row.delta_center20_mass)]);
const strengthRows = analysis.contrasts.strength_at_fixed_size.map((row) => [String(row.n), String(row.delta_L50), String(row.delta_L90), fmt(row.delta_edge_weight), fmt(row.delta_center20_mass)]);
const secondRows = analysis.cases.map((item) => {
  const pair = item.pairs[1];
  return [String(item.n), String(item.strength), fmt(pair.edge_weight), String(pair.L50), fmt(pair.max_separation_ratio)];
});
const maxError = Math.max(...independent.cases.flatMap((item) => item.pairs.map((pair) => pair.max_profile_absolute_error)));
const children = [
  para(run("Floquet-BdG 同强度 2×2 尺寸对照", { bold: true, size: 34, color: palette.dark }), { heading: HeadingLevel.TITLE, alignment: AlignmentType.CENTER, spacing: { before: 600, after: 220 } }),
  para(run("尺寸效应随强度变号；新 profile 通过不等于体 winding 已验证", { bold: true, size: 24, color: palette.primary }), { alignment: AlignmentType.CENTER, spacing: { after: 230 } }),
  para(run("N=400／600 × r=0.05／0.1 · seed=0 · 嵌套随机流", { size: 20, color: palette.light }), { alignment: AlignmentType.CENTER, spacing: { after: 260 } }),
  para(run("2026-11-11　新案例只做 profile，未计算 N=640", { size: 19, color: palette.accent }), { alignment: AlignmentType.CENTER, spacing: { after: 300 } }),
  heading("目录"),
  para(run("以下页码为可见缓存；在 Word/WPS 中更新域可刷新。", { size: 17, italics: true, color: palette.light })),
  toc(titles.map((title, index) => ({ title, level: 1, page: index + 2 }))),
  pageBreak(),

  heading(titles[0]),
  citedBody("2×2 设计在相同无序强度和同一嵌套随机流下比较尺寸，避免直接把此前不同强度案例相减。四格均保留最近对与次近对，表中先列最近对。", 1),
  makeTable(["N", "r", "端点权重", "L50", "L90", "最近对诊断"], caseRows, [700, 800, 2100, 1300, 1300, 3306], 11),
  equation("ΔE(r) = E600(r) − E400(r)"),
  makeTable(["r", "ΔL50", "ΔL90", "Δ端点权重", "Δ中心20%质量"], sizeRows, [900, 1700, 1700, 2500, 2706], 11),
  para(new ImageRun({ type: "png", data: fs.readFileSync(path.join(root, "matched-profile-control.png")), transformation: { width: 490, height: Math.round(490 * 1289 / 1853) } }), { alignment: AlignmentType.CENTER, keepNext: true }),
  para(run("图 1　四格最近对与次近对的两端累积覆盖。", { size: 16, italics: true }), { alignment: AlignmentType.CENTER }),
  pageBreak(),

  heading(titles[1]),
  citedBody("在 N=400 和 N=600 上，强度从 0.05 增至 0.1 都伴随 L50 缩短，且强度升高伴随端点权重增加。该现象只描述当前有限模型和两个强度点，不能外推为无序越强越局域的普遍结论。", 2),
  makeTable(["N", "ΔL50", "ΔL90", "Δ端点权重", "Δ中心20%质量"], strengthRows, [900, 1700, 1700, 2500, 2706], 11),
  equation("IE = ΔE(0.1) − ΔE(0.05) = 0.138435"),
  body("r=0.05 时，N=600 相对 N=400 的 L50 增加 34、端点权重下降约 0.065；r=0.1 时，L50 增加 13、端点权重上升约 0.073。尺寸效应在两种强度下方向不同，端点权重的符号反转仅是 seed=0 的实测描述，不是普遍尺寸律。"),
  body("描述性交互项用于判断尺寸效应是否随强度改变方向或幅度。它不是统计显著性、独立重复或因果证明。"),
  makeTable(["N", "r", "次近对端点权重", "次近对 L50", "最大分离比"], secondRows, [700, 800, 3000, 2200, 2806], 11),
  para(run("次近对只作机制诊断，不回溯修改任何端点或体 winding 结论。", { size: 18, color: palette.accent })),
  pageBreak(),

  heading(titles[2]),
  citedBody("N=600、r=0.1 的新 profile 判据通过，端点权重为 0.657705，L50=37；但不等于体 winding 已验证。它只登记为同尺寸、同强度、同种子的后续体积分候选，不替换 N=600、r=0.05 的既有未恢复结论。", 3),
  makeTable(["检查项", "本轮结论", "下一步边界"], [
    ["固定强度尺寸对照", "r=0.05 与 r=0.1 的端点权重差方向不同", "增加预登记种子，检验方向是否稳定"],
    ["固定尺寸强度对照", "两种尺寸下端点权重均增加，L50 均缩短", "不外推到其他强度或无序模型"],
    ["N=600、r=0.1", "新 profile 判据通过", "仅在同一参数下复核体积分，不升格"],
    ["N=640", "未计算", "不以扩大尺寸代替机制对照"],
  ], [2300, 4000, 3206], 11),
  body("复现：python research/floquet-bdg-tbc/analyze_matched_profiles.py；独立复核：python research/floquet-bdg-tbc/verify_matched_profiles.py。"),
  body(`独立 SciPy 后端与直接 Gram 投影已复核全部四格；最大剖面绝对误差为 ${maxError.toExponential(3)}。原数组和对比公式见 matched_profile_control.json。`),
  para(run("证据边界：单种子、有限二次模型、profile 诊断；不构成统计因果、材料预测或热力学极限证明。", { size: 18, color: palette.accent })),
];

const document = new Document({
  creator: "TOE-SYLVA",
  title: "Floquet-BdG 同强度 2×2 尺寸对照",
  description: "N=400/600 与 r=0.05/0.1 的固定种子 profile 对照。",
  features: { updateFields: true },
  styles: { paragraphStyles: [1, 2].map((level) => ({ id: `TOC${level}`, name: `TOC ${level}`, basedOn: "Normal", next: "Normal", quickFormat: true, run: { font, size: 19, color: palette.dark }, paragraph: { spacing: { after: 70, line: 240 }, indent: { left: (level - 1) * 360 } } })) },
  footnotes: {
    1: { children: [footnote("matched_profile_control.json. Four preregistered cells preserve the nested random stream and the original two endpoint candidate pairs.")] },
    2: { children: [footnote("Fixed-size contrasts and the difference-in-differences interaction are descriptive seed=0 quantities only. No statistical or causal claim is made.")] },
    3: { children: [footnote("matched_profile_independent.json. SciPy eig and direct Gram projectors reproduce all four cells; no new winding integral is inferred from the profile-only result.")] },
  },
  sections: [{
    properties: { page: { margin: { top: 900, bottom: 900, left: 1000, right: 1000 } } },
    headers: { default: new Header({ children: [para(run("TOE-SYLVA · Floquet-BdG · 同强度尺寸对照", { size: 17, color: palette.primary }), { alignment: AlignmentType.CENTER })] }) },
    footers: { default: new Footer({ children: [para(new TextRun({ children: [PageNumber.CURRENT], font, size: 17 }), { alignment: AlignmentType.CENTER })] }) },
    children,
  }],
});
fs.writeFileSync(outputPath, await Packer.toBuffer(document));
