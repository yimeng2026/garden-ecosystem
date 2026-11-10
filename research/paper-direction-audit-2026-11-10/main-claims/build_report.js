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
  MathSuperScript,
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
const citedBody = (text, footnoteId) => para([run(text), new FootnoteReferenceRun(footnoteId)], { indent: { firstLine: 420 } });
const heading = (text, level = 1) => para(run(text, { bold: true, size: level === 1 ? 30 : 26, color: palette.dark }), {
  heading: level === 1 ? HeadingLevel.HEADING_1 : HeadingLevel.HEADING_2,
  spacing: { before: 250, after: 140 },
  keepNext: true,
});
const xmlEscape = (value) => String(value)
  .replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;");
const toc = (entries) => {
  const cached = entries.map(({ title, level }) => `<w:p><w:pPr><w:pStyle w:val="TOC${level}"/>
    <w:tabs><w:tab w:val="right" w:leader="dot" w:pos="9000"/></w:tabs>
    <w:ind w:left="${Math.max(0, level - 1) * 360}"/></w:pPr>
    <w:r><w:t>${xmlEscape(title)}</w:t></w:r></w:p>`).join("");
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
const tcSimple = () => new MathSuperScript({
  children: [new MathSubScript({ children: [new MathRun("T")], subScript: [new MathRun("c")] })],
  superScript: [new MathRun("simple")],
});
const omegaLog = () => new MathSubScript({ children: [new MathRun("ω")], subScript: [new MathRun("log")] });
const temperatureEquation = () => para(new MathEquation({ children: [
  tcSimple(),
  new MathRun(" = "),
  new MathFraction({ numerator: [new MathRun("11.6 "), omegaLog()], denominator: [new MathRun("1.20")] }),
  new MathRun(" exp(−E)"),
] }), { alignment: AlignmentType.CENTER, spacing: { before: 120, after: 180 } });

const song = data.evidence.song;
const semenok = data.evidence.semenok;
const nature = data.evidence.nature_citation;
const critical = data.evidence.critical_manifold;
const lean = data.evidence.formalization;
const si = data.evidence.si;
const titles = [
  "一、总裁决",
  "二、四个方法方向",
  "三、LaSc₂H₂₄：证据时间线与争议结构",
  "四、Nature 引文错配：这是确定错误",
  "五、必然性命题：数值反例和证明债务",
  "六、手册叙事：哪些可以说，哪些不能说",
  "七、前批审计补充",
  "八、分档勘误与后续优先级",
  "九、验证范围",
];
const children = [
  para(run("主论文四版本与手册两章", { bold: true, size: 38, color: palette.dark }), {
    heading: HeadingLevel.TITLE,
    alignment: AlignmentType.CENTER,
    spacing: { before: 620, after: 230 },
  }),
  para(run("证据角色、实验争议与未竟工作审计", { bold: true, size: 30, color: palette.primary }), {
    alignment: AlignmentType.CENTER,
    spacing: { after: 300 },
  }),
  para(run("正向实验预印本与独立负向复现并存", { size: 22, color: palette.light }), {
    alignment: AlignmentType.CENTER,
    spacing: { after: 240 },
  }),
  para(run("2026-11-10　只读审计　不修改原文、不新增实验或材料预测", { size: 20 }), {
    alignment: AlignmentType.CENTER,
    spacing: { after: 360 },
  }),
  heading("目录"),
  toc(titles.map((title) => ({ title, level: 1 }))),
  new Paragraph({ children: [new PageBreak()] }),

  heading(titles[0]),
  body("当前不是“只有理论预测”，也不是“实验已经铁证完成”，而是正向实验预印本与独立负向复现并存。Song 的实验报告必须保留，Semenok 的负向结果同样必须保留；独立正向复现和同行评议尚未确立。"),
  body("四份主论文版本和两章手册属于同一研究纲领，不是六个新理论。本批形成必然性命题、可复现计算、实验争议和出版治理四个方法方向。"),
  ...data.sources.map((source) => para([
    run(`${source.id}：`, { bold: true, size: 17 }),
    run(`${source.path}；SHA-256 ${source.sha256}（只读）。`, { size: 17 }),
  ], { spacing: { after: 90, line: 230 } })),

  heading(titles[1]),
  makeTable(
    ["方向与角色", "已闭合的局部审计", "未竟工作与下一步"],
    data.directions.map((row) => [
      `${row.id}：${row.role}`,
      row.closed,
      `${row.unfinished} 下一步：${row.next}`,
    ]),
    [3200, 2700, 3606],
  ),

  heading(titles[2]),
  makeTable(
    ["来源与角色", "关键结果", "不能升级为"],
    [
      ["PNAS 121(26)／2024 理论预测", "167 GPa 最高 316 K；250 GPa 最高 331 K", "实验确认或后续实验的替代品"],
      [`Song／2025 正向实验预印本`, `作者报告 ${song.onset_tc_k[0]}–${song.onset_tc_k[1]} K／${song.pressure_gpa[0]}–${song.pressure_gpa[1]} GPa；${song.reproducible_runs_reported} 次可重复运行`, "独立正向复现、同行评议、直接 Meissner 或必然性证明"],
      [`Semenok／2026 独立负向复现预印本`, `${semenok.unsuccessful_attempts} 次合成未成功；${semenok.synthesis_pressure_gpa[0]}–${semenok.synthesis_pressure_gpa[1]} GPa 下未见 ${semenok.no_superconductivity_range_k[0]}–${semenok.no_superconductivity_range_k[1]} K 超导`, "对 Song 或整个材料族的最终逻辑否证"],
    ],
    [2600, 4000, 2906],
  ),
  citedBody("PNAS 的预测角色不变，但不能用 2024 预测替代后续实验证据。", 1),
  citedBody(`Song 作者报告零电阻、磁场抑制和 XRD，并把高于 200 GPa 的直接 Meissner 磁测量列为后续工作；${song.reproducible_runs_reported} 次可重复运行不等于给出总尝试分母。`, 2),
  citedBody(`Semenok 等报告 ${semenok.unsuccessful_attempts} 次未成功，同时仍讨论 300 GPa 下理论 Tc>300 K 和前驱体工程。`, 3),
  para(new ImageRun({
    type: "png",
    data: fs.readFileSync(path.join(audit, "claims-timeline.png")),
    transformation: { width: 610, height: 266 },
  }), { alignment: AlignmentType.CENTER, keepNext: true }),
  para(run("图 1　理论预测、实验宣称与独立负向复现：不是真伪投票。图件位于证据比较表之后、争议解释之前。", { size: 19, italics: true }), {
    alignment: AlignmentType.CENTER,
  }),
  body("正向与负向结果不支持简单投票式结论；下一步应核对前驱体有序化、原始数据和跨实验室正向复现。Semenok 的负向结果不是对 Song 或整个材料族的最终逻辑否证。"),

  heading(titles[3]),
  citedBody(`手册 [C1] 把 Nature 626, 779–784 写成 ${nature.claimed_title}。Crossref 的权威元数据表明该卷页实际是 ${nature.actual_title}，DOI ${nature.actual_doi}，主题是氮化硼陶瓷，不是 2024 年 Nature 论文所声称的 LaSc₂H₂₄ 工作。`, 4),
  body("后续原文修订应删除该错误引文并留痕，分别引用 PNAS 预测、Song 正向预印本和 Semenok 负向预印本。不得把 Song 的 2025 预印本倒填成 2024 Nature 论文，也不得写成已有独立实验室交叉验证。"),

  heading(titles[4]),
  citedBody("临界流形使用同一简化 Allen–Dynes/McMillan 公式且 f₁=f₂=1。它只检验简化公式的逻辑后果，不是材料预测。", 5),
  temperatureEquation(),
  makeTable(
    ["λ", "μ*", "输入 ωlog（meV）", "Tc（K）"],
    critical.temperature_anchors.map((row) => [
      String(row.lambda),
      String(row.mu_star),
      String(row.omega_log_meV),
      String(row.tc_K),
    ]),
    [1700, 1700, 3300, 2806],
  ),
  body(`三个锚点均低于 300 K。全量复核为 ${critical.root_count} 组根、${critical.grid_point_count.toLocaleString("en-US")} 个直接点，分类不一致为 ${critical.grid_class_disagreements}。这反驳的是使用同一简化公式时的普适必然性措辞，不否定完整 Eliashberg 理论、特定材料或 Song 的实验报告。`),
  body(`前批方法审计还记录 Lean Markdown ${lean.markdown_proof_hole_count} 处行首证明债务、独立文件 ${lean.standalone_sorry_count} 个显式 sorry，未运行编译；SI 有 ${si.placeholder_count} 处既定模式占位，未提供 DFT 输入、声子谱或收敛日志。主论文的“形式证明”“完整 DFT 验证”不能按现稿成立。`),

  heading(titles[5]),
  makeTable(
    ["处理级别", "可用表述", "禁止或待核实表述"],
    [
      ["可以说", "Song 作者报告 13 次可重复实验运行、零电阻、磁场抑制和 XRD。", "不得自动升级为独立确认或同行评议完成。"],
      ["必须同时说", "Semenok 等报告七次未成功；独立正向复现未确立，直接 Meissner 仍待完成。", "不得只保留正向结果或把负向结果称为最终否证。"],
      ["成功率 100% 不受支持", "13 次可重复运行没有给出总尝试分母。", "不得写成“13 次全部成功”“铁证”。"],
      ["未核实而非判假", "第 42/43 次故事、300 万元成本未找到当前全文支持。", "标未核实或删除并留痕，不直接判定虚构。"],
      ["不能写", "直接 Meissner、独立实验室交叉验证、必然性的终极证明、2024 年 Nature 320 K 突破。", "不得倒填年份、书目、证据等级或证明状态。"],
    ],
    [2200, 3900, 3406],
  ),

  heading(titles[6]),
  body(`${data.prior_audit_addendum.decision}这是一项时间边界补充，不是删除前批结果，也不意味着 PNAS 数值判断错误。`),

  heading(titles[7]),
  makeTable(
    ["级别与对象", "已观察问题", "建议动作"],
    data.corrections.map((row) => [
      `${row.severity}／${row.target}`,
      row.finding,
      row.action,
    ]),
    [2500, 3600, 3406],
  ),
  body("P2 的实质研究任务包括：一个材料的完整计算复现切片、Lean 命题和证明清偿、前驱体有序化对照、独立正向复现、直接 Meissner 和同位素验证。书目纠错本身不等于科学突破。"),

  heading(titles[8]),
  makeTable(
    ["边界", "状态", "含义"],
    Object.entries(data.open_boundaries).map(([key, value]) => [
      key,
      String(value),
      "当前未确立，不得由预印本存在、局部数值或文档措辞推定完成。",
    ]),
    [3700, 1000, 4806],
  ),
  body("本批使用冻结哈希、原始 PDF、Crossref 元数据、前批方法审计和临界流形数值证据。独立来源复核见 verify_primary_sources.py；最终命令、退出码见 run.log；Word 逐页结果见 word-qa/report.json。"),
  body("本批没有运行 Lean、没有新做实验或独立复现、没有新增材料预测，也没有修改六份原文。全库审计尚未完成。"),
];

const document = new Document({
  creator: "TOE-SYLVA",
  title: "主论文四版本与手册两章：证据角色、实验争议与未竟工作审计",
  description: "正负实验预印本并存、Nature 引文错配、数值反例、证明债务与出版边界。",
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
    1: { children: [para(run(`Predicted hot superconductivity in LaSc2H24 under pressure. PNAS 121(26), e2401840121 (2024). DOI 10.1073/pnas.2401840121. ${data.evidence.pnas_prediction.url}`, { size: 18 }))] },
    2: { children: [para(run(`Y. Song et al. Room-Temperature Superconductivity at 298 K in Ternary La-Sc-H System at High-pressure Conditions. arXiv:2510.01273v2 (2025). ${song.url}`, { size: 18 }))] },
    3: { children: [para(run(`D. V. Semenok et al. Stability analysis of superconductivity in P6/mmm-LaSc2H24 and its experimental reproducibility from La-Sc alloys. arXiv:2605.29985v2 (2026). ${semenok.url}`, { size: 18 }))] },
    4: { children: [para(run(`Crossref metadata for DOI 10.1038/s41586-024-07036-5: ${nature.actual_title}, Nature 626, 779–784 (2024). ${nature.crossref_url}`, { size: 18 }))] },
    5: { children: [para(run(`TOE-SYLVA critical-manifold numerical evidence: .worktrees/critical-manifold/papers/room_temp_sc/critical_manifold/results.json and REVIEW.docx. Scope: ${critical.scope}`, { size: 18 }))] },
  },
  sections: [{
    properties: { page: { margin: { top: 1200, bottom: 1200, left: 1200, right: 1200 } } },
    headers: {
      default: new Header({
        children: [para(run("TOE-SYLVA · 主论文与手册证据审计 · 争议边界", { size: 18, color: palette.primary }), {
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
