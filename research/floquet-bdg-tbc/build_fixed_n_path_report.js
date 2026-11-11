import fs from "node:fs";
import path from "node:path";
import {
  AlignmentType, Document, Footer, FootnoteReferenceRun, Header, HeadingLevel,
  ImageRun, ImportedXmlComponent, Math as MathEquation, MathFraction, MathRun,
  MathSubScript, Packer,
  PageBreak, PageNumber, Paragraph, ShadingType, Table, TableCell, TableRow,
  TextRun, WidthType,
} from "docx";

const outputPath = process.argv[2];
if (!outputPath) throw new Error("Usage: node build_fixed_n_path_report.js /absolute/path/report.docx");
const root = path.dirname(outputPath);
const analysis = JSON.parse(fs.readFileSync(path.join(root, "fixed_n_path_analysis.json"), "utf8"));
const font = { ascii: "Times New Roman", hAnsi: "Times New Roman", cs: "Times New Roman", eastAsia: "SimSun" };
const palette = { dark: "293B40", primary: "356A64", accent: "A25B3F", light: "687A7E", fill: "EDF3F1" };
const run = (text, options = {}) => new TextRun({ text: String(text), font, size: 20, ...options });
const para = (children, options = {}) => new Paragraph({ spacing: { after: 100, line: 270 }, ...options, children: Array.isArray(children) ? children : [children] });
const body = (text) => para(run(text), { indent: { firstLine: 400 } });
const citedBody = (text, id) => para([run(text), new FootnoteReferenceRun(id)], { indent: { firstLine: 400 } });
const heading = (text, level = 1) => para(run(text, { bold: true, size: level === 1 ? 29 : 23, color: palette.dark }), { heading: level === 1 ? HeadingLevel.HEADING_1 : HeadingLevel.HEADING_2, spacing: { before: 170, after: 100 }, keepNext: true });
const pageBreak = () => new Paragraph({ children: [new PageBreak()] });
const xmlEscape = (value) => String(value).replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;");
const toc = (entries) => {
  const cached = entries.map(({ title, level, page }) => `<w:p><w:pPr><w:pStyle w:val="TOC${level}"/><w:tabs><w:tab w:val="right" w:leader="dot" w:pos="9000"/></w:tabs><w:ind w:left="${Math.max(0, level - 1) * 360}"/></w:pPr><w:r><w:t>${xmlEscape(title)}</w:t></w:r><w:r><w:tab/></w:r><w:r><w:t>${page}</w:t></w:r></w:p>`).join("");
  return ImportedXmlComponent.fromXmlString(`<w:sdt xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:sdtPr><w:alias w:val="目录"/></w:sdtPr><w:sdtContent><w:p><w:r><w:fldChar w:fldCharType="begin" w:dirty="true"/><w:instrText xml:space="preserve"> TOC \\o &quot;1-2&quot; \\h \\z \\u </w:instrText><w:fldChar w:fldCharType="separate"/></w:r></w:p>${cached}<w:p><w:r><w:fldChar w:fldCharType="end"/></w:r></w:p></w:sdtContent></w:sdt>`).root[0];
};
const cell = (text, index, widths, header, size = 10) => new TableCell({
  children: [para(run(text, { size, bold: header }), { spacing: { after: 0, line: 165 } })],
  width: { size: widths[index], type: WidthType.DXA }, margins: { top: 20, bottom: 20, left: 35, right: 35 },
  shading: header ? { type: ShadingType.CLEAR, fill: palette.fill } : undefined,
});
const makeTable = (headers, rows, widths, size = 10) => new Table({
  width: { size: widths.reduce((a, b) => a + b, 0), type: WidthType.DXA }, columnWidths: widths,
  rows: [new TableRow({ tableHeader: true, cantSplit: true, children: headers.map((text, index) => cell(text, index, widths, true, size)) }), ...rows.map((row) => new TableRow({ cantSplit: true, children: row.map((text, index) => cell(text, index, widths, false, size)) }))],
});
const equation = (children) => para(new MathEquation({ children: Array.isArray(children) ? children : [new MathRun(children)] }), { alignment: AlignmentType.CENTER, spacing: { before: 55, after: 70 } });
const sub = (base, subscript) => new MathSubScript({ children: [new MathRun(base)], subScript: [new MathRun(subscript)] });
const footnote = (text) => para(run(text, { size: 15 }), { spacing: { after: 30, line: 190 } });
const fmt = (value) => Number(value).toPrecision(5).replace(/\.0+$/, "");
const pathRows = analysis.path.map((point) => [
  String(point.strength), fmt(point.pairs[0].center), fmt(point.pairs[1].center), fmt(point.center_separation),
  fmt(point.pairs[0].max_separation_ratio), fmt(point.pairs[1].max_separation_ratio), String(point.pairs[0].diagnostic_joint_pass), String(point.pairs[1].diagnostic_joint_pass),
]);
const pathTable = makeTable(["r", "最近对中心", "次近对中心", "中心间隔", "最近对分离比", "次近对分离比", "最近对诊断", "次近对诊断"], pathRows, [650, 1350, 1350, 1250, 1200, 1200, 950, 1956], 8);
const linkRows = analysis.links.map((link) => [String(link.from), String(link.to), fmt(link.diagonal_score), fmt(link.swapped_score), link.dominant_assignment, fmt(link.center_separation_after - link.center_separation_before)]);
const linkTable = makeTable(["从 r", "到 r", "同谱秩得分", "交换得分", "主导分配", "中心间隔变化"], linkRows, [900, 900, 1800, 1800, 2400, 2106], 9);
const titles = ["一、固定随机流的九个参数点", "二、同N相邻子空间重叠", "三、离散路径能支持什么"];
const children = [
  para(run("Floquet-BdG 固定尺寸参数路径", { bold: true, size: 34, color: palette.dark }), { heading: HeadingLevel.TITLE, alignment: AlignmentType.CENTER, spacing: { before: 600, after: 220 } }),
  para(run("同N对应更强，但离散路径仍非连续证明", { bold: true, size: 25, color: palette.primary }), { alignment: AlignmentType.CENTER, spacing: { after: 230 } }),
  para(run("N=400 · seed=6 · 9个强度点 · 8条相邻链接", { size: 20, color: palette.light }), { alignment: AlignmentType.CENTER, spacing: { after: 260 } }),
  para(run("2026-11-11　不新增类别，不补算体 winding，未计算 N=640", { size: 19, color: palette.accent }), { alignment: AlignmentType.CENTER, spacing: { after: 300 } }),
  heading("目录"),
  para(run("以下页码为可见缓存；在 Word/WPS 中更新域可刷新。", { size: 17, italics: true, color: palette.light })),
  toc(titles.map((title, index) => ({ title, level: 1, page: index + 2 }))),
  pageBreak(),

  heading(titles[0]),
  citedBody("所有强度点使用同一个 beta 随机流，因此变化只来自无序强度。相同 N 的二维子空间直接 QR 后比较，不再需要跨尺寸插值。", 1),
  equation([
    sub("c", "p"), new MathRun(" = "),
    new MathFraction({ numerator: [sub("d", "2p"), new MathRun(" + "), sub("d", "2p+1")], denominator: [new MathRun("2")] }),
    new MathRun(",　Δc = |"), sub("c", "1"), new MathRun(" − "), sub("c", "0"), new MathRun("|"),
  ]),
  para(run("r=0.050 必须复现原冻结剖面、端点权重、谱距离和分离比；10⁻¹⁰ 仅用于复现，不是近简并或交叉阈值。", { size: 18, color: palette.light })),
  pathTable,
  para(run(`参考点最大剖面误差 ${analysis.max_reference_profile_absolute_error.toExponential(1)}，最大谱距离误差 ${analysis.max_reference_distance_absolute_error.toExponential(1)}。`, { size: 17, color: palette.light })),
  pageBreak(),

  heading(titles[1]),
  citedBody("同谱秩与交换分配均由相邻二维子空间的奇异值给出。这里比较同一 N 的子空间，不需要共同嵌入。", 2),
  equation([
    new MathRun("D = "),
    new MathFraction({ numerator: [sub("O", "00"), new MathRun(" + "), sub("O", "11")], denominator: [new MathRun("2")] }),
    new MathRun(",　S = "),
    new MathFraction({ numerator: [sub("O", "01"), new MathRun(" + "), sub("O", "10")], denominator: [new MathRun("2")] }),
  ]),
  para(new ImageRun({ type: "png", data: fs.readFileSync(path.join(root, "fixed-n-path.png")), transformation: { width: 500, height: Math.round(500 * 1366 / 1978) } }), { alignment: AlignmentType.CENTER, keepNext: true }),
  para(run("图 1　谱中心、中心间隔、既有分离比与相邻重叠。虚线为参考点 r=0.050。", { size: 16, italics: true }), { alignment: AlignmentType.CENTER }),
  body(`8条链接全部由同谱秩分配占优，没有交换分配链接。同尺寸相邻重叠范围为 ${fmt(Math.min(...analysis.links.map((row) => row.diagonal_score)))}–${fmt(Math.max(...analysis.links.map((row) => row.diagonal_score)))}。`),
  body(`最小中心间隔为 ${fmt(analysis.summary.min_center_separation)}，出现在 r=${analysis.summary.min_center_separation_strength}；相邻中心间隔最大绝对变化为 ${fmt(analysis.summary.max_adjacent_center_separation_change)}。`),
  pageBreak(),

  heading(titles[2]),
  linkTable,
  body("同 N 的相邻重叠高于此前跨尺寸弱重叠，说明同尺寸的态对应更可辨识；但8个离散链接仍不等于连续态追踪。尤其在最大间隔变化处，同谱秩得分约0.768，交换得分约0.091，没有交换占优。"),
  body(`最近对 profile 联合诊断通过的强度为 ${analysis.summary.pair0_joint_pass_strengths.join("、")}；次近对没有通过点。诊断在 r>0.050 后失效不能被改写为拓扑相变。`),
  citedBody("离散路径上的交换分配链接只能作为细化候选。本网格没有此类链接，但也不能把有限步长外推为连续路径不变性。", 3),
  body("本轮没有证明连续路径、谱交叉、避免交叉、真实态追踪、次近对拓扑性或体 winding。原类别和此前计数未改变。复现：python research/floquet-bdg-tbc/analyze_fixed_n_path.py。"),
  para(run("证据边界：N=400、固定随机流、9个参数点和8条相邻链接的离散诊断。", { size: 18, color: palette.accent })),
];

