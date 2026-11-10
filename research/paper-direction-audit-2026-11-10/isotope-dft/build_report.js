import fs from "node:fs";
import path from "node:path";
import {
  AlignmentType,
  Document,
  Footer,
  FootnoteReferenceRun,
  Header,
  HeadingLevel,
  ImageRun,
  ImportedXmlComponent,
  Math as MathEquation,
  MathFraction,
  MathRun,
  MathSubScript,
  Packer,
  PageBreak,
  PageNumber,
  Paragraph,
  ShadingType,
  Table,
  TableCell,
  TableRow,
  TextRun,
  WidthType,
} from "docx";

const outputPath = process.argv[2];
if (!outputPath) throw new Error("Usage: node build_report.js /absolute/path/REVIEW.docx");
const audit = path.dirname(outputPath);
const data = JSON.parse(fs.readFileSync(path.join(audit, "review.json"), "utf8"));
const font = { ascii: "Times New Roman", hAnsi: "Times New Roman", cs: "Times New Roman", eastAsia: "SimSun" };
const palette = { dark: "263238", primary: "455A64", light: "78909C", fill: "EEF3F6" };
const run = (text, options = {}) => new TextRun({ text: String(text), font, size: 22, ...options });
const para = (children, options = {}) => new Paragraph({
  spacing: { after: 120, line: 290 },
  ...options,
  children: Array.isArray(children) ? children : [children],
});
const body = (text, options = {}) => para(run(text), { indent: { firstLine: 420 }, ...options });
const bodyAfterTable = (text) => body(text, { spacing: { before: 180, after: 120, line: 290 } });
const citedBody = (text, footnoteId) => para([run(text), new FootnoteReferenceRun(footnoteId)], { indent: { firstLine: 420 } });
const heading = (text, level = 1) => para(run(text, { bold: true, size: level === 1 ? 30 : 26, color: palette.dark }), {
  heading: level === 1 ? HeadingLevel.HEADING_1 : HeadingLevel.HEADING_2,
  spacing: { before: 250, after: 140 },
  keepNext: true,
});
const xmlEscape = (value) => String(value)
  .replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;");
const toc = (entries) => {
  const cached = entries.map(({ title, level, page }) => `<w:p><w:pPr><w:pStyle w:val="TOC${level}"/>
    <w:tabs><w:tab w:val="right" w:leader="dot" w:pos="9000"/></w:tabs>
    <w:ind w:left="${Math.max(0, level - 1) * 360}"/></w:pPr>
    <w:r><w:t>${xmlEscape(title)}</w:t></w:r><w:r><w:tab/></w:r><w:r><w:t>${page}</w:t></w:r></w:p>`).join("");
  return ImportedXmlComponent.fromXmlString(`<w:sdt xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
    <w:sdtPr><w:alias w:val="目录"/></w:sdtPr><w:sdtContent>
      <w:p><w:r><w:fldChar w:fldCharType="begin" w:dirty="true"/>
        <w:instrText xml:space="preserve"> TOC \\o &quot;1-2&quot; \\h \\z \\u </w:instrText>
        <w:fldChar w:fldCharType="separate"/></w:r></w:p>
      ${cached}<w:p><w:r><w:fldChar w:fldCharType="end"/></w:r></w:p>
    </w:sdtContent></w:sdt>`).root[0];
};
const cell = (text, index, widths, header) => new TableCell({
  children: [para(run(text, { size: 16, bold: header }), { spacing: { after: 0, line: 210 } })],
  width: { size: widths[index], type: WidthType.DXA },
  margins: { top: 40, bottom: 40, left: 80, right: 80 },
  shading: header ? { type: ShadingType.CLEAR, fill: palette.fill } : undefined,
});
const makeTable = (headers, rows, widths) => new Table({
  width: { size: widths.reduce((a, b) => a + b, 0), type: WidthType.DXA },
  columnWidths: widths,
  rows: [
    new TableRow({ tableHeader: true, cantSplit: true, children: headers.map((text, index) => cell(text, index, widths, true)) }),
    ...rows.map((row) => new TableRow({ cantSplit: true, children: row.map((text, index) => cell(text, index, widths, false)) })),
  ],
});
const sub = (base, subscript) => new MathSubScript({ children: [new MathRun(base)], subScript: [new MathRun(subscript)] });
const isotopeEquation = () => para(new MathEquation({ children: [
  new MathRun("α = −"),
  new MathFraction({
    numerator: [new MathRun("ln "), sub("T", "c,D"), new MathRun(" − ln "), sub("T", "c,H")],
    denominator: [new MathRun("ln "), sub("M", "D"), new MathRun(" − ln "), sub("M", "H")],
  }),
] }), { alignment: AlignmentType.CENTER, spacing: { before: 120, after: 180 } });

