import fs from "node:fs";
import path from "node:path";
import {
  AlignmentType, Document, Footer, FootnoteReferenceRun, Header, HeadingLevel,
  ImageRun, ImportedXmlComponent, Math as MathEquation, MathFraction, MathRun,
  MathSubScript, MathSuperScript, Packer, PageBreak, PageNumber, Paragraph,
  ShadingType, Table, TableCell, TableRow, TextRun, WidthType,
} from "docx";

const outputPath = process.argv[2];
if (!outputPath) throw new Error("Usage: node build_holdout_pair_evaluation_report.js /absolute/path/report.docx");
const root = path.dirname(outputPath);
const analysis = JSON.parse(fs.readFileSync(path.join(root, "holdout_pair_evaluation_analysis.json"), "utf8"));
const independent = JSON.parse(fs.readFileSync(path.join(root, "holdout_pair_evaluation_independent.json"), "utf8"));
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
const directionText = { same_as_jump_changes: "同向", opposite_to_jump_changes: "反向" };
const outcomeTable = makeTable(
  ["seed", "路径角色", "跳变改变数", "是否进入剩余对"],
  Array.from({ length: 8 }, (_, seed) => [String(seed), seed in Object.fromEntries(analysis.comparison_seed_values.map((value) => [value, true])) ? "对照实现" : "剩余实现", String(analysis.jump_counts[String(seed)]), seed in Object.fromEntries(analysis.comparison_seed_values.map((value) => [value, true])) ? "仅与剩余种子配对" : "是"]),
  [900, 2600, 2200, 4206], 8,
);
const tiePairs = analysis.pair_evaluations.slice(0, 25).filter((row) => !row.informative);
const tieTable = makeTable(
  ["seed 对", "跳变计数", "处理"],
  tiePairs.map((row) => [`${row.seed_a}—${row.seed_b}`, `${row.jump_a}＝${row.jump_b}`, "无方向信息；保留，不判一致或不一致"]),
  [1800, 2000, 6106], 8,
);
const candidateTable = makeTable(
  ["指标", "方向", "一致对", "不一致对", "平局", "候选零差分", "规则结论"],
  analysis.candidate_summaries.map((row) => [row.metric, directionText[row.direction], String(row.consistent_pair_count), String(row.inconsistent_pair_count), String(row.uninformative_pair_count), String(row.candidate_tie_count), row.all_informative_pairs_consistent ? "全部一致" : "未全部一致"]),
  [2150, 750, 950, 1050, 750, 1250, 3006], 7,
);
const verificationTable = makeTable(
  ["复核对象", "数量／误差", "结果"],
  [
    ["逐对记录", `${independent.pair_record_count} 条；不一致 ${independent.pair_record_mismatch_count}`, "全部重放一致"],
    ["有效对与平局", `${independent.informative_pair_count}／${independent.uninformative_pair_count}`, "与冻结规则一致"],
    ["路径结局来源", `来源不一致 ${independent.source_outcome_mismatch_count}`, "全部绑定"],
    ["候选值", `最大误差 ${independent.max_value_absolute_error}`, "逐值一致"],
    ["候选汇总", `汇总不一致 ${independent.summary_mismatch_count}`, "全部一致"],
  ],
  [2700, 4500, 2706], 8,
);
const consistentCount = analysis.candidate_summaries.filter((row) => row.all_informative_pairs_consistent).length;
const png = fs.readFileSync(path.join(root, "holdout-pair-evaluation.png"));
const pixelWidth = png.readUInt32BE(16);
const pixelHeight = png.readUInt32BE(20);
const titles = ["一、路径结局与检验对", "二、图件与跳变平局", "三、全部十六项候选结果", "四、独立复核与证据边界"];
const children = [
  para(run("Floquet-BdG 剩余种子候选逐对方向检验", { bold: true, size: 32, color: palette.dark }), { heading: HeadingLevel.TITLE, alignment: AlignmentType.CENTER, spacing: { before: 560, after: 220 } }),
  para(run("400 条完整记录，不筛选有利结果", { bold: true, size: 25, color: palette.primary }), { alignment: AlignmentType.CENTER, spacing: { after: 230 } }),
  para(run("16 个候选 × 25 对 · 20 个有效对 · 5 个跳变平局", { size: 20, color: palette.light }), { alignment: AlignmentType.CENTER, spacing: { after: 260 } }),
  para(run(`${analysis.report_date}　不是预测，不计算相关性、回归或 p 值`, { size: 19, color: palette.accent }), { alignment: AlignmentType.CENTER, spacing: { after: 300 } }),
  heading("目录"),
  small("以下页码为可见缓存；在 Word/WPS 中更新域可刷新。"),
  toc(titles.map((title, index) => ({ title, level: 1, page: index + 2 }))),
  pageBreak(),

  heading(titles[0]),
  citedBody("全部8个种子的28个无序对中，排除 seed=0、1、6 内部的3个训练对，得到25个至少涉及一个剩余种子的检验对。每个候选均保留全部25对，不删除失败或平局。", 1),
  outcomeTable,
  equation([subSup("d", "ab", "(m)"), new MathRun(" = sgn("), sub("J", "b"), new MathRun(" − "), sub("J", "a"), new MathRun(") · "), sub("σ", "m"), new MathRun("；sgn(x) = "), new MathFraction({ numerator: [new MathRun("x")], denominator: [new MathRun("|x|")] })]),
  small("σm=+1 表示同向，σm=−1 表示反向；x=0 时不定义符号。候选差分符号与 d 相同才记为一致。跳变计数相同的对不计算方向。",
  ),
  body("20 个有效对用于严格方向核对，5 个跳变平局只保留记录。训练种子内部的 3 个对不参与本次规则结论。"),
  pageBreak(),

  heading(titles[1]),
  citedBody("图件同时展示八个实现的路径结局、检验对类型、16 个候选的一致与不一致计数，以及 20 个有效对的逐格结果。它不是预测准确率图。", 2),
  para(new ImageRun({ type: "png", data: png, transformation: { width: 500, height: Math.round(500 * pixelHeight / pixelWidth) } }), { alignment: AlignmentType.CENTER, keepNext: true }),
  para(run("图 1　冻结候选的逐对方向检验。绿色表示符合冻结方向，红色表示不符合。", { size: 16, italics: true }), { alignment: AlignmentType.CENTER }),
  tieTable,
  pageBreak(),

  heading(titles[2]),
  citedBody("严格规则要求全部 20 个有效对都满足冻结方向。任何一对不一致或候选零差分，都使候选不能记为全部一致。", 3),
  candidateTable,
  small(`共有 ${consistentCount} 个候选全部一致，${16 - consistentCount} 个未全部一致。q99 与 block_std_max 的 18 对一致、2 对不一致也必须保留，不能改写为验证通过。`),
  body("一致与不一致计数只用于核对预登记规则，不是预测准确率、统计显著性或物理理论真伪判定。全部 400 条逐对记录均保存在分析 JSON 中。"),
  pageBreak(),

  heading(titles[3]),
  citedBody("独立脚本从既有候选值和全部路径结局重新生成 400 条记录与 16 组汇总，不重新计算 Floquet 谱。", 4),
  verificationTable,
  heading("不是完全未触碰的外部验证集", 2),
  body("候选值此前已用于描述统计，只有路径跳变结局是新生成的。本工作至多是结局盲的逐对方向检验，不是外部实验重复、预测验证、相关性分析或统计显著性检验。"),
  heading("不可外推的结论", 2),
  body("全部一致也不构成统计显著性；不一致也不等于证伪物理理论。本报告不新增 Floquet 单元，不补算体 winding，未计算 N=640，不外推真实态交换、谱交叉、连续路径、普遍尺寸律、因果机制、热力学极限或新类别。"),
  body("复现：python research/floquet-bdg-tbc/analyze_holdout_pair_evaluation.py；独立复核：python research/floquet-bdg-tbc/verify_holdout_pair_evaluation.py。"),
  para(run("证据边界：严格方向规则已经完成，但预测验证、外部重复和统计显著性评估均未完成。", { size: 18, color: palette.accent })),
];

