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
  spacing: { after: 140, line: 290 },
  ...options,
  children: Array.isArray(children) ? children : [children],
});
const body = (text, options = {}) => para(run(text), { indent: { firstLine: 420 }, ...options });
const bodyAfterTable = (text) => body(text, { spacing: { before: 180, after: 140, line: 290 } });
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
  children: [para(run(text, { size: 17, bold: header }), { spacing: { after: 0, line: 230 } })],
  width: { size: widths[index], type: WidthType.DXA },
  margins: { top: 90, bottom: 90, left: 90, right: 90 },
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
const temperatureEquation = () => para(new MathEquation({ children: [
  sub("T", "c"),
  new MathRun(" = "),
  new MathFraction({ numerator: [sub("ω", "log")], denominator: [new MathRun("1.2")] }),
  new MathRun(" exp(E)"),
] }), { alignment: AlignmentType.CENTER, spacing: { before: 120, after: 120 } });
const exponentEquation = () => para(new MathEquation({ children: [
  new MathRun("E = −"),
  new MathFraction({
    numerator: [new MathRun("1.04(1 + λ)")],
    denominator: [new MathRun("λ − μ*(1 + 0.62λ)")],
  }),
] }), { alignment: AlignmentType.CENTER, spacing: { before: 80, after: 180 } });

const formula = data.evidence.formula_spotcheck;
const lanio2 = data.evidence.lanio2;
const grockowiak = data.evidence.grockowiak;
const cl = data.evidence.cl_doping;
const titles = [
  "一、血缘裁决与四个问题族",
  "二、公式链：文中值与文中公式复算值",
  "三、LaNiO₂：样品与掺杂范围",
  "四、556 K：高阶氢化物的证据角色",
  "五、验证百分比与星级：治理边界",
  "六、分档勘误与未竟工作",
  "七、验证范围",
];
const children = [
  para(run("实验验证与材料预测", { bold: true, size: 38, color: palette.dark }), {
    heading: HeadingLevel.TITLE,
    alignment: AlignmentType.CENTER,
    spacing: { before: 620, after: 230 },
  }),
  para(run("证据角色、公式链与未竟工作审计", { bold: true, size: 30, color: palette.primary }), {
    alignment: AlignmentType.CENTER,
    spacing: { after: 300 },
  }),
  para(run("一个研究纲领 · 四个方法问题族 · 只读审计", { size: 22, color: palette.light }), {
    alignment: AlignmentType.CENTER,
    spacing: { after: 240 },
  }),
  para(run("2026-11-10　不修改原文、不替换预测、不新增实验", { size: 20 }), {
    alignment: AlignmentType.CENTER,
    spacing: { after: 360 },
  }),
  heading("目录"),
  para(run("以下页码为可见缓存；在 Word/WPS 中更新域可刷新。", { size: 18, italics: true, color: palette.light })),
  toc(titles.map((title, index) => ({ title, level: 1, page: [2, 2, 3, 3, 4, 4, 4][index] }))),
  new Paragraph({ children: [new PageBreak()] }),

  heading(titles[0]),
  body(data.source_lineage.decision),
  body("四个方法问题族代表可继续发展的审计与验证方向，但不是四个独立新理论，也不意味着其外部首创性或科学有效性已经确立。"),
  ...data.sources.map((source) => para([
    run(`${source.id}：`, { bold: true, size: 17 }),
    run(`${source.path}；SHA-256 ${source.sha256}（只读）。`, { size: 17 }),
  ], { spacing: { after: 90, line: 230 } })),
  makeTable(
    ["问题族与角色", "已闭合的局部审计", "未竟工作与下一步"],
    data.directions.map((row) => [`${row.id}：${row.role}`, row.closed, `${row.unfinished} 下一步：${row.next}`]),
    [3000, 2700, 3806],
  ),

  heading(titles[1]),
  citedBody("文中简化公式如下；以下复算使用冻结的 numeric_spotcheck.py，只核对表内参数、公式与结果的一致性。", 1),
  temperatureEquation(),
  exponentEquation(),
  makeTable(
    ["条目", "ωlog（K）", "λ", "μ*", "文中 Tc（K）", "文中公式复算（K）"],
    [formula.h3s, formula.h_s_cl].map((row, index) => [
      index === 0 ? "H3S" : "H-S-Cl",
      String(row.omega_log_k),
      String(row.lambda),
      String(row.mu_star),
      String(row.claimed_tc_k),
      row.computed_tc_k.toFixed(6),
    ]),
    [1050, 1350, 800, 900, 2200, 3206],
  ),
  para(new ImageRun({
    type: "png",
    data: fs.readFileSync(path.join(audit, data.figure.png)),
    transformation: { width: 610, height: Math.round(610 * 5.2 / 9.4) },
  }), { alignment: AlignmentType.CENTER, keepNext: true }),
  para(run(`${data.figure.caption}。图件位于公式复算表之后、结果解释之前。`, { size: 19, italics: true }), {
    alignment: AlignmentType.CENTER,
  }),
  body("复算只证明参数—公式—结果不一致，不能替代 Allen–Dynes 修正、Eliashberg 求解或第一性原理计算。必须补齐 f1/f2、ω2/ωlog、参数来源、压力、掺杂结构和原始输入输出。"),
  citedBody(`独立第一性原理研究报告：200 GPa 下 6.25% Cl→${cl.results[0].tc_k} K、12.5% Cl→${cl.results[1].tc_k} K。Cl 掺杂削弱超导但降低稳定压力，与 20% Cl→320 K 的提升推断不相容。`, 2),

  heading(titles[2]),
  citedBody(`原文摘要明确：未掺杂和低掺杂 La1−xCaxNiO2 薄膜从 300 K 到 2 K 均绝缘，超导穹顶位于 ${lanio2.superconducting_dome[0]} < x < ${lanio2.superconducting_dome[1]}。因此未掺杂薄膜绝缘，不能把 LaNiO₂ 写成 20–40 K 已验证超导体。`, 3),
  body("后续每个材料结论必须绑定化学式、掺杂元素、掺杂范围、薄膜形态、输运证据和原始图号；不能将掺杂样品的结论继承给未掺杂母体。"),

  heading(titles[3]),
  citedBody(`Grockowiak 等原文报告初始 ${grockowiak.initial_tc_k} K，后续热循环使 onset 不可逆达到 ${grockowiak.maximum_onset_tc_k} K。原文描述扭曲 LaH₁₀ 骨架及取代形成高阶化合物，并明确缺少 Meissner 和可靠高温 H–T 相图，还存在非零电阻和混合相。`, 4),
  body("因此这篇论文不能被删除或称为虚构，但也不能并入二元 LaH₁₀ 的常规验证百分比。后续需要独立复现、成分与相确定、直接磁测量、热力学平衡和原始样品路径核对。"),

  heading(titles[4]),
  body(data.evidence.scoring.role + "。92%、88%、45%、9.5/10 和星级没有公开指标定义、权重、样本集、误差模型或复算公式。若保留，只能标为主观研究治理标签；建立公开评分卡后才可以量化。"),

  heading(titles[5]),
  makeTable(
    ["级别", "已观察问题", "建议动作"],
    data.corrections.map((row) => [row.severity, row.finding, row.action]),
    [900, 4400, 4206],
  ),
  bodyAfterTable("真正的未竟工作不是再写一组更高 Tc，而是建立原始输入、参数、修正因子、样品身份、独立复现和可复算评分卡之间的闭环。"),

  heading(titles[6]),
  makeTable(
    ["边界", "状态", "含义"],
    Object.entries(data.open_boundaries).map(([key, value]) => [key, String(value), "当前未完成，不得由局部复算、原文措辞或文档存在推定完成。"]),
    [3700, 1000, 4806],
  ),
  bodyAfterTable("本批使用冻结哈希、原始出版商／PMC／arXiv 来源和独立公式复算。命令、退出码见 run.log；Word 逐页结果见 word-qa/report.json。"),
  body("本批没有重跑第一性原理、没有替换材料预测、没有新做实验或独立复现、没有修改两份原文。全库审计尚未完成。"),
];