const iso = data.evidence.isotope;
const pressure = data.evidence.pressure;
const jarvis = data.evidence.jarvis;
const nickelate = data.evidence.nickelate;
const titles = [
  "一、血缘裁决与四个发展方向",
  "二、同位素：公式、温度对和来源",
  "三、压力：斜率算术与方法分轨",
  "四、DFT 与机器学习：可复现契约",
  "五、分档勘误与发展任务",
  "六、验证范围与开放边界",
];
const children = [
  para(run("同位素压力与多层 DFT", { bold: true, size: 38, color: palette.dark }), {
    heading: HeadingLevel.TITLE,
    alignment: AlignmentType.CENTER,
    spacing: { before: 620, after: 230 },
  }),
  para(run("参数血缘、方法分轨与未竟工作审计", { bold: true, size: 30, color: palette.primary }), {
    alignment: AlignmentType.CENTER,
    spacing: { after: 300 },
  }),
  para(run("一个研究纲领 · 四个发展方向 · 只读审计", { size: 22, color: palette.light }), {
    alignment: AlignmentType.CENTER,
    spacing: { after: 240 },
  }),
  para(run("2026-11-10　不修改原文、不重跑计算、不新增实验", { size: 20 }), {
    alignment: AlignmentType.CENTER,
    spacing: { after: 360 },
  }),
  heading("目录"),
  para(run("以下页码为可见缓存；在 Word/WPS 中更新域可刷新。", { size: 18, italics: true, color: palette.light })),
  toc(titles.map((title, index) => ({ title, level: 1, page: [2, 2, 3, 3, 4, 4][index] }))),
  new Paragraph({ children: [new PageBreak()] }),

  heading(titles[0]),
  body(data.source_lineage.decision),
  body("四个方向是同一研究纲领的方法任务，不代表四个新理论，也不表示外部首创性或科学有效性已经确立。"),
  ...data.sources.map((source) => para([
    run(`${source.id}：`, { bold: true, size: 17 }),
    run(`${source.path}；SHA-256 ${source.sha256}（只读）。`, { size: 17 }),
  ], { spacing: { after: 90, line: 230 } })),
  makeTable(
    ["方向与角色", "已闭合的局部审计", "未竟工作与下一步"],
    data.directions.map((row) => [`${row.id}：${row.role}`, row.closed, `${row.unfinished} 下一步：${row.next}`]),
    [3000, 2700, 3806],
  ),

  heading(titles[1]),
  citedBody("原文同位素公式缺少温度与质量比。以下使用标准分式，并将每组温度、压力和来源绑定后再比较。", 1),
  isotopeEquation(),
  makeTable(
    ["温度对", "压力", "复算 α", "证据裁决"],
    [
      [`原文 LaH₁₀：${iso.printed_lah10.tc_h}/${iso.printed_lah10.tc_d} K`, `${iso.printed_lah10.pressure_gpa} GPa`, iso.printed_lah10.alpha.toFixed(15), "不是文中 0.46，需核对温度对来源"],
      [`Durajski LaH₁₀：${iso.durajski_lah10.tc_h}/${iso.durajski_lah10.tc_d} K`, `约 ${iso.durajski_lah10.pressure_gpa} GPa`, iso.durajski_lah10.alpha.toFixed(15), "与原文报告约 0.46 对应"],
      [`H₃S：${iso.h3s.tc_h}/${iso.h3s.tc_d} K`, `${iso.h3s.pressure_gpa} GPa`, iso.h3s.alpha.toFixed(15), "落在原表 0.3–0.6 范围"],
    ],
    [2700, 1400, 2500, 2906],
  ),
  citedBody(`Durajski 使用约 150 GPa 的 ${iso.durajski_lah10.tc_h}/${iso.durajski_lah10.tc_d} K，复算 α＝${iso.durajski_lah10.alpha.toFixed(15)}，与其约 0.46 的报告对应；不能用原表 240/168 K 拼接该系数。`, 2),
  body("同位素系数支持电子-声子机制，但不能单独排他证明全部微观机制。后续必须绑定同压力 H/D 温度、结构相、样品和原始图号。"),

  heading(titles[2]),
  citedBody("Kruglov 正确书目为 Phys. Rev. B 101, 024508，原文写成 224508。表 1 的 271 K 星号明确标为 SCDFT，其余表内点为 Eliashberg。", 3),
  makeTable(
    ["压力段（GPa）", "方法", "复算斜率（K/GPa）", "证据边界"],
    pressure.rows.map((row) => [
      `${row.pressure_interval_gpa[0]}→${row.pressure_interval_gpa[1]}`,
      row.methods.join("→"),
      `${row.slope >= 0 ? "+" : ""}${row.slope.toFixed(3)}`,
      row.crosses_method_boundary ? "跨方法" : "同方法，但仍是理论点",
    ]),
    [1900, 2800, 2300, 2506],
  ),
  para(new ImageRun({
    type: "png",
    data: fs.readFileSync(path.join(audit, data.figure.png)),
    transformation: { width: 610, height: Math.round(610 * 1584 / 2816) },
  }), { alignment: AlignmentType.CENTER, keepNext: true }),
  para(run(`${data.figure.caption}。图件位于压力斜率表之后、结果解释之前；不含实验验证百分比。`, { size: 19, italics: true }), {
    alignment: AlignmentType.CENTER,
  }),
  body("三个斜率的算术均正确；问题是前两段跨方法，整组不是完整实验 Tc(P) 曲线。后续应分别输出 Eliashberg、SCDFT 与实验曲线，只在方法一致时求导。"),

  heading(titles[3]),
  citedBody("多层 DFT 资料提供的是方法框架，不是六层环体已经可计算的证明。大超胞不自动需要更密集 k 点，通用截断能和 r2SCAN<1% 也不是跨材料保证。", 4),
  makeTable(
    ["项目", "已核实角色", "未竟工作"],
    [
      ["大超胞与 k 点", "不自动需要更密集 k 点", "用倒空间间距和收敛曲线决定网格"],
      ["通用参数", "r2SCAN<1%、截断能和阈值不是跨材料保证", "绑定赝势、k/q、能量、力与声子收敛日志"],
      ["JARVIS 数据", `既有 ${jarvis.previous_zero_pressure_bulk}+ 块体和 ${jarvis.previous_zero_pressure_2d}+ 2D 零压数据真实；新增 ${jarvis.new_hydride_count_label}、${jarvis.new_pressure_range_gpa[0]}–${jarvis.new_pressure_range_gpa[1]} GPa、${jarvis.stable_candidates} 个候选`, "两类数据不得混成同一训练或评价口径"],
      ["1000 倍加速", `DFT ${jarvis.dft_core_hours} core hours；训练 ${jarvis.training_gpu_hours[0]}/${jarvis.training_gpu_hours[1]} GPU hours；无端到端 1000 倍基准`, "补推理成本、硬件、任务定义和外部测试"],
      ["NdNiO₂/KTaO₃", `本次 ${nickelate.search_result_count} 条检索未找到精确支持 4–8 层穹顶的来源`, "标未解析并补 DOI／图号，不判其为假"],
      ["六层环体", "尚无可计算定义", "先定义结构、层间耦合、边界条件和化学式，再生成输入"],
    ],
    [1900, 4400, 3206],
  ),
  citedBody(`JARVIS 的既有零压数据与新增高压氢化物数据均已核实。DFT 约 ${jarvis.dft_core_hours} core hours，训练约 ${jarvis.training_gpu_hours[0]}/${jarvis.training_gpu_hours[1]} GPU hours；这些不是端到端 1000 倍加速的替代证明。`, 5),
  citedBody(`镍酸盐查询“${nickelate.query}”返回 ${nickelate.search_result_count} 条结果，未找到精确支持 4–8 层穹顶的来源；该否定仅限本次检索范围。`, 6),

  heading(titles[4]),
  makeTable(
    ["级别", "已观察问题", "建议动作"],
    data.corrections.map((row) => [row.severity, row.finding, row.action]),
    [900, 4400, 4206],
  ),
  bodyAfterTable("优先顺序：先清偿同位素和书目血缘，再建立方法一致的压力曲线；随后完成最小多层结构的收敛切片与 ML 成本基准。四个方向是同一研究纲领的方法任务。"),

  heading(titles[5]),
  makeTable(
    ["边界", "状态", "含义"],
    Object.entries(data.open_boundaries).map(([key, value]) => [key, String(value), "当前未完成，不得由资料表、局部复算或检索结果推定完成。"]),
    [3700, 1000, 4806],
  ),
  bodyAfterTable("本批使用冻结哈希、原始 PDF、Scholar 检索和独立数值复算。命令与退出码见 run.log；Word 逐页结果见 word-qa/report.json。"),
  body("本批没有重跑计算、训练或实验，没有修改两份原文。全库审计尚未完成。"),
];