const document = new Document({
  creator: "TOE-SYLVA",
  title: "Floquet-BdG 剩余种子候选逐对方向检验",
  description: "16个冻结候选在25个剩余种子相关对上的完整方向检验。",
  features: { updateFields: true },
  styles: { paragraphStyles: [1, 2].map((level) => ({ id: `TOC${level}`, name: `TOC ${level}`, basedOn: "Normal", next: "Normal", quickFormat: true, run: { font, size: 19, color: palette.dark }, paragraph: { spacing: { after: 70, line: 240 }, indent: { left: (level - 1) * 360 } } })) },
  footnotes: {
    1: { children: [footnote("remaining_seed_outcome_protocol.json and all five remaining-seed path outcome files. Twenty-five pairs involve at least one remaining seed; three training-only pairs are excluded.")] },
    2: { children: [footnote("holdout_pair_evaluation_analysis.json and holdout-pair-evaluation.png. All 400 pair records are retained, including failures and jump ties.")] },
    3: { children: [footnote("holdout_pair_evaluation_analysis.json. Strict all-informative-pair consistency is descriptive and is not a predictive validation or significance test.")] },
    4: { children: [footnote("holdout_pair_evaluation_independent.json. Independent replay confirms all 400 records and 16 summaries without new Floquet spectra.")] },
  },
  sections: [{
    properties: { page: { margin: { top: 900, bottom: 900, left: 1000, right: 1000 } } },
    headers: { default: new Header({ children: [para(run("TOE-SYLVA · Floquet-BdG · 剩余种子逐对方向检验", { size: 17, color: palette.primary }), { alignment: AlignmentType.CENTER })] }) },
    footers: { default: new Footer({ children: [para(new TextRun({ children: [PageNumber.CURRENT], font, size: 17 }), { alignment: AlignmentType.CENTER })] }) },
    children,
  }],
});
fs.writeFileSync(outputPath, await Packer.toBuffer(document));