const document = new Document({
  creator: "TOE-SYLVA",
  title: "实验验证与材料预测：证据角色、公式链与未竟工作审计",
  description: "同一研究纲领的四个方法问题族，公式、掺杂、高阶氢化物与验证治理的证据边界。",
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
    1: { children: [para(run("TOE-SYLVA frozen arithmetic check: validation-materials/numeric_spotcheck.py. Scope: printed formula and printed parameters only; not a first-principles calculation.", { size: 18 }))] },
    2: { children: [para(run("First-principles study of Cl-doped H3S, arXiv:1804.08224v3. https://arxiv.org/html/1804.08224v3", { size: 18 }))] },
    3: { children: [para(run("Superconducting dome in La1−xCaxNiO2 thin films, PMC8856608. https://pmc.ncbi.nlm.nih.gov/articles/PMC8856608/", { size: 18 }))] },
    4: { children: [para(run(`Grockowiak et al. Frontiers in Electronic Materials, DOI ${grockowiak.doi}. ${grockowiak.source_url}`, { size: 18 }))] },
  },
  sections: [{
    properties: { page: { margin: { top: 1200, bottom: 1200, left: 1200, right: 1200 } } },
    headers: {
      default: new Header({
        children: [para(run("TOE-SYLVA · 实验验证与材料预测 · 证据边界", { size: 18, color: palette.primary }), {
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
