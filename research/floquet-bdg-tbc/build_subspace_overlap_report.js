import fs from "node:fs";
import path from "node:path";
import {
  AlignmentType, Document, Footer, FootnoteReferenceRun, Header, HeadingLevel,
  ImageRun, ImportedXmlComponent, Math as MathEquation, MathFraction, MathRun,
  MathSubScript, MathSuperScript, Packer,
  PageBreak, PageNumber, Paragraph, ShadingType, Table, TableCell, TableRow,
  TextRun, WidthType,
} from "docx";

const outputPath = process.argv[2];
if (!outputPath) throw new Error("Usage: node build_subspace_overlap_report.js /absolute/path/report.docx");
const root = path.dirname(outputPath);
const analysis = JSON.parse(fs.readFileSync(path.join(root, "subspace_overlap_analysis.json"), "utf8"));
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
  width: { size: widths[index], type: WidthType.DXA }, margins: { top: 20, bottom: 20, left: 40, right: 40 },
  shading: header ? { type: ShadingType.CLEAR, fill: palette.fill } : undefined,
});
const makeTable = (headers, rows, widths, size = 10) => new Table({
  width: { size: widths.reduce((a, b) => a + b, 0), type: WidthType.DXA }, columnWidths: widths,
  rows: [new TableRow({ tableHeader: true, cantSplit: true, children: headers.map((text, index) => cell(text, index, widths, true, size)) }), ...rows.map((row) => new TableRow({ cantSplit: true, children: row.map((text, index) => cell(text, index, widths, false, size)) }))],
});
const equation = (children) => para(new MathEquation({ children: Array.isArray(children) ? children : [new MathRun(children)] }), { alignment: AlignmentType.CENTER, spacing: { before: 55, after: 70 } });
const sub = (base, subscript) => new MathSubScript({ children: [new MathRun(base)], subScript: [new MathRun(subscript)] });
const subSup = (base, subscript, superScript) => new MathSuperScript({ children: [sub(base, subscript)], superScript: [new MathRun(superScript)] });
const footnote = (text) => para(run(text, { size: 15 }), { spacing: { after: 30, line: 190 } });
const fmt = (value) => Number(value).toPrecision(6).replace(/\.0+$/, "");
const scoreRows = analysis.cases.flatMap((item) => item.grids.map((grid) => [
  `${item.seed}／${item.strength}`, String(grid.m), fmt(grid.diagonal_score), fmt(grid.swapped_score), grid.dominant_assignment,
]));
const scoreTable = makeTable(["seed／r", "M", "同谱秩得分", "交换得分", "数值主导分配"], scoreRows, [1100, 900, 2200, 2200, 3506], 9);
const matrixTable = (item) => {
  const grid = item.grids[item.grids.length - 1];
  const rows = [0, 1].map((i) => [`第${i + 1}对`, ...[0, 1].map((j) => {
    const entry = grid.overlap_matrix[i][j];
    return `O=${fmt(entry.overlap)}；${fmt(entry.principal_angles_deg[0])}°／${fmt(entry.principal_angles_deg[1])}°`;
  })]);
  return makeTable(["N400＼N600", "第1对", "第2对"], rows, [1800, 4053, 4053], 9);
};
const titles = ["一、共同网格与分配得分", "二、完整重叠矩阵的网格表现", "三、主角度、结论与边界"];
const children = [
  para(run("Floquet-BdG 跨尺寸子空间重叠", { bold: true, size: 34, color: palette.dark }), { heading: HeadingLevel.TITLE, alignment: AlignmentType.CENTER, spacing: { before: 600, after: 220 } }),
  para(run("相对谱秩优势不等于高保真态对应", { bold: true, size: 25, color: palette.primary }), { alignment: AlignmentType.CENTER, spacing: { after: 230 } }),
  para(run("两个近 miss · 一个参考 · 三个共同细网格", { size: 20, color: palette.light }), { alignment: AlignmentType.CENTER, spacing: { after: 260 } }),
  para(run("2026-11-11　不新增类别，不补算体 winding，未计算 N=640", { size: 19, color: palette.accent }), { alignment: AlignmentType.CENTER, spacing: { after: 300 } }),
  heading("目录"),
  para(run("以下页码为可见缓存；在 Word/WPS 中更新域可刷新。", { size: 17, italics: true, color: palette.light })),
  toc(titles.map((title, index) => ({ title, level: 1, page: index + 2 }))),
  pageBreak(),

  heading(titles[0]),
  citedBody("不同尺寸本征矢不能直接点积。将复数内部旋量分量从格心 (i+1/2)/N 线性插值到共同 M 网格，再做约化 QR 正交化；M 预先固定为1200、2400、4800。", 1),
  equation([
    new MathRun("Q(N,M) = orth("), sub("I", "M"), new MathRun("("), sub("V", "N"), new MathRun(")),　"),
    sub("O", "ij"), new MathRun(" = "),
    new MathFraction({ numerator: [subSup("s", "1", "2"), new MathRun(" + "), subSup("s", "2", "2")], denominator: [new MathRun("2")] }),
  ]),
  equation([
    new MathRun("{"), sub("s", "1"), new MathRun(", "), sub("s", "2"), new MathRun("} = singular values["),
    subSup("Q(400,M)", "i", "H"), new MathRun(" "), sub("Q(600,M)", "j"), new MathRun("],　"),
    sub("θ", "k"), new MathRun(" = arccos("), sub("s", "k"), new MathRun(")"),
  ]),
  para(run("二维子空间比较消除了单矢量相位和内部旋转任意性。同谱秩与交换分配均保留，不新增数值阈值。", { size: 18, color: palette.light })),
  scoreTable,
  para(run(`重算相同本征对仍复现冻结剖面，最大误差 ${analysis.max_profile_absolute_error.toExponential(3)}，低于 10⁻¹⁰。`, { size: 17, color: palette.light })),
  pageBreak(),

  heading(titles[1]),
  citedBody("对数坐标用于显示不同数量级；标签采用科学计数，避免把弱重叠四舍五入成零。", 2),
  para(new ImageRun({ type: "png", data: fs.readFileSync(path.join(root, "subspace-overlap.png")), transformation: { width: 500, height: Math.round(500 * 1558 / 2071) } }), { alignment: AlignmentType.CENTER, keepNext: true }),
  para(run("图 1　左列为四个跨尺寸子空间重叠，右列为同谱秩与交换分配得分。三个对照在三网格上均由同谱秩分配占优。", { size: 16, italics: true }), { alignment: AlignmentType.CENTER }),
  body(`M=4800 的同谱秩得分依次为 ${fmt(analysis.cases[0].grids[2].diagonal_score)}、${fmt(analysis.cases[1].grids[2].diagonal_score)}、${fmt(analysis.cases[2].grids[2].diagonal_score)}；绝对重叠均很弱。主导分配在三网格间不变，但不构成网格收敛证明。`),
  body("矩阵行固定属于 N=400、列固定属于 N=600；交换 i、j 不会同时交换尺寸，所以矩阵无需对称。"),
  pageBreak(),

  heading(titles[2]),
  ...analysis.cases.flatMap((item) => [heading(`seed=${item.seed}，r=${item.strength}：M=4800`, 2), matrixTable(item)]),
  body("三个对照的同谱秩得分均高于交换得分，因此当前嵌入下没有由交换得分占优支持的排序交换候选。主角度普遍较大，说明这种相对优势不是高保真态对应。"),
  citedBody("若未来出现交换得分更高，也只能先称排序交换候选，不能直接宣称物理态交换。次近对不因此被命名为拓扑端点。", 3),
  body("线性插值只是选定的共同表示，不是连续极限或真实态追踪。局域尖峰、振荡和简并仍可能影响结果；需要替代嵌入与更多对照检验稳健性。"),
  body("本轮没有证明同一物理态、排序交换、体 winding、材料实现或热力学极限。原类别及此前16对照符号计数未改变。复现：python research/floquet-bdg-tbc/analyze_subspace_overlap.py。"),
  para(run("证据边界：六个既有单元的重算验证与共同表示诊断；不新增物理单元，不后验移动阈值。", { size: 18, color: palette.accent })),
];

