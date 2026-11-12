import fs from "node:fs";
import path from "node:path";
import {
  AlignmentType, Document, Footer, FootnoteReferenceRun, Header, HeadingLevel,
  ImageRun, ImportedXmlComponent, Math as MathEquation, MathFraction, MathRun,
  MathSubScript, MathSuperScript, Packer, PageBreak, PageNumber, Paragraph,
  ShadingType, Table, TableCell, TableRow, TextRun, WidthType,
} from "docx";

const outputPath = process.argv[2];
if (!outputPath) throw new Error("Usage: node build_remaining_seed_outcome_report.js /absolute/path/report.docx");
const root = path.dirname(outputPath);
const match = path.basename(outputPath).match(/seed(\d+)/);
if (!match) throw new Error("The output filename must contain a seed number");
const seed = Number(match[1]);
const analysis = JSON.parse(fs.readFileSync(path.join(root, `remaining_seed${seed}_path_outcome_analysis.json`), "utf8"));
const independent = JSON.parse(fs.readFileSync(path.join(root, `remaining_seed${seed}_path_outcome_independent.json`), "utf8"));
const font = { ascii: "Times New Roman", hAnsi: "Times New Roman", cs: "Times New Roman", eastAsia: "SimSun" };
const palette = { dark: "293B40", primary: "356A64", accent: "A25B3F", light: "687A7E", fill: "EDF3F1" };
const run = (text, options = {}) => new TextRun({ text: String(text), font, size: 20, ...options });
const para = (children, options = {}) => new Paragraph({ spacing: { after: 100, line: 270 }, ...options, children: Array.isArray(children) ? children : [children] });
const body = (text) => para(run(text), { indent: { firstLine: 400 } });
const small = (text, options = {}) => para(run(text, { size: 17, color: palette.light, ...options }));
const citedBody = (text, id) => para([run(text), new FootnoteReferenceRun(id)], { indent: { firstLine: 400 } });
const heading = (text, level = 1) => para(run(text, { bold: true, size: level === 1 ? 29 : 23, color: palette.dark }), { heading: level === 1 ? HeadingLevel.HEADING_1 : HeadingLevel.HEADING_2, spacing: { before: 170, after: 100 }, keepNext: true });
const pageBreak = () => new Paragraph({ children: [new PageBreak()] });
const xmlEscape = (value) => String(value).replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;");
const toc = (entries) => {
  const cached = entries.map(({ title, level, page }) => `<w:p><w:pPr><w:pStyle w:val="TOC${level}"/><w:tabs><w:tab w:val="right" w:leader="dot" w:pos="9000"/></w:tabs><w:ind w:left="${Math.max(0, level - 1) * 360}"/></w:pPr><w:r><w:t>${xmlEscape(title)}</w:t></w:r><w:r><w:tab/></w:r><w:r><w:t>${page}</w:t></w:r></w:p>`).join("");
  return ImportedXmlComponent.fromXmlString(`<w:sdt xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:sdtPr><w:alias w:val="目录"/></w:sdtPr><w:sdtContent><w:p><w:r><w:fldChar w:fldCharType="begin" w:dirty="true"/><w:instrText xml:space="preserve"> TOC \\o &quot;1-2&quot; \\h \\z \\u </w:instrText><w:fldChar w:fldCharType="separate"/></w:r></w:p>${cached}<w:p><w:r><w:fldChar w:fldCharType="end"/></w:r></w:p></w:sdtContent></w:sdt>`).root[0];
};
const cell = (text, index, widths, header, size = 8) => new TableCell({
  children: [para(run(text, { size, bold: header }), { spacing: { after: 40, line: 240, lineRule: "auto" } })],
  width: { size: widths[index], type: WidthType.DXA }, margins: { top: 80, bottom: 80, left: 60, right: 60 },
  shading: header ? { type: ShadingType.CLEAR, fill: palette.fill } : undefined,
});
const makeTable = (headers, rows, widths, size = 8) => new Table({
  width: { size: widths.reduce((a, b) => a + b, 0), type: WidthType.DXA }, columnWidths: widths,
  rows: [new TableRow({ tableHeader: true, cantSplit: true, children: headers.map((text, index) => cell(text, index, widths, true, size)) }), ...rows.map((row) => new TableRow({ cantSplit: true, children: row.map((text, index) => cell(text, index, widths, false, size)) }))],
});
const equation = (children) => para(new MathEquation({ children: Array.isArray(children) ? children : [new MathRun(children)] }), { alignment: AlignmentType.CENTER, spacing: { before: 55, after: 70 } });
const sub = (base, subscript) => new MathSubScript({ children: [new MathRun(base)], subScript: [new MathRun(subscript)] });
const sup = (base, superScript) => new MathSuperScript({ children: [new MathRun(base)], superScript: [new MathRun(superScript)] });
const subSup = (base, subscript, superScript) => new MathSuperScript({ children: [sub(base, subscript)], superScript: [new MathRun(superScript)] });
const footnote = (text) => para(run(text, { size: 15 }), { spacing: { after: 30, line: 190 } });
const fmt = (value) => Number(value).toPrecision(6).replace(/\.0+$/, "");
const allSeeds = [2, 3, 4, 5, 7];
const completed = allSeeds.filter((value) => value === seed || fs.existsSync(path.join(root, `remaining_seed${value}_path_outcome_analysis.json`)));
const pending = allSeeds.filter((value) => !completed.includes(value));
const summary = analysis.summary;
const summaryTable = makeTable(
  ["seed", "尺寸单元", "跨尺寸矩阵", "原生链接", "跳变改变数", "主导改变数", "新中点极值数"],
  [[String(seed), "26", "78", "24", String(summary.jump_change_count), String(summary.driver_comparison_change_count), String(summary.new_extrema_midpoint_count)]],
  [700, 1300, 1500, 1300, 1800, 1800, 1506], 8,
);
const jumpTable = makeTable(
  ["方法", "项", "原最大跳变及链接", "细化最大跳变及链接", "改变"],
  analysis.jump_comparisons.map((row) => [row.method, row.entry, `${fmt(row.original_max_adjacent_absolute_jump)}（${row.original_jump_from}→${row.original_jump_to}）`, `${fmt(row.refined_max_adjacent_absolute_jump)}（${row.refined_jump_from}→${row.refined_jump_to}）`, row.jump_changed ? "是" : "否"]),
  [1300, 800, 2900, 2900, 2006], 7,
);
const verificationTable = makeTable(
  ["复核对象", "数量／误差", "结论"],
  [
    ["主剖面与块平均", `误差 ${independent.max_master_absolute_error}／${independent.max_beta_absolute_error}`, "逐值一致"],
    ["26 个预登记单元", `谱误差 ${independent.max_spectrum_absolute_error}`, "逐值一致"],
    ["78 组跨尺寸矩阵", `矩阵误差 ${independent.max_matrix_absolute_error}`, "数值一致"],
    ["288 条矩阵项差分", `误差 ${independent.max_entry_delta_absolute_error}`, "数值一致"],
    ["24 条原生链接", `误差 ${independent.max_native_link_absolute_error}`, "数值一致"],
    ["路径结局", `跳变／主导不一致 ${independent.jump_outcome_mismatch_count}／${independent.driver_outcome_mismatch_count}`, "完全一致"],
  ],
  [2700, 4600, 2606], 8,
);
const png = fs.readFileSync(path.join(root, `remaining-seed${seed}-outcome.png`));
const pixelWidth = png.readUInt32BE(16);
const pixelHeight = png.readUInt32BE(20);
const titles = ["一、冻结协议与路径结局", "二、图件与逐项跳变", "三、独立复核与证据边界"];
const children = [
  para(run(`Floquet-BdG seed=${seed} 剩余种子路径结局`, { bold: true, size: 32, color: palette.dark }), { heading: HeadingLevel.TITLE, alignment: AlignmentType.CENTER, spacing: { before: 560, after: 220 } }),
  para(run("只生成预登记结局，不提前评价候选", { bold: true, size: 25, color: palette.primary }), { alignment: AlignmentType.CENTER, spacing: { after: 230 } }),
  para(run("26 个尺寸单元 · 78 组跨尺寸矩阵 · 24 条原生链接", { size: 20, color: palette.light }), { alignment: AlignmentType.CENTER, spacing: { after: 260 } }),
  para(run(`${analysis.report_date}　不补算体 winding，未计算 N=640`, { size: 19, color: palette.accent }), { alignment: AlignmentType.CENTER, spacing: { after: 300 } }),
  heading("目录"),
  small("以下页码为可见缓存；在 Word/WPS 中更新域可刷新。"),
  toc(titles.map((title, index) => ({ title, level: 1, page: index + 2 }))),
  pageBreak(),

  heading(titles[0]),
  citedBody(`seed=${seed} 使用既有主剖面与冻结的13点强度网格。原9点／8链接与细化13点／12链接逐种子比较，全部点、链接和主导项均保留，不归一化，也不筛选有利路径段。`, 1),
  equation([subSup("β", "s,b", "(N)"), new MathRun(" = "), new MathFraction({ numerator: [new MathRun("∑"), sub("x", "s,(b−1)kN+j")], denominator: [sub("k", "N")] })]),
  small("N=400 时每块 12 个值，N=600 时每块 8 个值。跨尺寸矩阵不是同尺寸态跟踪，原生有限链接也不是连续路径证明。"),
  summaryTable,
  equation([sub("J", "s"), new MathRun(" = ∑"), sup("1", "changed"), new MathRun("，按两种表示与四个矩阵项逐对计数")]),
  body(`当前已完成 seed=${completed.join("、")} 的路径结局；待完成 seed=${pending.join("、")}。五个剩余种子全部齐备之前，候选逐对评估保持关闭。`),
  small(`本种子的跳变改变数为 ${summary.jump_change_count}，主导项计数改变数为 ${summary.driver_comparison_change_count}，新增中点参与极值的位置数为 ${summary.new_extrema_midpoint_count}。这些结局分别报告，不能互相替代。`),
  pageBreak(),

  heading(titles[1]),
  citedBody("图中同时保留两种表示的 O00、O01／O10 路径、步长改变计数和同尺寸原生重叠。图件用于描述路径，不作候选验证。", 2),
  para(new ImageRun({ type: "png", data: png, transformation: { width: 500, height: Math.round(500 * pixelHeight / pixelWidth) } }), { alignment: AlignmentType.CENTER, keepNext: true }),
  para(run(`图 1　seed=${seed} 的路径、步长改变计数及原生重叠。最大跳变位置不变不等于所有路径特征不变。`, { size: 16, italics: true }), { alignment: AlignmentType.CENTER }),
  jumpTable,
  pageBreak(),

  heading(titles[2]),
  citedBody(`独立重建 26 个预登记单元、78 组矩阵、24 条原生链接和 288 条矩阵项差分，协议外新增谱计算为 ${independent.additional_unregistered_floquet_spectra}。候选评估未执行。`, 3),
  verificationTable,
  heading("不是完全未触碰的外部验证集", 2),
  body("既有候选值曾在描述统计中出现，只有路径跳变结局是新生成的。因此，后续设计至多是结局盲的逐对方向检验，不是外部实验重复、预测模型、相关性分析或统计显著性检验。"),
  heading("不可外推的结论", 2),
  body("本报告不构成候选通过或淘汰、真实态交换、谱交叉、普遍尺寸律、因果机制或热力学极限结论。旧交换候选属于不同无序实现，不能与路径差分直接相减。"),
  body(`复现：python research/floquet-bdg-tbc/analyze_remaining_seed_outcome.py --seed ${seed}；独立复核：python research/floquet-bdg-tbc/verify_remaining_seed_outcome.py --seed ${seed}。`),
  para(run("证据边界：本页只确认 seed 的路径结局和复核一致性；其余种子与候选检验仍需按冻结协议继续。", { size: 18, color: palette.accent })),
];

