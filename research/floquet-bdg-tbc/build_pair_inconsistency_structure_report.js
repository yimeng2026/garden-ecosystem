import fs from "node:fs";
import path from "node:path";
import {
  AlignmentType, Document, Footer, FootnoteReferenceRun, Header, HeadingLevel,
  ImageRun, ImportedXmlComponent, Math as MathEquation, MathFraction, MathRun,
  MathSubScript, MathSuperScript, Packer, PageBreak, PageNumber, Paragraph,
  ShadingType, Table, TableCell, TableRow, TextRun, WidthType,
} from "docx";

const outputPath = process.argv[2];
if (!outputPath) throw new Error("Usage: node build_pair_inconsistency_structure_report.js /absolute/path/report.docx");
const root = path.dirname(outputPath);
const analysis = JSON.parse(fs.readFileSync(path.join(root, "pair_inconsistency_structure_analysis.json"), "utf8"));
const independent = JSON.parse(fs.readFileSync(path.join(root, "pair_inconsistency_structure_independent.json"), "utf8"));
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
const pairsText = (pairs) => pairs.length ? pairs.map(([a, b]) => `${a}-${b}`).join("、") : "无";
const pairTable = makeTable(
  ["seed 对", "跳变计数", "一致候选", "不一致候选", "候选零差分", "集中程度"],
  analysis.pair_summaries.map((row) => [`${row.seed_a}—${row.seed_b}`, `${row.jump_a}→${row.jump_b}`, String(row.consistent_count), String(row.inconsistent_count), String(row.zero_diff_count), row.all_candidates_inconsistent ? "全部失败" : row.all_candidates_consistent ? "全部一致" : "混合"]),
  [1200, 1500, 1400, 1500, 1600, 2706], 7,
);
const closest = analysis.closest_candidate_comparison;
const closestTable = makeTable(
  ["集合关系", "数量", "seed 对"],
  [
    ["共同失败", String(closest.intersection_count), pairsText(closest.shared_pairs)],
    ["仅 q99 失败", String(closest.only_a_count), pairsText(closest.only_a_pairs)],
    ["仅 block_std_max 失败", String(closest.only_b_count), pairsText(closest.only_b_pairs)],
    ["并集", String(closest.union_count), pairsText([...closest.shared_pairs, ...closest.only_a_pairs, ...closest.only_b_pairs])],
  ],
  [2600, 1000, 6306], 8,
);
const failureTable = makeTable(
  ["指标", "失败数", "失败 seed 对", "候选零差分"],
  analysis.candidate_failure_sets.map((row) => [row.metric, String(row.failing_pairs.length), pairsText(row.failing_pairs), pairsText(row.zero_diff_pairs)]),
  [1850, 800, 5956, 1300], 6,
);
const verificationTable = makeTable(
  ["复核对象", "数量／不一致", "结果"],
  [
    ["无序对汇总", `20 组；不一致 ${independent.pair_summary_mismatch_count}`, "全部一致"],
    ["失败集合", `16 组；不一致 ${independent.failure_set_mismatch_count}`, "全部一致"],
    ["集合重叠", `120 组；不一致 ${independent.overlap_mismatch_count}`, "全部一致"],
    ["完整 k 谱", `不一致 ${independent.spectrum_mismatch_count}`, "全部一致"],
    ["最接近候选比较", `不一致 ${independent.closest_comparison_mismatch_count}`, "全部一致"],
  ],
  [2700, 4500, 2706], 8,
);
const png = fs.readFileSync(path.join(root, "pair-inconsistency-structure.png"));
const pixelWidth = png.readUInt32BE(16);
const pixelHeight = png.readUInt32BE(20);
const titles = ["一、二十个无序对的失败分布", "二、图件与最接近候选比较", "三、失败集合与一百二十组重叠", "四、独立复核与证据边界"];
const children = [
  para(run("Floquet-BdG 候选不一致对结构分析", { bold: true, size: 32, color: palette.dark }), { heading: HeadingLevel.TITLE, alignment: AlignmentType.CENTER, spacing: { before: 560, after: 220 } }),
  para(run("共同失败与指标特异失败，不是因果归因", { bold: true, size: 25, color: palette.primary }), { alignment: AlignmentType.CENTER, spacing: { after: 230 } }),
  para(run("20 个有效对 · 16 个失败集合 · 120 组重叠 · 104 条失败赋值", { size: 20, color: palette.light }), { alignment: AlignmentType.CENTER, spacing: { after: 260 } }),
  para(run(`${analysis.report_date}　不是预测，不修改严格规则，不提出集成或新指标`, { size: 19, color: palette.accent }), { alignment: AlignmentType.CENTER, spacing: { after: 300 } }),
  heading("目录"),
  small("以下页码为可见缓存；在 Word/WPS 中更新域可刷新。"),
  toc(titles.map((title, index) => ({ title, level: 1, page: index + 2 }))),
  pageBreak(),

  heading(titles[0]),
  citedBody("只使用既有20个有效无序对。每个对均保留16个候选的一致与不一致计数，原400条记录和5个跳变平局不变。", 1),
  pairTable,
  equation([subSup("I", "ab", ""), new MathRun(" = ∑"), sub("m", ""), sup("1", "inconsistent"), new MathRun("，0≤"), sub("I", "ab"), new MathRun("≤16")]),
  small(`没有任何无序对让16个候选全部失败，也没有让全部候选一致。最集中的2—5对有 ${independent.max_pair_inconsistent_candidate_count} 个候选失败。`),
  pageBreak(),

  heading(titles[1]),
  citedBody("图件展示每个无序对的失败候选数、完整 k 谱、失败集合 Jaccard 重叠，以及 q99 与 block_std_max 的集合关系。它不是预测准确率或因果图。", 2),
  para(new ImageRun({ type: "png", data: png, transformation: { width: 500, height: Math.round(500 * pixelHeight / pixelWidth) } }), { alignment: AlignmentType.CENTER, keepNext: true }),
  para(run("图 1　共同失败与指标特异失败的结构。Jaccard 只描述集合重叠。", { size: 16, italics: true }), { alignment: AlignmentType.CENTER }),
  closestTable,
  small(`q99 与 block_std_max 的 Jaccard=${closest.jaccard}。两者共享0—2，但各自另有不同失败位置，不能视为等价指标。`),
  pageBreak(),

  heading(titles[2]),
  citedBody("120 组候选两两组合均计算交集、并集、共享对和单侧对。Jaccard 在并集非空时定义为交集与并集之比；空并集记为 null。", 3),
  equation([sub("J", "AB"), new MathRun(" = "), new MathFraction({ numerator: [new MathRun("|"), sub("F", "A"), new MathRun(" ∩ "), sub("F", "B"), new MathRun("|")], denominator: [new MathRun("|"), sub("F", "A"), new MathRun(" ∪ "), sub("F", "B"), new MathRun("|")] })]),
  failureTable,
  small("失败集合包含方向不一致和候选零差分；零差分另列。完整120组重叠保存在分析 JSON，不在正文选择性展示。",
  ),
  pageBreak(),

  heading(titles[3]),
  citedBody("独立脚本从400条原始逐对记录重新计算全部结构，不重新计算 Floquet 谱。", 4),
  verificationTable,
  heading("共同失败不是因果归因", 2),
  body("同一无序实现对多个统计量的共同影响、离散跳变计数造成的集合重合，都可能产生共同失败。当前数据不能区分这些解释，因此不能把共同失败直接命名为物理机制。指标特异失败也不自动等于指标缺陷。"),
  heading("严格规则保持不变", 2),
  body("本分析不是预测验证、统计显著性检验或完全未触碰的外部验证；不提出新指标、集成规则或修正版接受阈值。严格规则下0／16全对一致的原结论不变。"),
  body("复现：python research/floquet-bdg-tbc/analyze_pair_inconsistency_structure.py；独立复核：python research/floquet-bdg-tbc/verify_pair_inconsistency_structure.py。"),
  para(run("证据边界：结构分析已经完成，但因果机制、预测能力和外部实验重复均未建立。", { size: 18, color: palette.accent })),
];

