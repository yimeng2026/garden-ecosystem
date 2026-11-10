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
  margins: { top: 20, bottom: 20, left: 80, right: 80 },
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
const exponentEquation = () => para(new MathEquation({ children: [
  new MathRun("f(λ, μ*) = "),
  new MathFraction({
    numerator: [new MathRun("1.04(1 + λ)")],
    denominator: [new MathRun("λ − μ*(1 + 0.62λ)")],
  }),
] }), { alignment: AlignmentType.CENTER, spacing: { before: 100, after: 100 } });
const tcEquation = () => para(new MathEquation({ children: [
  sub("T", "c"), new MathRun(" = "),
  new MathFraction({ numerator: [sub("Θ", "D")], denominator: [new MathRun("1.45")] }),
  new MathRun(" exp(−f(λ, μ*))"),
] }), { alignment: AlignmentType.CENTER, spacing: { before: 80, after: 160 } });

const bad = data.evidence.formula4;
const good = data.evidence.correct_example;
const threshold = data.evidence.threshold_lambda25;
const units = data.evidence.units;
const conditions = data.evidence.conditions;
const experiment = data.evidence.experiment;
const intro = data.evidence.intro;
const titles = [
  "一、血缘裁决与四个发展方向",
  "二、公式 4 与正确示例：参数不能混用",
  "三、实验角色与频率单位",
  "四、入门教学与分档勘误",
  "五、验证范围与开放边界",
];
const children = [
  para(run("手册第 1–3 章", { bold: true, size: 38, color: palette.dark }), {
    heading: HeadingLevel.TITLE,
    alignment: AlignmentType.CENTER,
    spacing: { before: 620, after: 230 },
  }),
  para(run("教学边界、参数复算与未竟工作审计", { bold: true, size: 30, color: palette.primary }), {
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
  toc(titles.map((title, index) => ({ title, level: 1, page: [2, 2, 3, 4, 5][index] }))),
  new Paragraph({ children: [new PageBreak()] }),

  heading(titles[0]),
  body(data.source_lineage.decision),
  body("四个方向是同一研究纲领的方法任务，不是四个新理论，也不表示外部首创性或科学有效性已经确立。"),
  ...data.sources.map((source) => para([
    run(`${source.id}：`, { bold: true, size: 16 }),
    run(`${source.path}；SHA-256 ${source.sha256}（只读）。`, { size: 16 }),
  ], { spacing: { after: 70, line: 220 } })),
  makeTable(
    ["方向与角色", "已闭合的局部审计", "未竟工作与下一步"],
    data.directions.map((row) => [`${row.id}：${row.role}`, row.closed, `${row.unfinished} 下一步：${row.next}`]),
    [3000, 2700, 3806],
  ),

  heading(titles[1]),
  citedBody("第 3 章把简化 McMillan 公式用于普遍必然性。以下先按同一公式复算具体参数，再讨论其物理适用域。", 1),
  exponentEquation(),
  tcEquation(),
  makeTable(
    ["参数组", "文中值（K）", "独立复算（K）", "裁决"],
    [
      [`公式 4：λ=2.5、μ*=0.15、Θ_D=2100 K`, String(bad.claimed_tc_k), bad.computed_tc_k.toFixed(12), "文中值错误"],
      [`正确示例：λ=3.6、μ*=0.12、Θ_D=2100 K`, String(good.claimed_tc_k), good.computed_tc_k.toFixed(12), "近似值可保留"],
      [`λ=2.5、μ*=0.15 的 Θ_D 阈值`, String(threshold.claimed_theta_d_k), threshold.computed_theta_d_k.toFixed(12), "约 2427 K 的算术正确"],
    ],
    [3400, 1600, 2500, 2006],
  ),
  para(new ImageRun({
    type: "png",
    data: fs.readFileSync(path.join(audit, data.figure.png)),
    transformation: { width: 610, height: Math.round(610 * 1584 / 2816) },
  }), { alignment: AlignmentType.CENTER, keepNext: true }),
  para(run(`${data.figure.caption}。图件位于数值复算表之后、结果解释之前；不含验证百分比。`, { size: 19, italics: true }), {
    alignment: AlignmentType.CENTER,
  }),
  body("这些结果只适用于指定简化公式和参数域。原“三条件”与定理条件并不等价，准二维也没有进入证明，因此不能称为普遍物理必然性。可保留的是指定模型的参数充分条件。"),
  citedBody("BCS 与 McMillan 的原始文献支持相干配对组态和特定模型／经验参数分析，不支持把库珀对简单当成独立玻色子，也不支持所有材料统一的 30–40 K 数学上限。", 2),

  heading(titles[2]),
  makeTable(
    ["项目", "已核实结果", "证据边界"],
    [
      ["Song", `onset 上限 ${experiment.song_onset_max_k} K，低于 300 K`, "直接 Meissner、独立正向复现未确立；Semenok 负向复现不能省略"],
      ["210 meV", `${units.omega_210_mev_k.toFixed(6)} K`, "若与 Θ_D 是同一最大频率，不是 2100 K；若 Θ_D 是另一有效量，单列定义和来源"],
      ["150 meV", `${units.omega_150_mev_k.toFixed(6)} K`, "不与项目 300 K 必然性阈值混用"],
      ["作者与结构", "Liu 与 Song 署名不统一；P6/mmm 不自动等于准二维", "统一来源，准二维需各向异性证据"],
    ],
    [1700, 4200, 3606],
  ),
  citedBody(`Song 的 onset 上限为 ${experiment.song_onset_max_k} K，低于 300 K；直接 Meissner 和独立正向复现未确立，Semenok 的七次未成功必须并列保留。`, 3),
  citedBody("理论框架审计已定位原三条件与定理条件的差异：λ>2 与 λ≥2.5、ℏω>150 meV 与 Θ_D≥1800 K、准二维未进入证明，不能把它们视为等价命题。", 4),

  heading(titles[3]),
  body(`1986 年镧钡铜氧为 ${intro.year_1986_tc_k} K，仍低于液氮 ${intro.liquid_nitrogen_k} K；1987 年 YBCO 为 ${intro.year_1987_tc_k} K 才超过液氮。H₂S 应统一为 ${intro.correct_chemical_formula}。`),
  body("BCS 是由正常态和虚拟配对组态构成的相干基态，不是简单的独立玻色子气体。McMillan 的“最大 Tc”属于特定模型与历史经验背景，不是所有材料统一的 30–40 K 数学上限。"),
  makeTable(
    ["级别", "已观察问题", "建议动作"],
    data.corrections.map((row) => [row.severity, row.finding, row.action]),
    [900, 4400, 4206],
  ),
  bodyAfterTable("可发展的方向不是删除教学，而是把类比、近似、公式和实验各归其位：入门章提供物理直觉，条件章只证明简化模型内的结论，实验章同时呈现正负证据。"),

  heading(titles[4]),
  makeTable(
    ["边界", "状态", "含义"],
    Object.entries(data.open_boundaries).map(([key, value]) => [key, String(value), "当前未完成，不得由教学叙事、局部复算或单一预印本推定完成。"]),
    [3700, 1000, 4806],
  ),
  bodyAfterTable("本批使用六项冻结来源、原始理论文献和独立数值复算。命令与退出码见 run.log；Word 逐页结果见 word-qa/report.json。其余入门事实未全审。"),
  body("本批没有重跑计算或实验，没有闭合 Θ_D 原始谱，没有修改两章原文。全库审计尚未完成。"),
];

const document = new Document({
  creator: "TOE-SYLVA",
  title: "手册第 1–3 章：教学边界、参数复算与未竟工作审计",
  description: "BCS 教学、简化模型充分条件、实验角色与单位血缘。",
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
    1: { children: [para(run("TOE-SYLVA read-only sources: organized/08-手册章节/01-第1-2章_超导入门与科普.md and organized/08-手册章节/02-第3章_必然性定理.md. Formula and narrative roles audited separately.", { size: 18 }))] },
    2: { children: [para(run("Bardeen, Cooper and Schrieffer, Theory of Superconductivity, Phys. Rev. 108, 1175 (1957), DOI 10.1103/PhysRev.108.1175; McMillan, Transition Temperature of Strong-Coupled Superconductors, Phys. Rev. 167, 331 (1968), DOI 10.1103/PhysRev.167.331.", { size: 18 }))] },
    3: { children: [para(run("Y. Song et al., Room-Temperature Superconductivity at 298 K in Ternary La-Sc-H System at High-pressure Conditions, arXiv:2510.01273; D. V. Semenok et al., independent negative replication preprint, arXiv:2605.29985. See main-claims/review.json.", { size: 18 }))] },
    4: { children: [para(run("Prior theory audit: theory-breakthrough/review.json. Original three conditions differ from the theorem's actual parameter set; quasi-2D is not used in the proof.", { size: 18 }))] },
    5: { children: [para(run("Prior data-governance audit: data-governance/review.json. Repeated summaries do not establish independent confirmation; direct Meissner and first-four-criteria completion remain unsupported.", { size: 18 }))] },
    6: { children: [para(run("Prior numerical evidence: main-claims/review.json, critical_manifold results. Simplified formula anchors constrain only the same simplified model, not full Eliashberg theory or a specific material.", { size: 18 }))] },
  },
  sections: [{
    properties: { page: { margin: { top: 1200, bottom: 1200, left: 1200, right: 1200 } } },
    headers: {
      default: new Header({
        children: [para(run("TOE-SYLVA · 手册第 1–3 章 · 证据边界", { size: 18, color: palette.primary }), {
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
