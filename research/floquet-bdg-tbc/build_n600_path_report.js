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
if (!outputPath) throw new Error("Usage: node build_n600_path_report.js /absolute/path/report.docx");
const root = path.dirname(outputPath);
const analysis = JSON.parse(fs.readFileSync(path.join(root, "n600_path_analysis.json"), "utf8"));
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
const pointTable = (region, old) => makeTable(["r", "N=600中心间隔", "N=400中心间隔", "绝对差"], region.points.map((point, index) => [String(point.strength), fmt(point.center_separation), fmt(old.points[index].center_separation), fmt(Math.abs(point.center_separation - old.points[index].center_separation))]), [1200, 2900, 2900, 2906], 9);
const linkTable = (region, old) => makeTable(["从 r", "到 r", "N=600同谱秩", "N=400同谱秩", "N=600交换", "N=400交换", "主导分配（N=600／N=400）"], region.links.map((link, index) => [String(link.from), String(link.to), fmt(link.diagonal_score), fmt(old.links[index].diagonal_score), fmt(link.swapped_score), fmt(old.links[index].swapped_score), `${link.dominant_assignment}／${old.links[index].dominant_assignment}`]), [800, 800, 1500, 1500, 1350, 1350, 2606], 8);
const titles = ["一、两个细化邻域的尺寸对照", "二、N=600 与 N=400 路径图", "三、八条链接与尺寸差异"];
const children = [
  para(run("Floquet-BdG N=600 细化路径复核", { bold: true, size: 34, color: palette.dark }), { heading: HeadingLevel.TITLE, alignment: AlignmentType.CENTER, spacing: { before: 600, after: 220 } }),
  para(run("分配方向一致不等于尺寸不变", { bold: true, size: 25, color: palette.primary }), { alignment: AlignmentType.CENTER, spacing: { after: 230 } }),
  para(run("N=600 · seed=6 · 10个细化点 · 8条同N链接", { size: 20, color: palette.light }), { alignment: AlignmentType.CENTER, spacing: { after: 260 } }),
  para(run("2026-11-11　不新增类别，不补算体 winding，未计算 N=640", { size: 19, color: palette.accent }), { alignment: AlignmentType.CENTER, spacing: { after: 300 } }),
  heading("目录"),
  para(run("以下页码为可见缓存；在 Word/WPS 中更新域可刷新。", { size: 17, italics: true, color: palette.light })),
  toc(titles.map((title, index) => ({ title, level: 1, page: index + 2 }))),
  pageBreak(),

  heading(titles[0]),
  citedBody("复核 N=400 的两个细化邻域；各自比较同 N 子空间，不做跨尺寸本征矢点积。N=600 的 r=0.050 原冻结单元必须复现到10⁻¹⁰。", 1),
  equation([
    sub("c", "p"), new MathRun(" = "),
    new MathFraction({ numerator: [sub("d", "2p"), new MathRun(" + "), sub("d", "2p+1")], denominator: [new MathRun("2")] }),
    new MathRun(",　Δc = |"), sub("c", "1"), new MathRun(" − "), sub("c", "0"), new MathRun("|"),
  ]),
  heading("最大变化链接", 2),
  pointTable(analysis.regions[0], analysis.n400_regions[0]),
  heading("最小间隔邻域", 2),
  pointTable(analysis.regions[1], analysis.n400_regions[1]),
  para(run(`参考点最大数值误差 ${analysis.max_reference_error.toExponential(1)}。新增 N=600 参数点共9个。`, { size: 17, color: palette.light })),
  pageBreak(),

  heading(titles[1]),
  citedBody("两个尺寸各自的同 N 谱指标和重叠得分。分配方向可比较，但不能把指标对照当成连续态追踪或尺寸不变性。", 2),
  equation([
    new MathRun("D = "),
    new MathFraction({ numerator: [sub("O", "00"), new MathRun(" + "), sub("O", "11")], denominator: [new MathRun("2")] }),
    new MathRun(",　S = "),
    new MathFraction({ numerator: [sub("O", "01"), new MathRun(" + "), sub("O", "10")], denominator: [new MathRun("2")] }),
  ]),
  para(new ImageRun({ type: "png", data: fs.readFileSync(path.join(root, "n600-path.png")), transformation: { width: 500, height: Math.round(500 * 1366 / 2053) } }), { alignment: AlignmentType.CENTER, keepNext: true }),
  para(run("图 1　上排为最大变化链接，下排为最小间隔邻域；绿色为 N=600，棕色为 N=400。", { size: 16, italics: true }), { alignment: AlignmentType.CENTER }),
  body(`N=600 的8条链接全部由同谱秩分配占优，与 N=400 的主导分配一致 ${analysis.size_comparison.assignment_agreement_count}/8。最小中心间隔为 ${fmt(analysis.summary.min_center_separation)}，位于 r=${analysis.summary.min_center_separation_strength}，与 N=400 的位置不同。`),
  body(`最大相邻间隔变化为 ${fmt(analysis.summary.max_adjacent_center_separation_change)}，位于 ${analysis.size_comparison.max_change_link.from}→${analysis.size_comparison.max_change_link.to}，不是 N=400 的最大变化链接。`),
  pageBreak(),

  heading(titles[2]),
  heading("最大变化链接", 2),
  linkTable(analysis.regions[0], analysis.n400_regions[0]),
  heading("最小间隔邻域", 2),
  linkTable(analysis.regions[1], analysis.n400_regions[1]),
  body(`同谱秩得分的最大尺寸绝对差为 ${fmt(analysis.size_comparison.max_diagonal_score_absolute_difference)}，中心间隔的最大尺寸绝对差为 ${fmt(analysis.size_comparison.max_center_separation_absolute_difference)}。N=600 在最大变化区的首个链接重叠较低，随后升高；最小间隔区的重叠趋势与 N=400 不同。`),
  body(`N=600 最近对联合诊断通过强度为 ${analysis.summary.pair0_joint_pass_strengths.join("、")}；次近对没有通过点。诊断区间随尺寸改变，不能据此宣称拓扑相变或尺寸不变性。`),
  citedBody("细化提高各尺寸内部的可辨识性，但不构成连续路径、谱交叉、避免交叉、真实态追踪、次近对拓扑性或体 winding 证明。原类别和此前计数未改变。", 3),
  body("复现：python research/floquet-bdg-tbc/analyze_n600_path.py。N=600 的10点8链接、参考误差和 N=400 指标对照保存在 n600_path_analysis.json。"),
  para(run("证据边界：两个尺寸各自的同 N 路径诊断；方向一致不等于尺寸不变。", { size: 18, color: palette.accent })),
];

