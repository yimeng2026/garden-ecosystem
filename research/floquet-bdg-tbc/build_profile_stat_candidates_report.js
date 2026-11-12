import fs from "node:fs";
import path from "node:path";
import {
  AlignmentType, Document, Footer, FootnoteReferenceRun, Header, HeadingLevel,
  ImageRun, ImportedXmlComponent, Math as MathEquation, MathFraction, MathRun,
  MathSubScript, MathSuperScript, Packer, PageBreak, PageNumber, Paragraph,
  ShadingType, Table, TableCell, TableRow, TextRun, WidthType,
} from "docx";

const outputPath = process.argv[2];
if (!outputPath) throw new Error("Usage: node build_profile_stat_candidates_report.js /absolute/path/report.docx");
const root = path.dirname(outputPath);
const analysis = JSON.parse(fs.readFileSync(path.join(root, "profile_stat_candidates_analysis.json"), "utf8"));
const independent = JSON.parse(fs.readFileSync(path.join(root, "profile_stat_candidates_independent.json"), "utf8"));
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
const directionText = { same_as_jump_changes: "同向", opposite_to_jump_changes: "反向", unordered: "无序" };
const coarseningText = { both_same: "两尺寸同向", different: "两尺寸不同向", unordered: "无序", not_applicable: "不适用" };

const profileTable = makeTable(
  ["seed", "均值", "标准差", "最小值", "5%分位", "95%分位", "最大值", "粗糙度", "x<0.1", "x>0.8", "lag1"],
  analysis.profiles.map((row) => {
    const s = row.master_metrics;
    return [String(row.seed), fmt(s.mean), fmt(s.std), fmt(s.min), fmt(s.q05), fmt(s.q95), fmt(s.max), fmt(s.roughness_rms), fmt(s.low_frac_0p1), fmt(s.high_frac_0p8), fmt(s.lag1)];
  }),
  [500, 900, 900, 1000, 900, 900, 1000, 1000, 900, 900, 1006], 7,
);
const candidateTable = makeTable(
  ["指标", "层级", "方向", "block标签", "取值数", "seed=1", "seed=0", "seed=6"],
  analysis.candidate_metrics.slice(0, 12).map((row) => [row.metric, row.level, directionText[row.direction], coarseningText[row.coarsening_direction], String(row.unique_count), fmt(row.values["1"]), fmt(row.values["0"]), fmt(row.values["6"])]),
  [1500, 750, 750, 1050, 650, 1750, 1750, 1706], 7,
);
const verificationTable = makeTable(
  ["复核对象", "数量／误差", "结论"],
  [
    ["主剖面", `${independent.profile_count} 个；最大误差 ${independent.max_master_absolute_error}`, "逐值一致"],
    ["N=400／600 块平均", `两种；最大误差 ${independent.max_beta_absolute_error}`, "逐值一致"],
    ["全部指标", `${independent.metric_record_count} 组；最大误差 ${independent.max_metric_absolute_error}`, "数值一致"],
    ["候选标签", `不一致 ${independent.candidate_mismatch_count} 项`, "方向与标签一致"],
  ],
  [2600, 4500, 2806], 8,
);
const pathTable = makeTable(
  ["对照 seed", "跳变改变数", "主导项计数", "监督排序可用性"],
  [["0", "4", "4", "无"], ["1", "0", "4", "无"], ["6", "6", "4", "无"]],
  [1800, 2200, 2200, 3706], 8,
);
const titles = ["一、八个主剖面与描述统计", "二、候选规则与前十二项", "三、图件与独立复核", "四、不能建模的边界与下一步"];
const children = [
  para(run("Floquet-BdG 无序剖面候选统计指标", { bold: true, size: 32, color: palette.dark }), { heading: HeadingLevel.TITLE, alignment: AlignmentType.CENTER, spacing: { before: 560, after: 220 } }),
  para(run("从描述统计到可检验问题，而不是直接预测", { bold: true, size: 25, color: palette.primary }), { alignment: AlignmentType.CENTER, spacing: { after: 230 } }),
  para(run("8 个主剖面 · 40 组指标 · 16 个探索性候选", { size: 20, color: palette.light }), { alignment: AlignmentType.CENTER, spacing: { after: 260 } }),
  para(run(`${analysis.report_date}　不拟合预测模型，不计算相关性或 p 值`, { size: 19, color: palette.accent }), { alignment: AlignmentType.CENTER, spacing: { after: 300 } }),
  heading("目录"),
  small("以下页码为可见缓存；在 Word/WPS 中更新域可刷新。"),
  toc(titles.map((title, index) => ({ title, level: 1, page: index + 2 }))),
  pageBreak(),

  heading(titles[0]),
  citedBody("从既有批次按 seed 去重得到 8 个主剖面，每个包含 4800 个值。统一计算位置、尾部、粗糙度、总变差、符号变化、滞后相关和局部 block 统计，不归一化，也不按结果筛选剖面。", 1),
  equation([subSup("β", "s,b", "(N)"), new MathRun(" = "), new MathFraction({ numerator: [new MathRun("∑"), sub("x", "s,(b−1)kN+j")], denominator: [sub("k", "N")] })]),
  small("N=400 时每块 12 个值，N=600 时每块 8 个值；局部标准差使用 ddof=0。公式中的求和范围为每块全部元素。"),
  profileTable,
  small("表中数值仅描述当前 8 个无序实现。粗糙度为相邻差分均方根，lag1 为一阶滞后相关；它们不是谱跳变的因果代理。"),
  pageBreak(),

  heading(titles[1]),
  citedBody("预登记规则要求指标在 8 个种子中至少有 6 个不同取值，并在 seed=1、0、6 上严格同向或反向于跳变改变数 0、4、6。block 指标另记录 N=400 与 N=600 是否同向，但不把该标签当成独立验证。", 2),
  equation([sub("C", "m"), new MathRun(" = 1 ⇔ "), sub("u", "m"), new MathRun(" ≥ 6 且严格同向或反向；"), sup("m", "stored"), new MathRun(" 与重建值逐项比较")]),
  candidateTable,
  small(`共 ${analysis.candidate_metrics.length} 个候选；本表按协议顺序展示前 12 个，其余为 ${analysis.candidate_metrics.slice(12).map((row) => row.metric).join("、")}。完整 40 组结果全部保留在 JSON。`),
  pageBreak(),

  heading(titles[2]),
  citedBody(`独立脚本重建全部主剖面、两种块平均、全部指标和候选标签。最大主剖面误差、块平均误差与指标误差均为 ${independent.max_metric_absolute_error}，候选标签不一致数为 ${independent.candidate_mismatch_count}。`, 3),
  para(new ImageRun({ type: "png", data: fs.readFileSync(path.join(root, "profile-stat-candidates.png")), transformation: { width: 500, height: Math.round(500 * 1393 / 2133) } }), { alignment: AlignmentType.CENTER, keepNext: true }),
  para(run("图 1　主剖面位置、粗糙度、尾部分数及前 12 个探索性候选的秩次。秩次只用于描述，不是预测准确率。", { size: 16, italics: true }), { alignment: AlignmentType.CENTER }),
  verificationTable,
  small("独立复核没有重新计算 Floquet 谱，也没有拟合模型、计算相关性、回归或 p 值。"),
  pageBreak(),

  heading(titles[3]),
  citedBody("三个对照种子的主导项计数均为 4，不能提供监督排序。跨种子最大跳变链接完全一致的条目数为 0，说明实现依赖不能被步长细化消除，也不能由单一统计量替代。", 4),
  pathTable,
  heading("探索性候选的正确用途", 2),
  body("这 16 个指标只能作为后续研究的问题生成器。若继续使用，必须先在剩余种子上预注册指标、结局定义、比较方向和排除规则，再评估一致方向是否保持；不能把本轮方向匹配当作可推广的预测能力。"),
  heading("不可外推的结论", 2),
  body("本报告不构成统计显著性、因果归因、预测准确率、真实态交换、谱交叉、普遍尺寸律或热力学极限结论。旧交换候选属于不同无序实现，不能与统计差分直接相减。未补算体 winding，未计算 N=640，也未改变旧类别。"),
  body("复现：python research/floquet-bdg-tbc/analyze_profile_stat_candidates.py；独立复核：python research/floquet-bdg-tbc/verify_profile_stat_candidates.py。"),
  para(run("证据边界：8 个既有主剖面、40 组描述统计和 16 个探索性候选；下一步是预注册验证，而不是直接预测。", { size: 18, color: palette.accent })),
];