const document = new Document({
  creator: "TOE-SYLVA",
  title: "Floquet-BdG 跨尺寸子空间重叠",
  description: "共同细网格上的主子空间重叠、主角度与谱秩分配诊断。",
  features: { updateFields: true },
  styles: { paragraphStyles: [1, 2].map((level) => ({ id: `TOC${level}`, name: `TOC ${level}`, basedOn: "Normal", next: "Normal", quickFormat: true, run: { font, size: 19, color: palette.dark }, paragraph: { spacing: { after: 70, line: 240 }, indent: { left: (level - 1) * 360 } } })) },
  footnotes: {
    1: { children: [footnote("subspace_overlap_protocol.json. Linear common-grid embedding and reduced QR are diagnostics, not a continuum limit or physical state tracking.")] },
    2: { children: [footnote("subspace_overlap_analysis.json. Recomputed eigenvectors reproduce all frozen pair profiles within 1e-10.")] },
    3: { children: [footnote("All three cases favor diagonal rank assignment on all three grids, but absolute overlaps are weak and no rank exchange is proven.")] },
  },
  sections: [{
    properties: { page: { margin: { top: 900, bottom: 900, left: 1000, right: 1000 } } },
    headers: { default: new Header({ children: [para(run("TOE-SYLVA · Floquet-BdG · 跨尺寸子空间重叠", { size: 17, color: palette.primary }), { alignment: AlignmentType.CENTER })] }) },
    footers: { default: new Footer({ children: [para(new TextRun({ children: [PageNumber.CURRENT], font, size: 17 }), { alignment: AlignmentType.CENTER })] }) },
    children,
  }],
});
fs.writeFileSync(outputPath, await Packer.toBuffer(document));
