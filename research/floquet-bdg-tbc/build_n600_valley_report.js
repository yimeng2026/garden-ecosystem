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
if (!outputPath) throw new Error("Usage: node build_n600_valley_report.js /absolute/path/report.docx");
const root = path.dirname(outputPath);
const analysis = JSON.parse(fs.readFileSync(path.join(root, "n600_valley_analysis.json"), "utf8"));
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
const pointTable = makeTable(["r", "N=600中心间隔", "N=400中心间隔", "绝对差"], analysis.points.map((point, index) => [String(point.strength), fmt(point.center_separation), fmt(analysis.n400_points[index].center_separation), fmt(Math.abs(point.center_separation - analysis.n400_points[index].center_separation))]), [1200, 2900, 2900, 2906], 9);
const linkTable = makeTable(["从 r", "到 r", "N=600同谱秩", "N=400同谱秩", "N=600交换", "N=400交换", "主导分配（N=600／N=400）"], analysis.links.map((link, index) => [String(link.from), String(link.to), fmt(link.diagonal_score), fmt(analysis.n400_links[index].diagonal_score), fmt(link.swapped_score), fmt(analysis.n400_links[index].swapped_score), `${link.dominant_assignment}／${analysis.n400_links[index].dominant_assignment}`]), [800, 800, 1500, 1500, 1350, 1350, 2606], 8);
const titles = ["一、谷值区的五个参数点", "二、中心间隔与重叠下降图", "三、八项指标与解释边界"];
const children = [
  para(run("Floquet-BdG N=600 谷值与重叠下降区", { bold: true, size: 34, color: palette.dark }), { heading: HeadingLevel.TITLE, alignment: AlignmentType.CENTER, spacing: { before: 600, after: 220 } }),
  para(run("局部谷值不是谱交叉，低重叠具有步长依赖", { bold: true, size: 25, color: palette.primary }), { alignment: AlignmentType.CENTER, spacing: { after: 230 } }),
  para(run("N=600 · seed=6 · 5个参数点 · 4条同N链接", { size: 20, color: palette.light }), { alignment: AlignmentType.CENTER, spacing: { after: 260 } }),
  para(run("2026-11-11　不新增类别，不补算体 winding，未计算 N=640", { size: 19, color: palette.accent }), { alignment: AlignmentType.CENTER, spacing: { after: 300 } }),
  heading("目录"),
  para(run("以下页码为可见缓存；在 Word/WPS 中更新域可刷新。", { size: 17, italics: true, color: palette.light })),
  toc(titles.map((title, index) => ({ title, level: 1, page: index + 2 }))),
  pageBreak(),

  heading(titles[0]),
  citedBody("新增 r=0.043125 和0.044375，复核0.0425、0.04375、0.045三个旧点。分别记录中心间隔、同谱秩重叠、交换得分和既有 profile 诊断，不把它们混成同一个机制名称。", 1),
  equation([
    sub("c", "p"), new MathRun(" = "),
    new MathFraction({ numerator: [sub("d", "2p"), new MathRun(" + "), sub("d", "2p+1")], denominator: [new MathRun("2")] }),
    new MathRun(",　Δc = |"), sub("c", "1"), new MathRun(" − "), sub("c", "0"), new MathRun("|"),
  ]),
  pointTable,
  heading("相邻链接与尺寸对照", 2),
  linkTable,
  para(run(`三个旧点的最大数值复核误差 ${analysis.max_reference_error.toExponential(1)}。`, { size: 17, color: palette.light })),
  pageBreak(),

  heading(titles[1]),
  citedBody("同 N 的二维子空间直接 QR 后比较。新增点只提高局部分辨率，不把有限步长外推为连续路径不变性。", 2),
  equation([
    new MathRun("D = "),
    new MathFraction({ numerator: [sub("O", "00"), new MathRun(" + "), sub("O", "11")], denominator: [new MathRun("2")] }),
    new MathRun(",　S = "),
    new MathFraction({ numerator: [sub("O", "01"), new MathRun(" + "), sub("O", "10")], denominator: [new MathRun("2")] }),
  ]),
  para(new ImageRun({ type: "png", data: fs.readFileSync(path.join(root, "n600-valley.png")), transformation: { width: 500, height: Math.round(500 * 1366 / 2060) } }), { alignment: AlignmentType.CENTER, keepNext: true }),
  para(run("图 1　中心间隔、同谱秩重叠、交换得分和既有分离比；虚线为此前最小值位置 r=0.04375。", { size: 16, italics: true }), { alignment: AlignmentType.CENTER }),
  body("4条链接全部由同谱秩分配占优，与 N=400 的方向一致。最小中心间隔移动到新增点 r=0.044375，当前值为0.00128955。"),
  body(`最大同谱秩下降为 ${fmt(analysis.summary.max_diagonal_score_drop)}，最大交换得分上升为 ${fmt(analysis.summary.max_swapped_score_increase)}；最大中心间隔变化为 ${fmt(analysis.summary.max_adjacent_center_separation_change)}。`),
  pageBreak(),

  heading(titles[2]),
  makeTable(["指标", "实测值", "解释边界"], [
    ["最小中心间隔", fmt(analysis.summary.min_center_separation), "位于新增点 r=0.044375，不是连续极值证明"],
    ["最大同谱秩下降", fmt(analysis.summary.max_diagonal_score_drop), "位于0.04375→0.044375，不能直接命名交叉"],
    ["最大交换上升", fmt(analysis.summary.max_swapped_score_increase), "同一链接，但交换仍仅约0.0725"],
    ["最低同谱秩得分", fmt(analysis.summary.min_diagonal_score), "仍高于粗网格低值，显示步长依赖"],
    ["最近对诊断", analysis.summary.pair0_joint_pass_strengths.join("、"), "全部5点通过；不构成体 winding 证明"],
    ["次近对诊断", "无", "没有通过点，不命名为拓扑端点"],
  ], [2300, 2700, 4906], 9),
  body("最大同谱秩下降和最大交换上升都位于0.04375→0.044375。该链接同谱秩为0.904956，交换为0.0725257。粗网格末段的更低重叠没有以同样幅度出现，说明低值具有步长依赖。"),
  citedBody("中心间隔回升和重叠下降不是谱交叉证明，也不是尺寸不变性或连续态追踪结论。原类别和此前计数未改变。", 3),
  body("本轮没有证明连续路径、避免交叉、真实态交换、次近对拓扑性或体 winding。复现：python research/floquet-bdg-tbc/analyze_n600_valley.py。"),
  para(run("证据边界：N=600 谷值区的5个参数点和4条同N链接；离散最小值不是连续极值。", { size: 18, color: palette.accent })),
];