const document = new Document({
  creator: "TOE-SYLVA",
  title: "Floquet-BdG 无序剖面候选统计指标",
  description: "八个无序主剖面的描述统计、探索性候选和独立复核。",
  features: { updateFields: true },
  styles: { paragraphStyles: [1, 2].map((level) => ({ id: `TOC${level}`, name: `TOC ${level}`, basedOn: "Normal", next: "Normal", quickFormat: true, run: { font, size: 19, color: palette.dark }, paragraph: { spacing: { after: 70, line: 240 }, indent: { left: (level - 1) * 360 } } })) },
  footnotes: {
    1: { children: [footnote("profile_stat_candidates_protocol.json, matched_beta_batch_a_analysis.json and matched_beta_batch_b_analysis.json. Eight established masters are deduplicated by seed; no favorable realization is selected.")] },
    2: { children: [footnote("profile_stat_candidates_protocol.json and profile_stat_candidates_analysis.json. The direction and distinct-value rule is descriptive and preregistered; it is not a significance test.")] },
    3: { children: [footnote("profile_stat_candidates_independent.json. All masters, block means, metrics and candidate labels are rebuilt independently with zero observed numerical mismatch.")] },
    4: { children: [footnote("seed01_matrix_midpoint_analysis.json and seed6_matrix_midpoint_analysis.json. Jump-change counts are 4, 0 and 6 for seeds 0, 1 and 6; every driver-change count is 4.")] },
  },
  sections: [{
    properties: { page: { margin: { top: 900, bottom: 900, left: 1000, right: 1000 } } },
    headers: { default: new Header({ children: [para(run("TOE-SYLVA · Floquet-BdG · 无序剖面候选统计", { size: 17, color: palette.primary }), { alignment: AlignmentType.CENTER })] }) },
    footers: { default: new Footer({ children: [para(new TextRun({ children: [PageNumber.CURRENT], font, size: 17 }), { alignment: AlignmentType.CENTER })] }) },
    children,
  }],
});
fs.writeFileSync(outputPath, await Packer.toBuffer(document));
