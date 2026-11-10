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
const unitsEquation = () => para(new MathEquation({ children: [
  sub("N", "F"), new MathRun("：states/f.u./Ry（不是 states/eV/f.u.）"),
] }), { alignment: AlignmentType.CENTER, spacing: { before: 100, after: 100 } });
const thresholdEquation = () => para(new MathEquation({ children: [
  sub("T", "c"), new MathRun(" > 273 K   与   "), sub("T", "c"), new MathRun(" > 300 K：不是同一验证口径"),
] }), { alignment: AlignmentType.CENTER, spacing: { before: 80, after: 160 } });

const song = data.evidence.song;
const htsc = data.evidence.htsc;
const validation = data.evidence.validation;
const boron = data.evidence.boron;
const kruglov = data.evidence.kruglov;
const dmrg = data.evidence.research_update.dmrg;
const qec = data.evidence.research_update.qec;
const titles = [
  "一、血缘裁决与四个发展方向",
  "二、Song 循环确认与 HTSC 真实范围",
  "三、可发展的研究方向及其边界",
  "四、分档勘误与数据治理任务",
  "五、验证范围与开放边界",
];
const children = [
  para(run("总览与技术复盘", { bold: true, size: 38, color: palette.dark }), {
    heading: HeadingLevel.TITLE,
    alignment: AlignmentType.CENTER,
    spacing: { before: 620, after: 230 },
  }),
  para(run("事实血缘、基准范围与未竟工作审计", { bold: true, size: 30, color: palette.primary }), {
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
  ], { spacing: { after: 60, line: 220 } })),
  makeTable(
    ["方向与角色", "已闭合的局部审计", "未竟工作与下一步"],
    data.directions.map((row) => [`${row.id}：${row.role}`, row.closed, `${row.unfinished} 下一步：${row.next}`]),
    [3000, 2700, 3806],
  ),

  heading(titles[1]),
  citedBody("第 12 份资料把 Song、HTSC、五项标准和 B–C 汇总，但总览中的归类必须与原始证据一致。", 1),
  makeTable(
    ["项目", "总览中的问题", "原始证据裁决"],
    [
      ["Song", "四探针＋迈斯纳、前四项满足", "onset 271–298 K；直接 Meissner 和独立正向复现未确立；重复总览不构成独立证据"],
      ["HTSC", "常压基准与 300 GPa 候选混写", `${htsc.sample_count} 个样本；平均 ${htsc.average_tc_k} K；最高 ${htsc.maximum_tc_k} K；高压和非 BCS 排除`],
      ["Li₂NaH₁₇", "资料写 340 K，HTSC 讨论写 297 K", "明确不纳入 HTSC；Jiang 原始值待核，本批不擅断哪个值正确"],
      ["五项标准", "二手博客被当成全球共识", `Patsnap 可作内部清单；${validation.blog_threshold_k} K 与项目 ${validation.project_theorem_threshold_k} K 不混用`],
    ],
    [1700, 3400, 4406],
  ),
  citedBody(`HTSC-2025 原文包含 ${htsc.sample_count} 个样本、平均 ${htsc.average_tc_k} K、最高 ${htsc.maximum_tc_k} K，明确要求去泄漏，并排除高压和非 BCS 体系；开放数据可用。`, 2),
  thresholdEquation(),
  citedBody(`Patsnap 的五项标准只作为二手博客框架，${validation.blog_threshold_k} K 与项目 ${validation.project_theorem_threshold_k} K 不是同一验证口径；具体材料必须逐项回源。`, 3),
  citedBody("第 16 份总览进一步写成“LaSc₂H₂₄ 满足前四项”，与直接 Meissner 和三个独立团队复现未确立相冲突。", 4),
  citedBody("第 20 份完整清单重复“四探针＋迈斯纳”和 Google 首次等说法，因此必须按同一证据卡同步勘误，而不是把重复当成确认。", 5),
  body("HTSC 的开放数据、去泄漏训练划分和 BCS 快速验证流程值得保留。后续应分开常压基准与高压候选，公开失败案例和外部 DFT 验证。"),

  heading(titles[2]),
  citedBody("第 21 份技术复盘提供数据矩阵和缺口清单，但有表格不等于完整谱、完整输入或可复现结果。", 6),
  makeTable(
    ["方向", "已核实进展", "未竟工作"],
    [
      ["B–C 笼状结构", `${boron.compound_count} 个化合物；CaB₈C 预测 ${boron.ca_b8c_predicted_tc_k} K`, "不是实验实现，需要合成与输运验证"],
      ["Chen DMRG", `${dmrg.chen_legs}-leg 基态 d 波；公开代码数据`, "更宽系统与无限二维极限未闭合"],
      ["Kruglov／压力", "文章号 024508；N_F 为 states/f.u./Ry；斜率算术成立", "方法混用，不是纯实验曲线；全谱和输入未开放"],
      ["Google／中性原子", "63 μs 实时解码；48×3D [[8,3,2]]", "不写绝对首次，不写 48×distance-7 LDPC"],
    ],
    [1900, 4400, 3206],
  ),
  para(new ImageRun({
    type: "png",
    data: fs.readFileSync(path.join(audit, data.figure.png)),
    transformation: { width: 610, height: Math.round(610 * 1584 / 2816) },
  }), { alignment: AlignmentType.CENTER, keepNext: true }),
  para(run(`${data.figure.caption}。图件位于证据角色表之后、结果解释之前；不含验证百分比。`, { size: 19, italics: true }), {
    alignment: AlignmentType.CENTER,
  }),
  citedBody(`Song 的作者正向预印本必须保留，但直接 Meissner、独立正向复现和同行评议未确立；多份总览重复不能形成独立确认。`, 7),
  unitsEquation(),
  citedBody("Kruglov 的正确文章号为 024508，N_F 为 states/f.u./Ry；压力斜率跨 Eliashberg／SCDFT，不是纯实验曲线。", 8),
  citedBody(`PRB 111, 014510 的 ${boron.compound_count} 个化合物筛选中，CaB₈C 的最高预测 Tc 为 ${boron.ca_b8c_predicted_tc_k} K，属于第一性原理预测而非实验实现。`, 9),
  citedBody("DMRG 应更新为 Chen 8-leg 基态进展和公开代码数据，同时保留二维极限未闭合；QEC 则按 Google 后续里程碑和中性原子 48×3D [[8,3,2]] 同步修正。", 10),
  body("所有研究方向都可以继续，但必须按预测、作者报告、独立复现和工程实现分级更新。B–C 需要实验，Chen 需要更宽系统，Floquet 需要实验验证，涡旋量子比特需要物理实现协议。"),

  heading(titles[3]),
  makeTable(
    ["级别", "已观察问题", "建议动作"],
    data.corrections.map((row) => [row.severity, row.finding, row.action]),
    [900, 4400, 4206],
  ),
  bodyAfterTable("数据矩阵的完整性不再以“有表格”判断，而以原始谱、结构、输入、日志、单位和不确定度判断。归档只表示文件存在，重复总览只表示同一结论被复制，均不等于验证。"),

  heading(titles[4]),
  makeTable(
    ["边界", "状态", "含义"],
    Object.entries(data.open_boundaries).map(([key, value]) => [key, String(value), "当前未完成，不得由总览、重复引用或局部预测推定完成。"]),
    [3700, 1000, 4806],
  ),
  bodyAfterTable("本批使用十二项冻结来源、HTSC 原文、Patsnap 与 PRB 摘要及既有审计对象。命令与退出码见 run.log；Word 逐页结果见 word-qa/report.json。"),
  body("本批没有重跑计算或实验，没有核实 Jiang 原始值，没有修改四份原文。全库审计尚未完成。"),
];

