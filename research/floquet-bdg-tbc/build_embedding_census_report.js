import fs from "node:fs";
import path from "node:path";
import {
  AlignmentType, Document, Footer, FootnoteReferenceRun, Header, HeadingLevel,
  ImageRun, ImportedXmlComponent, Math as MathEquation, MathRun, Packer,
  PageBreak, PageNumber, Paragraph, ShadingType, Table, TableCell, TableRow,
  TextRun, WidthType,
} from "docx";

const outputPath = process.argv[2];
if (!outputPath) throw new Error("Usage: node build_embedding_census_report.js /absolute/path/report.docx");
const root = path.dirname(outputPath);
const analysis = JSON.parse(fs.readFileSync(path.join(root, "embedding_census_analysis.json"), "utf8"));
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
const rows = analysis.cases.map((item) => {
  const row = item.method_comparisons[2];
  return [String(item.seed), String(item.strength), fmt(row.linear_diagonal_score), fmt(row.cell_average_diagonal_score), fmt(row.linear_swapped_score), fmt(row.cell_average_swapped_score), row.linear_assignment, row.cell_average_assignment];
});
const censusTable = makeTable(["seed", "r", "线性同谱秩", "单元平均同谱秩", "线性交换", "单元平均交换", "线性主导", "单元平均主导"], rows, [550, 550, 1300, 1300, 1250, 1250, 1200, 2506], 8);
const candidate = analysis.cases.find((item) => item.label === "seed_6_r_0p05");
const candidateRows = candidate ? ["linear_point", "cell_average"].map((method) => {
  const grid = candidate.methods[method].grids[2];
  return [method === "linear_point" ? "线性点值" : "单元平均", ...[0, 1].flatMap((i) => [0, 1].map((j) => fmt(grid.overlap_matrix[i][j].overlap)))];
}) : [];
const candidateTable = makeTable(["方法", "O00", "O01", "O10", "O11"], candidateRows, [2200, 1926, 1926, 1926, 1928], 10);
const titles = ["一、16个对照的共同表示审计", "二、全样本图与网格汇总", "三、交换候选与解释边界"];
const children = [
  para(run("Floquet-BdG 全样本共同表示审计", { bold: true, size: 34, color: palette.dark }), { heading: HeadingLevel.TITLE, alignment: AlignmentType.CENTER, spacing: { before: 600, after: 220 } }),
  para(run("从三例方向稳定到全样本中的一个交换候选", { bold: true, size: 25, color: palette.primary }), { alignment: AlignmentType.CENTER, spacing: { after: 230 } }),
  para(run("16个对照 · 两种共同表示 · 96个方法网格", { size: 20, color: palette.light }), { alignment: AlignmentType.CENTER, spacing: { after: 260 } }),
  para(run("2026-11-11　不新增类别，不补算体 winding，未计算 N=640", { size: 19, color: palette.accent }), { alignment: AlignmentType.CENTER, spacing: { after: 300 } }),
  heading("目录"),
  para(run("以下页码为可见缓存；在 Word/WPS 中更新域可刷新。", { size: 17, italics: true, color: palette.light })),
  toc(titles.map((title, index) => ({ title, level: 1, page: index + 2 }))),
  pageBreak(),

  heading(titles[0]),
  citedBody("线性点值和分片常数单元平均沿用前两轮实现。M=1200／2400／4800；最近对与次近对分别形成二维子空间。只重算相同本征对，不改变物理输入。", 1),
  equation("O_ij = (s_1² + s_2²) / 2,  D = (O_00 + O_11) / 2,  S = (O_01 + O_10) / 2"),
  para(run("D 为同谱秩分配得分，S 为交换分配得分；较大者仅构成数值主导分配。下表为 M=4800。", { size: 18, color: palette.light })),
  censusTable,
  para(run(`原剖面最大误差 ${analysis.max_profile_absolute_error.toExponential(3)}；前三例两种方法的最大复现差均为零。`, { size: 17, color: palette.light })),
  pageBreak(),

  heading(titles[1]),
  citedBody("全样本直接计算取代从三例外推。对数坐标显示弱重叠的不同数量级，不表示统计显著性。", 2),
  para(new ImageRun({ type: "png", data: fs.readFileSync(path.join(root, "embedding-census.png")), transformation: { width: 500, height: Math.round(500 * 1326 / 2037) } }), { alignment: AlignmentType.CENTER, keepNext: true }),
  para(run("图 1　上排为方法得分比较，左下为方法差，右下为 M=4800 的线性／单元平均主导分配组合。", { size: 16, italics: true }), { alignment: AlignmentType.CENTER }),
  body(`96个方法网格中，同谱秩占优 ${analysis.summary.diagonal_dominant_count}/96；两种方法主导分配一致 ${analysis.summary.same_assignment_count}/48。全部六个方法网格均为同谱秩的对照为 ${analysis.summary.fully_diagonal_case_count}/16。`),
  body(`M=4800 上，两种方法主导分配一致 ${analysis.summary.finest_same_assignment_count}/16。两种方法均为15例同谱秩、1例交换。最大方法间同谱秩得分差为 ${fmt(analysis.summary.max_absolute_diagonal_score_change)}。`),
  pageBreak(),

  heading(titles[2]),
  body("交换候选只有 seed=6、r=0.05。其线性同谱秩得分约0.00200693、交换约0.00234643；单元平均同谱秩约0.00195621、交换约0.00230312。两种方法在三个网格上均为交换分配占优。"),
  candidateTable,
  body("候选矩阵的最小主角度约为84.74°，绝对重叠仍弱。相对得分优势不构成高保真态对应，更不能直接命名为物理态交换。"),
  citedBody("其余15个对照在两种方法和三个网格上均由同谱秩分配占优。交换候选只登记预定义得分关系，不新增类别，也不把次近对命名为拓扑端点。", 3),
  body("后续应针对该候选检查完整矩阵、排序交换、简并和更多共同表示，而不是选择有利结果。全样本计数不是统计总体推断或显著性检验。"),
  body("本轮没有证明表示不变性、同一物理态、真实态追踪、排序交换、网格收敛或体 winding。原类别及此前响应计数未改变。复现：python research/floquet-bdg-tbc/analyze_embedding_census.py。"),
  para(run("证据边界：32个既有尺寸单元、96个方法网格的描述性审计；交换候选不是态交换证明。", { size: 18, color: palette.accent })),
];