const document = new Document({
  creator: "TOE-SYLVA",
  title: "Floquet-BdG 固定尺寸参数路径",
  description: "固定随机流下九点路径与同N相邻子空间重叠。",
  features: { updateFields: true },
  styles: { paragraphStyles: [1, 2].map((level) => ({ id: `TOC${level}`, name: `TOC ${level}`, basedOn: "Normal", next: "Normal", quickFormat: true, run: { font, size: 19, color: palette.dark }, paragraph: { spacing: { after: 70, line: 240 }, indent: { left: (level - 1) * 360 } } })) },
  footnotes: {
    1: { children: [footnote("fixed_n_path_protocol.json. The disorder realization is identical at every strength; only r changes.")] },
    2: { children: [footnote("fixed_n_path_analysis.json. Same-N two-dimensional subspaces are compared directly without cross-size embedding.")] },
    3: { children: [footnote("All eight adjacent links favor diagonal assignment. Discrete paths do not prove continuous tracking or an avoided crossing.")] },
  },
  sections: [{
    properties: { page: { margin: { top: 900, bottom: 900, left: 1000, right: 1000 } } },
    headers: { default: new Header({ children: [para(run("TOE-SYLVA · Floquet-BdG · 固定尺寸参数路径", { size: 17, color: palette.primary }), { alignment: AlignmentType.CENTER })] }) },
    footers: { default: new Footer({ children: [para(new TextRun({ children: [PageNumber.CURRENT], font, size: 17 }), { alignment: AlignmentType.CENTER })] }) },
    children,
  }],
});
fs.writeFileSync(outputPath, await Packer.toBuffer(document));