const document = new Document({
  creator: "TOE-SYLVA",
  title: "同位素压力与多层 DFT：参数血缘、方法分轨与未竟工作审计",
  description: "同位素参数血缘、方法一致压力曲线、可复现 DFT 与机器学习基准治理。",
  features: { updateFields: true },
  styles: {
    paragraphStyles: [1, 2].map((level) => ({
      id: `TOC${level}`,
      name: `TOC ${level}`,
      basedOn: "Normal",
      next: "Normal",
      quickFormat: true,
      run: { font, size: 20, color: palette.dark },
      paragraph: { spacing: { after: 80, line: 250 }, indent: { left: (level - 1) * 360 } },
    })),
  },
  footnotes: {
    1: { children: [para(run("TOE-SYLVA read-only source: organized/17-资料收集-同位素效应与压力导数.md. The printed isotope formula and temperature pairs are audited, not edited.", { size: 18 }))] },
    2: { children: [para(run("Durajski et al., Isotope effect in superconducting lanthanum hydride under high compression, arXiv:1912.09663; Phys. Rev. B 101, 214501. Source pair: 249/180 K near 150 GPa.", { size: 18 }))] },
    3: { children: [para(run(`Kruglov et al., Superconductivity of LaH10 and LaH16 polyhydrides, Phys. Rev. B 101, 024508. DOI ${data.evidence.bibliography.doi}. Table 1 marks 271 K as SCDFT.`, { size: 18 }))] },
    4: { children: [para(run("TOE-SYLVA read-only source: organized/19-资料收集-多层结构DFT参数.md. Generic workflow only; six-layer-ring input is not defined.", { size: 18 }))] },
    5: { children: [para(run(`Wines and Choudhary, Data-driven design of high pressure hydride superconductors using DFT and deep learning, arXiv:${jarvis.arxiv}. ${jarvis.url}`, { size: 18 }))] },
    6: { children: [para(run(`Scholar search evidence: sources/nickelate-dome-scholar.csv; query “${nickelate.query}”; ${nickelate.search_result_count} returned rows. Absence is limited to this search scope.`, { size: 18 }))] },
  },
  sections: [{
    properties: { page: { margin: { top: 1200, bottom: 1200, left: 1200, right: 1200 } } },
    headers: {
      default: new Header({
        children: [para(run("TOE-SYLVA · 同位素压力与多层 DFT · 证据边界", { size: 18, color: palette.primary }), {
          alignment: AlignmentType.CENTER,
        })],
      }),
    },
    footers: {
      default: new Footer({
        children: [para(new TextRun({ children: [PageNumber.CURRENT], font, size: 18 }), {
          alignment: AlignmentType.CENTER,
        })],
      }),
    },
    children,
  }],
});

fs.writeFileSync(outputPath, await Packer.toBuffer(document));