const document = new Document({
  creator: "TOE-SYLVA",
  title: "总览与技术复盘：事实血缘、基准范围与未竟工作审计",
  description: "原始证据、单篇审计和多份总览之间的纠错传播与数据治理。",
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
    1: { children: [para(run("TOE-SYLVA read-only source: organized/12-资料收集-氢化物与验证进展.md. Song, HTSC, Patsnap and B–C are re-evaluated by evidence role.", { size: 18 }))] },
    2: { children: [para(run(`HTSC-2025: A Benchmark Dataset of Ambient-Pressure High-Temperature Superconductors for AI-Driven Critical Temperature Prediction, arXiv:${htsc.arxiv}. 140 samples, mean 27.3 K, maximum 160 K; open data: ${htsc.open_data_url}`, { size: 18 }))] },
    3: { children: [para(run("Patsnap Research Landscape 2026, secondary blog excerpt. Five criteria are useful as an internal checklist, not proof of a universal consensus. Source: sources/patsnap-excerpts.md", { size: 18 }))] },
    4: { children: [para(run("TOE-SYLVA read-only source: organized/16-资料收集-总览与下一步.md. The claim that LaSc₂H₂₄ meets the first four criteria is not supported.", { size: 18 }))] },
    5: { children: [para(run("TOE-SYLVA read-only source: organized/20-资料收集-总览与完整清单.md. Repeated summaries are not independent evidence.", { size: 18 }))] },
    6: { children: [para(run("TOE-SYLVA read-only source: organized/21-技术复盘-全领域数据审计.md. Tables alone do not establish complete spectra, inputs or reproducibility.", { size: 18 }))] },
    7: { children: [para(run("Y. Song et al., Room-Temperature Superconductivity at 298 K in Ternary La-Sc-H System at High-pressure Conditions, arXiv:2510.01273. Author-reported positive preprint; direct Meissner and independent positive replication are not established in the audited evidence.", { size: 18 }))] },
    8: { children: [para(run("Kruglov et al., Phys. Rev. B 101, 024508, DOI 10.1103/PhysRevB.101.024508. Table 1: Nf states/f.u./Ry; 271 K is SCDFT, other tabulated points Eliashberg.", { size: 18 }))] },
    9: { children: [para(run("Li et al., Prediction of high-temperature ambient-pressure superconductivity in hexagonal boron-rich clathrates, Phys. Rev. B 111, 014510 (2025), DOI 10.1103/PhysRevB.111.014510. 96 compounds; CaB8C predicted 77.1 K.", { size: 18 }))] },
    10: { children: [para(run("Prior DMRG/QEC audit: dmrg-qec/review.json. Chen 8-leg ground-state result and open code/data; Google milestone and neutral-atom 48×3D [[8,3,2]] roles preserved with their stated limits.", { size: 18 }))] },
  },
  sections: [{
    properties: { page: { margin: { top: 1200, bottom: 1200, left: 1200, right: 1200 } } },
    headers: {
      default: new Header({
        children: [para(run("TOE-SYLVA · 总览与技术复盘 · 证据边界", { size: 18, color: palette.primary }), {
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
