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
  children: [para(run(text, { size: 17, bold: header }), { spacing: { after: 0, line: 220 } })],
  width: { size: widths[index], type: WidthType.DXA },
  margins: { top: 60, bottom: 60, left: 90, right: 90 },
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
const tc = (argument) => new MathSubScript({ children: [new MathRun("T")], subScript: [new MathRun("c")] });
const logicEquation = () => para(new MathEquation({ children: [
  new MathRun("∃ p : "), tc(), new MathRun("(p) > 300 K"),
  new MathRun("   ⇏   "),
  new MathRun("∀ m ∈ D : "), tc(), new MathRun("(m) > 300 K"),
] }), { alignment: AlignmentType.CENTER, spacing: { before: 120, after: 180 } });

const theory = data.evidence.theory;
const logic = data.evidence.logic;
const experiment = data.evidence.experiment;
const breakthrough = data.evidence.breakthrough;
const titles = [
  "一、血缘裁决与四个发展方向",
  "二、理论证明链：证明债务与逻辑断点",
  "三、突破详解：实验与预测必须分轨",
  "四、分档勘误与发展任务",
  "五、验证范围与开放边界",
];
const children = [
  para(run("理论框架与突破详解", { bold: true, size: 38, color: palette.dark }), {
    heading: HeadingLevel.TITLE,
    alignment: AlignmentType.CENTER,
    spacing: { before: 620, after: 230 },
  }),
  para(run("证明链、实验角色与未竟工作审计", { bold: true, size: 30, color: palette.primary }), {
    alignment: AlignmentType.CENTER,
    spacing: { after: 300 },
  }),
  para(run("一个研究纲领 · 四个发展方向 · 只读审计", { size: 22, color: palette.light }), {
    alignment: AlignmentType.CENTER,
    spacing: { after: 240 },
  }),
  para(run("2026-11-10　不修改原文、不制造证明、不新增实验", { size: 20 }), {
    alignment: AlignmentType.CENTER,
    spacing: { after: 360 },
  }),
  heading("目录"),
  para(run("以下页码为可见缓存；在 Word/WPS 中更新域可刷新。", { size: 18, italics: true, color: palette.light })),
  toc(titles.map((title, index) => ({ title, level: 1, page: [2, 2, 3, 4, 4][index] }))),
  new Paragraph({ children: [new PageBreak()] }),

  heading(titles[0]),
  body(data.source_lineage.decision),
  body("四个方向是可继续发展的方法任务，不代表四个已经成立的新理论，也不表示外部首创性或科学有效性已确立。"),
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
  citedBody(`理论文档有 ${theory.admit_count} 处 admit、${theory.sorry_count} 处 sorry，合计 ${theory.proof_debt_total} 处显式证明债务。文档自述为 0.1-alpha 草案，不能把占位可解析升级为机器证明完成。`, 1),
  body(`五个 Superconductivity.* 模块引用和三个核心定理名在本次 ${theory.module_search_scope} 检索中未解析；共扫描 ${theory.lean_file_count_searched} 个 Lean 文件。未解析不等于其他位置绝对不存在实现，本批未运行 Lean 编译。`),
  makeTable(
    ["项目", "审计结果", "不能升级为"],
    [
      ["显式证明债务", `${theory.admit_count} 处 admit；${theory.sorry_count} 处 sorry`, "构造性证明已完成"],
      ["模块解析", `五个引用；本次仓库命中 ${theory.repository_module_match_count}`, "已有可构建实现或其他位置不存在"],
      ["单点存在到普遍必然", "不是有效逻辑推论", "连续性自动把所有材料变为室温超导"],
      ["简化公式锚点", `Tc≈${logic.simplified_formula_anchor.tc_k.toFixed(6)} K`, "否定完整 Eliashberg 或特定材料"],
    ],
    [2200, 3300, 4006],
  ),
  logicEquation(),
  citedBody(`既有临界流形结果在 λ=${logic.simplified_formula_anchor.lambda}、μ*=${logic.simplified_formula_anchor.mu_star}、ωlog=${logic.simplified_formula_anchor.omega_log_meV} meV 时给出 Tc≈${logic.simplified_formula_anchor.tc_k.toFixed(6)} K。它只约束同一简化公式的普适必然性，不否定完整 Eliashberg 理论或特定材料。`, 2),
  body("下一步应先固定最小可证命题与定义，再逐引理清偿并执行公理审计。H1–H6 需要绑定可观测量、反例条件和失败后的理论降级规则。"),

  heading(titles[2]),
  makeTable(
    ["来源", "数值与角色", "尚未确立"],
    [
      ["PNAS 2024", `167 GPa→${experiment.pnas.predicted_tc_k[0]} K；250 GPa→${experiment.pnas.predicted_tc_k[1]} K；理论预测`, "不能作为后续实验值"],
      ["Song 2025 预印本", `onset ${experiment.song.onset_tc_k[0]}–${experiment.song.onset_tc_k[1]} K；${experiment.song.reproducible_runs_reported} 次作者报告可重复运行`, "独立正向复现、直接 Meissner、同行评议、总尝试分母"],
      ["Semenok 2026 预印本", `${experiment.semenok.unsuccessful_attempts} 次未成功；独立负向复现`, "不是对 Song 或整个材料族的最终否证"],
    ],
    [2000, 4000, 3506],
  ),
  para(new ImageRun({
    type: "png",
    data: fs.readFileSync(path.join(audit, data.figure.png)),
    transformation: { width: 610, height: Math.round(610 * 1584 / 2816) },
  }), { alignment: AlignmentType.CENTER, keepNext: true }),
  para(run(`${data.figure.caption}。图件位于证据角色表之后、结果解释之前；不含成功率或证明完成百分比。`, { size: 19, italics: true }), {
    alignment: AlignmentType.CENTER,
  }),
  citedBody(`PNAS 的 ${experiment.pnas.predicted_tc_k.join("/")} K 是理论预测，不能当作后续实验值。`, 3),
  citedBody(`Song 的 onset 上限为 ${Math.max(...experiment.song.onset_tc_k)} K，低于 300 K；${experiment.song.reproducible_runs_reported} 次作者报告运行不等于独立实验室，独立正向复现和直接 Meissner 尚未确立。`, 4),
  citedBody(`Semenok 报告 ${experiment.semenok.unsuccessful_attempts} 次未成功，必须作为独立负向复现保留，但不是对 Song 或整个材料族的最终否证。`, 5),
  body("不能把 Song 的 298 K 与 PNAS 的 316 K 拼成 298–316 K 实验结果，更不能由单个材料报告证明所有满足抽象假设的材料必然室温超导。"),
  body("P6/mmm 不自动证明准二维，结构与 Tc 一致也不单独验证微观配对机制。需要分别提供层状各向异性、谱函数、同位素和配对机制证据。"),
  body(`突破文档日期为 ${breakthrough.document_date}，却引用 ${breakthrough.cited_preprint_month} 预印本，构成元数据时间矛盾。下一步应核查版本血缘，不直接判定造假。`),

  heading(titles[3]),
  makeTable(
    ["级别", "已观察问题", "建议动作"],
    data.corrections.map((row) => [row.severity, row.finding, row.action]),
    [900, 4400, 4206],
  ),
  bodyAfterTable("优先顺序应是：先收缩命题并建立最小证明核，再做假设—测量接口与争议实验对照，最后同步全部派生文档。四个方向都属于同一研究纲领的未竟事业。"),

  heading(titles[4]),
  makeTable(
    ["边界", "状态", "含义"],
    Object.entries(data.open_boundaries).map(([key, value]) => [key, String(value), "当前未完成，不得由草案、单个材料报告或局部数值推定完成。"]),
    [3700, 1000, 4806],
  ),
  bodyAfterTable("本批使用冻结哈希、原文独立文本扫描、既有原始来源审计和独立数值复算。命令与退出码见 run.log；Word 逐页结果见 word-qa/report.json。"),
  body("本批没有运行 Lean、没有新做 DFT／Eliashberg、没有新做实验或独立复现、没有修改两份原文。全库审计尚未完成。"),
];