const document = new Document({
  creator: "TOE-SYLVA",
  title: "Floquet-BdG N=600 谷值与重叠下降区",
  description: "N=600 谷值、重叠下降及其步长依赖。",
  features: { updateFields: true },
  styles: { paragraphStyles: [1, 2].map((level) => ({ id: `TOC${level}`, name: `TOC ${level}`, basedOn: "Normal", next: "Normal", quickFormat: true, run: { font, size: 19, color: palette.dark }, paragraph: { spacing: { after: 70, line: 240 }, indent: { left: (level - 1) * 360 } } })) },
  footnotes: {
    1: { children: [footnote("n600_valley_protocol.json. Only two new points are inserted; all three previous N=600 points are reproduced exactly.")] },
    2: { children: [footnote("n600_valley_analysis.json. Same-N subspaces are compared directly without cross-size dot products or continuous-path promotion.")] },
    3: { children: [footnote("All four links favor diagonal assignment. The refined overlap drop and center-separation minimum are not evidence of a spectral crossing.")] },
  },
  sections: [{
    properties: { page: { margin: { top: 900, bottom: 900, left: 1000, right: 1000 } } },
    headers: { default: new Header({ children: [para(run("TOE-SYLVA · Floquet-BdG · N=600 谷值与重叠下降区", { size: 17, color: palette.primary }), { alignment: AlignmentType.CENTER })] }) },
    footers: { default: new Footer({ children: [para(new TextRun({ children: [PageNumber.CURRENT], font, size: 17 }), { alignment: AlignmentType.CENTER })] }) },
    children,
  }],
});
fs.writeFileSync(outputPath, await Packer.toBuffer(document));
