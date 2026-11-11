import fs from "node:fs";
import path from "node:path";
import {
  AlignmentType, Document, Footer, FootnoteReferenceRun, Header, HeadingLevel,
  ImageRun, ImportedXmlComponent, Math as MathEquation, MathRun, Packer,
  PageBreak, PageNumber, Paragraph, ShadingType, Table, TableCell, TableRow,
  TextRun, WidthType,
} from "docx";

const outputPath = process.argv[2];
if (!outputPath) throw new Error("Usage: node build_path_refinement_report.js /absolute/path/report.docx");
const root = path.dirname(outputPath);
const analysis = JSON.parse(fs.readFileSync(path.join(root, "path_refinement_analysis.json"), "utf8"));
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
const equation = (text) => para(new MathEquation({ children: [new MathRun(text)] }), { alignment: AlignmentType.CENTER, spacing: { before: 55, after: 70 } });
const footnote = (text) => para(run(text, { size: 15 }), { spacing: { after: 30, line: 190 } });
const fmt = (value) => Number(value).toPrecision(5).replace(/\.0+$/, "");
const pointTable = (region) => makeTable(["r", "最近对中心", "次近对中心", "中心间隔"], region.points.map((point) => [String(point.strength), fmt(point.pairs[0].center), fmt(point.pairs[1].center), fmt(point.center_separation)]), [1200, 2900, 2900, 2906], 9);
const linkTable = (region) => makeTable(["从 r", "到 r", "同谱秩得分", "交换得分", "主导分配"], region.links.map((link) => [String(link.from), String(link.to), fmt(link.diagonal_score), fmt(link.swapped_score), link.dominant_assignment]), [1100, 1100, 2200, 2200, 3306], 9);
const titles = ["一、两个邻域的细化点", "二、细化图与分配得分", "三、八条细分链接与解释边界"];
const children = [
  para(run("Floquet-BdG 参数路径定向细化", { bold: true, size: 34, color: palette.dark }), { heading: HeadingLevel.TITLE, alignment: AlignmentType.CENTER, spacing: { before: 600, after: 220 } }),
  para(run("粗步长跳变不等于交叉，离散最小值不等于连续极值", { bold: true, size: 25, color: palette.primary }), { alignment: AlignmentType.CENTER, spacing: { after: 230 } }),
  para(run("N=400 · seed=6 · 两个邻域 · 10个细化点", { size: 20, color: palette.light }), { alignment: AlignmentType.CENTER, spacing: { after: 260 } }),
  para(run("2026-11-11　不新增类别，不补算体 winding，未计算 N=640", { size: 19, color: palette.accent }), { alignment: AlignmentType.CENTER, spacing: { after: 300 } }),
  heading("目录"),
  para(run("以下页码为可见缓存；在 Word/WPS 中更新域可刷新。", { size: 17, italics: true, color: palette.light })),
  toc(titles.map((title, index) => ({ title, level: 1, page: index + 2 }))),
  pageBreak(),

  heading(titles[0]),
  citedBody("只细化粗路径识别的最大变化链接与最小间隔邻域。新增唯一点共5个；五个粗网格旧点全部复核，中心、距离、分离比、端点权重和诊断标志均一致。", 1),
  equation("c_p = (d_(2p) + d_(2p+1)) / 2,  Δc = |c_1 − c_0|"),
  heading("最大变化链接：0.050000–0.052500", 2),
  pointTable(analysis.regions[0]),
  heading("最小间隔邻域：0.040000–0.045000", 2),
  pointTable(analysis.regions[1]),
  para(run(`粗点最大数值误差 ${analysis.max_reference_error.toExponential(1)}。`, { size: 17, color: palette.light })),
  pageBreak(),

  heading(titles[1]),
  citedBody("相同 N 的二维子空间直接 QR 后比较。细步长提高分辨率，但不把有限点外推为连续路径不变性。", 2),
  equation("D = (O_00 + O_11) / 2,  S = (O_01 + O_10) / 2"),
  para(new ImageRun({ type: "png", data: fs.readFileSync(path.join(root, "path-refinement.png")), transformation: { width: 500, height: Math.round(500 * 1366 / 2079) } }), { alignment: AlignmentType.CENTER, keepNext: true }),
  para(run("图 1　上排为最大变化链接，下排为最小间隔邻域；左侧为中心间隔，右侧为分配得分。", { size: 16, italics: true }), { alignment: AlignmentType.CENTER }),
  body("8条细分链接全部由同谱秩分配占优。最大变化区同谱秩得分范围为0.97676–0.98489，最小间隔邻域为0.84764–0.90466。细步长提高了同 N 对应的可辨识性。"),
  body(`全部细化点的最小中心间隔为 ${fmt(analysis.summary.min_center_separation)}，位于新增点 r=${analysis.summary.min_center_separation_strength}；最大相邻间隔变化降为 ${fmt(analysis.summary.max_adjacent_center_separation_change)}。`),
  pageBreak(),

  heading(titles[2]),
  heading("最大变化链接", 2),
  linkTable(analysis.regions[0]),
  heading("最小间隔邻域", 2),
  linkTable(analysis.regions[1]),
  body("粗网格上的较大跳变在细化后分解为较小变化，且没有交换占优，因此不能把粗步长跳变直接解释为交叉。最小间隔位置从0.0425移动到0.04125，只说明当前离散网格的实测最小值位置。"),
  citedBody("若出现交换分配链接，它只是进一步细化候选；若没有，也不构成避免交叉证明。原类别和此前计数未改变。", 3),
  body("本轮没有证明连续路径、谱交叉、避免交叉、真实态追踪、次近对拓扑性或体 winding。复现：python research/floquet-bdg-tbc/analyze_path_refinement.py。"),
  para(run("证据边界：两个已识别邻域的定向细化；10个细化点、8条链接和五个粗点复核。", { size: 18, color: palette.accent })),
];

const document = new Document({
  creator: "TOE-SYLVA",
  title: "Floquet-BdG 参数路径定向细化",
  description: "最大变化链接与最小间隔邻域的同N细化诊断。",
  features: { updateFields: true },
  styles: { paragraphStyles: [1, 2].map((level) => ({ id: `TOC${level}`, name: `TOC ${level}`, basedOn: "Normal", next: "Normal", quickFormat: true, run: { font, size: 19, color: palette.dark }, paragraph: { spacing: { after: 70, line: 240 }, indent: { left: (level - 1) * 360 } } })) },
  footnotes: {
    1: { children: [footnote("path_refinement_protocol.json. Only the two regions identified by the coarse path are refined; the random stream is unchanged.")] },
    2: { children: [footnote("path_refinement_analysis.json. All five coarse reference points are reproduced exactly; refined links use the same QR/SVD metric.")] },
    3: { children: [footnote("All eight refined links favor diagonal assignment. Discrete refinement does not prove a continuous path or avoided crossing.")] },
  },
  sections: [{
    properties: { page: { margin: { top: 900, bottom: 900, left: 1000, right: 1000 } } },
    headers: { default: new Header({ children: [para(run("TOE-SYLVA · Floquet-BdG · 参数路径定向细化", { size: 17, color: palette.primary }), { alignment: AlignmentType.CENTER })] }) },
    footers: { default: new Footer({ children: [para(new TextRun({ children: [PageNumber.CURRENT], font, size: 17 }), { alignment: AlignmentType.CENTER })] }) },
    children,
  }],
});
fs.writeFileSync(outputPath, await Packer.toBuffer(document));