const document = new Document({
  creator: "TOE-SYLVA",
  title: "Floquet-BdG 全样本共同表示审计",
  description: "全部16个尺寸对照的两种共同表示与交换候选。",
  features: { updateFields: true },
  styles: { paragraphStyles: [1, 2].map((level) => ({ id: `TOC${level}`, name: `TOC ${level}`, basedOn: "Normal", next: "Normal", quickFormat: true, run: { font, size: 19, color: palette.dark }, paragraph: { spacing: { after: 70, line: 240 }, indent: { left: (level - 1) * 360 } } })) },
  footnotes: {
    1: { children: [footnote("embedding_census_protocol.json. Both embeddings reuse the same eigenvectors, grids and principal-subspace definitions.")] },
    2: { children: [footnote("embedding_census_analysis.json. Ninety-six method grids cover all sixteen preregistered contrasts without statistical-population inference.")] },
    3: { children: [footnote("seed_6_r_0p05 is the only swap candidate at M=4800. The score relation is robust across both embeddings and all three grids, but no state exchange is proven.")] },
  },
  sections: [{
    properties: { page: { margin: { top: 900, bottom: 900, left: 1000, right: 1000 } } },
    headers: { default: new Header({ children: [para(run("TOE-SYLVA · Floquet-BdG · 全样本共同表示审计", { size: 17, color: palette.primary }), { alignment: AlignmentType.CENTER })] }) },
    footers: { default: new Footer({ children: [para(new TextRun({ children: [PageNumber.CURRENT], font, size: 17 }), { alignment: AlignmentType.CENTER })] }) },
    children,
  }],
});
fs.writeFileSync(outputPath, await Packer.toBuffer(document));