const document = new Document({
  creator: "TOE-SYLVA",
  title: "Floquet-BdG 候选不一致对结构分析",
  description: "20个有效对、16个失败集合和120组重叠的描述性结构分析。",
  features: { updateFields: true },
  styles: { paragraphStyles: [1, 2].map((level) => ({ id: `TOC${level}`, name: `TOC ${level}`, basedOn: "Normal", next: "Normal", quickFormat: true, run: { font, size: 19, color: palette.dark }, paragraph: { spacing: { after: 70, line: 240 }, indent: { left: (level - 1) * 360 } } })) },
  footnotes: {
    1: { children: [footnote("pair_inconsistency_structure_protocol.json and holdout_pair_evaluation_analysis.json. Only the 20 informative pairs enter structural summaries; all source records remain unchanged.")] },
    2: { children: [footnote("pair_inconsistency_structure_analysis.json and pair-inconsistency-structure.png. The full k spectrum and all 120 overlap records are descriptive, not causal or predictive.")] },
    3: { children: [footnote("pair_inconsistency_structure_analysis.json. Failure sets include candidate zero differences and list them separately; empty-union Jaccard is null.")] },
    4: { children: [footnote("pair_inconsistency_structure_independent.json. Independent recomputation confirms all pair summaries, failure sets, overlaps, spectrum and closest-candidate comparison.")] },
  },
  sections: [{
    properties: { page: { margin: { top: 900, bottom: 900, left: 1000, right: 1000 } } },
    headers: { default: new Header({ children: [para(run("TOE-SYLVA · Floquet-BdG · 候选不一致对结构", { size: 17, color: palette.primary }), { alignment: AlignmentType.CENTER })] }) },
    footers: { default: new Footer({ children: [para(new TextRun({ children: [PageNumber.CURRENT], font, size: 17 }), { alignment: AlignmentType.CENTER })] }) },
    children,
  }],
});
fs.writeFileSync(outputPath, await Packer.toBuffer(document));