const document = new Document({
  creator: "TOE-SYLVA",
  title: "理论框架与突破详解：证明链、实验角色与未竟工作审计",
  description: "条件化证明、假设可证伪化、争议实验复现与证据血缘治理。",
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
    1: { children: [para(run("TOE-SYLVA read-only source: organized/03-理论框架/01-理论框架.md, version 0.1-alpha. Text scan: 17 admits and 5 sorries; no Lean compilation run in this audit.", { size: 18 }))] },
    2: { children: [para(run("Prior numerical evidence: .worktrees/critical-manifold/papers/room_temp_sc/critical_manifold/results.json, inherited from the verified main-claims/review.json. Simplified formula only; not a material prediction.", { size: 18 }))] },
    3: { children: [para(run(`Predicted hot superconductivity in LaSc2H24 under pressure. ${experiment.pnas.citation}. DOI 10.1073/pnas.2401840121. ${experiment.pnas.url}`, { size: 18 }))] },
    4: { children: [para(run(`Y. Song et al. Room-Temperature Superconductivity at 298 K in Ternary La-Sc-H System at High-pressure Conditions. arXiv:${experiment.song.arxiv}, ${experiment.song.version}. ${experiment.song.url}`, { size: 18 }))] },
    5: { children: [para(run(`D. V. Semenok et al. Independent negative replication preprint, arXiv:${experiment.semenok.arxiv}, ${experiment.semenok.version}. ${experiment.semenok.url}`, { size: 18 }))] },
  },
  sections: [{
    properties: { page: { margin: { top: 1200, bottom: 1200, left: 1200, right: 1200 } } },
    headers: {
      default: new Header({
        children: [para(run("TOE-SYLVA · 理论框架与突破详解 · 证据边界", { size: 18, color: palette.primary }), {
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