const document = new Document({
  creator: "TOE-SYLVA",
  title: `Floquet-BdG seed=${seed} 剩余种子路径结局`,
  description: "剩余种子的预登记路径结局、图件与独立复核。",
  features: { updateFields: true },
  styles: { paragraphStyles: [1, 2].map((level) => ({ id: `TOC${level}`, name: `TOC ${level}`, basedOn: "Normal", next: "Normal", quickFormat: true, run: { font, size: 19, color: palette.dark }, paragraph: { spacing: { after: 70, line: 240 }, indent: { left: (level - 1) * 360 } } })) },
  footnotes: {
    1: { children: [footnote("remaining_seed_outcome_protocol.json. The candidate list, path grid, raw outcomes and pair policy were frozen before any remaining-seed path outcome was computed.")] },
    2: { children: [footnote(`remaining_seed${seed}_path_outcome_analysis.json. All preregistered points and links are retained; no candidate score is computed.`)] },
    3: { children: [footnote(`remaining_seed${seed}_path_outcome_independent.json. Independent reconstruction is limited to the 26 preregistered cells; no unregistered spectrum or candidate evaluation is added.`)] },
  },
  sections: [{
    properties: { page: { margin: { top: 900, bottom: 900, left: 1000, right: 1000 } } },
    headers: { default: new Header({ children: [para(run(`TOE-SYLVA · Floquet-BdG · seed=${seed} 路径结局`, { size: 17, color: palette.primary }), { alignment: AlignmentType.CENTER })] }) },
    footers: { default: new Footer({ children: [para(new TextRun({ children: [PageNumber.CURRENT], font, size: 17 }), { alignment: AlignmentType.CENTER })] }) },
    children,
  }],
});
fs.writeFileSync(outputPath, await Packer.toBuffer(document));