const document = new Document({
  creator: "TOE-SYLVA",
  title: "Floquet-BdG N=600 细化路径复核",
  description: "N=600 与 N=400 的两个细化邻域和同N子空间比较。",
  features: { updateFields: true },
  styles: { paragraphStyles: [1, 2].map((level) => ({ id: `TOC${level}`, name: `TOC ${level}`, basedOn: "Normal", next: "Normal", quickFormat: true, run: { font, size: 19, color: palette.dark }, paragraph: { spacing: { after: 70, line: 240 }, indent: { left: (level - 1) * 360 } } })) },
  footnotes: {
    1: { children: [footnote("n600_path_protocol.json. The two refined regions are replicated at N=600 without cross-size eigenvector dot products.")] },
    2: { children: [footnote("n600_path_analysis.json. Both sizes use their own same-N QR/SVD metrics; the reference cell reproduces frozen evidence exactly.")] },
    3: { children: [footnote("All eight links favor diagonal assignment at both sizes, but minima, max-change links, overlaps and diagnostic intervals differ.")] },
  },
  sections: [{
    properties: { page: { margin: { top: 900, bottom: 900, left: 1000, right: 1000 } } },
    headers: { default: new Header({ children: [para(run("TOE-SYLVA · Floquet-BdG · N=600 细化路径复核", { size: 17, color: palette.primary }), { alignment: AlignmentType.CENTER })] }) },
    footers: { default: new Footer({ children: [para(new TextRun({ children: [PageNumber.CURRENT], font, size: 17 }), { alignment: AlignmentType.CENTER })] }) },
    children,
  }],
});
fs.writeFileSync(outputPath, await Packer.toBuffer(document));
