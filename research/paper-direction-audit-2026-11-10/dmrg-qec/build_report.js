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
const phaseEquation = () => para(new MathEquation({ children: [
  new MathRun("|"),
  new MathFraction({ numerator: [sub("t", "2")], denominator: [sub("t", "1")] }),
  new MathRun("| ≳ 0.15"),
] }), { alignment: AlignmentType.CENTER, spacing: { before: 120, after: 180 } });

const finite = data.evidence.dmrg.finite_temperature;
const globalRow = data.evidence.dmrg.global_ground_state;
const stripes = data.evidence.stripes;
const extended = data.evidence.extended_hubbard;
const qec = data.evidence.qec;
const titles = [
  "一、血缘裁决与四个发展方向",
  "二、DMRG：有限温度、基态与二维极限",
  "三、QEC：阈值、解码器和硬件角色",
  "四、分档勘误与发展任务",
  "五、验证范围与开放边界",
];
const children = [
  para(run("DMRG 与量子纠错", { bold: true, size: 38, color: palette.dark }), {
    heading: HeadingLevel.TITLE,
    alignment: AlignmentType.CENTER,
    spacing: { before: 620, after: 230 },
  }),
  para(run("证据阶梯、硬件角色与未竟工作审计", { bold: true, size: 30, color: palette.primary }), {
    alignment: AlignmentType.CENTER,
    spacing: { after: 300 },
  }),
  para(run("一个研究纲领 · 四个发展方向 · 只读审计", { size: 22, color: palette.light }), {
    alignment: AlignmentType.CENTER,
    spacing: { after: 240 },
  }),
  para(run("2026-11-10　不修改原文、不重跑模型、不新增硬件实验", { size: 20 }), {
    alignment: AlignmentType.CENTER,
    spacing: { after: 360 },
  }),
  heading("目录"),
  para(run("以下页码为可见缓存；在 Word/WPS 中更新域可刷新。", { size: 18, italics: true, color: palette.light })),
  toc(titles.map((title, index) => ({ title, level: 1, page: [2, 2, 3, 4, 4][index] }))),
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
  citedBody("DMRG 资料包含不同模型、温度和系综。以下把 Qu、Chen、条纹综述和 Peng 分开，不用单一“已证明”覆盖全部结果。", 1),
  makeTable(
    ["证据", "实际结果", "不能升级为"],
    [
      [`Qu：arXiv:${finite.arxiv}`, `有限温度；W≤${finite.max_width}；T/J≥${finite.min_temperature_t_over_j}；正 t′ 穹顶、负 t′ 更弱`, "无限二维零温基态证明"],
      [`Chen：arXiv:${globalRow.arxiv}`, `${globalRow.legs}-leg 基态；纯 t-J d 波；|t₂/t₁|≳${globalRow.uniform_abs_t2_over_t1} 均匀 SC；有代码数据`, "无限二维热力学极限已证明"],
      [`条纹综述：arXiv:${stripes.arxiv}`, `[43,44] 报告 d 波，[41,42] 更接近 CDW；能量差约 ${stripes.energy_difference_t}t`, "所有 DMRG 已得到同一基态"],
      [`Peng：PRB 107, ${extended.article}`, "长四腿圆柱中近邻吸引增强 d 波关联", "把前作一维 p 波当成本文直接结论"],
    ],
    [2500, 4500, 2506],
  ),
  phaseEquation(),
  citedBody(`Qu 的研究是有限温度热张量网络：宽度不超过 ${finite.max_width}、最低 T/J 约 ${finite.min_temperature_t_over_j}，正 t′ 侧有穹顶，负 t′ 侧配对更弱。`, 2),
  citedBody(`Chen 的 ${globalRow.legs}-leg 基态结果和 |t₂/t₁|≳0.15 均匀 SC 相真实存在，并附公开代码数据；但 GCE 自然基态、有限键维数和有限宽度不等于无限二维证明。`, 3),
  citedBody(`条纹综述实际为 [43,44] 报告 d 波、[41,42] 更接近 CDW，资料文档把两组编号写反。`, 4),
  citedBody(`Peng 等正式出处为 PRB 107, ${extended.article}，研究长四腿圆柱中近邻吸引增强 d 波关联；p 波是其所引的一维 EHM 前作。`, 5),
  body("Chen 的结果应发展为公开代码复现和更宽系统研究，而不是删除。有限温度、基态、系综和宽度必须分别报告。"),

  heading(titles[2]),
  citedBody("QEC 资料中的数值必须绑定噪声、码、解码器和硬件平台。跨学科引用另行按假说和实验证据分层。", 6),
  makeTable(
    ["证据", "实际结果", "证据边界"],
    [
      ["XZZX", `去极化 ${(qec.xzzx.depolarizing_threshold * 100).toFixed(1)}%；纯 Pauli 约 ${(qec.xzzx.pure_pauli_threshold * 100).toFixed(0)}%`, "不与电路级约 1% 直接横比"],
      ["Google", `d=5/7；Λ=${qec.google.lambda}±${qec.google.lambda_uncertainty}；${qec.google.latency_us} μs`, "后续里程碑，不写成无条件的绝对首次"],
      ["中性原子", `${qec.neutral_atoms.year} 年；48×${qec.neutral_atoms.logical_48_code}；另有 d=7 表面码 Bell 对`, "不能写成 48 个 distance-7 LDPC"],
    ],
    [1900, 4900, 2706],
  ),
  para(new ImageRun({
    type: "png",
    data: fs.readFileSync(path.join(audit, data.figure.png)),
    transformation: { width: 610, height: Math.round(610 * 1584 / 2816) },
  }), { alignment: AlignmentType.CENTER, keepNext: true }),
  para(run(`${data.figure.caption}。图件位于证据角色表之后、结果解释之前；不含成功率或验证百分比。`, { size: 19, italics: true }), {
    alignment: AlignmentType.CENTER,
  }),
  citedBody(`XZZX 的 ${(qec.xzzx.depolarizing_threshold * 100).toFixed(1)}% 对应标准去极化噪声，约 ${(qec.xzzx.pure_pauli_threshold * 100).toFixed(0)}% 对应纯 X／Y／Z Pauli 噪声；阈值真实，但比较口径不同。`, 7),
  citedBody(`Google 的距离 5／7、Λ＝${qec.google.lambda}±${qec.google.lambda_uncertainty} 和 ${qec.google.latency_us} μs 实时解码均真实；2023 年已有表面码标度工作，因此不写成无条件的绝对首次。`, 8),
  citedBody(`中性原子论文为 Nature 626（${qec.neutral_atoms.year}）：48 个逻辑量子比特来自 ${qec.neutral_atoms.logical_48_code} 码块；d＝7 表面码 Bell 对属于另一组实验，不能拼接成 48 个 distance-7 LDPC。`, 9),
  body("LDPC 的更高阈值、O(d) 开销和线性解码不是全码族统一性质。YBCO 涡旋量子比特与“拓扑保护＋QEC 双重容错”仍是待验证假说，需要相干时间、耦合、读出和实验协议。"),

  heading(titles[3]),
  makeTable(
    ["级别", "已观察问题", "建议动作"],
    data.corrections.map((row) => [row.severity, row.finding, row.action]),
    [900, 4400, 4206],
  ),
  bodyAfterTable("优先顺序：先修正证据编号与码族身份，再复现 Chen 的公开代码数据、建立 QEC 四维证据卡；跨学科部分先完成物理可实现性定义，不以类比替代实验。"),

  heading(titles[4]),
  makeTable(
    ["边界", "状态", "含义"],
    Object.entries(data.open_boundaries).map(([key, value]) => [key, String(value), "当前未完成，不得由局部文献、数值或类比推定完成。"]),
    [3700, 1000, 4806],
  ),
  bodyAfterTable("本批使用九项冻结来源、原始 PDF／HTML 和独立文本合同。命令与退出码见 run.log；Word 逐页结果见 word-qa/report.json。其余引文未全审。"),
  body("本批没有重跑模型、解码器或硬件实验，没有修改两份原文。全库审计尚未完成。"),
];

const document = new Document({
  creator: "TOE-SYLVA",
  title: "DMRG 与量子纠错：证据阶梯、硬件角色与未竟工作审计",
  description: "DMRG 证据阶梯、扩展模型、QEC 同口径基准和跨学科治理。",
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
    1: { children: [para(run("TOE-SYLVA read-only source: organized/14-资料收集-DMRG-Hubbard模型.md. Citation and evidence-role audit only.", { size: 18 }))] },
    2: { children: [para(run(`Qu et al., Phase Diagram, d-Wave Superconductivity, and Pseudogap of the t-t′-J Model at Finite Temperature, arXiv:${finite.arxiv}; PRL 133, 256003.`, { size: 18 }))] },
    3: { children: [para(run(`Chen, Haldane and Sheng, Global Phase Diagram of D-wave Superconductivity in the Square-Lattice t-J Model, arXiv:${globalRow.arxiv}; PNAS 2025, DOI 10.1073/pnas.2420963122. Code/data: ${globalRow.code_url}`, { size: 18 }))] },
    4: { children: [para(run(`Devereaux and Kivelson, The significance of “stripes” in the physics of the cuprates, the Hubbard model, and other highly correlated electronic systems, arXiv:${stripes.arxiv}.`, { size: 18 }))] },
    5: { children: [para(run(`Peng et al., Enhanced superconductivity by near-neighbor attraction in the doped Hubbard model, arXiv:${extended.arxiv}; Physical Review B 107, ${extended.article}.`, { size: 18 }))] },
    6: { children: [para(run("TOE-SYLVA read-only source: organized/18-资料收集-量子纠错码进展.md. Noise/code/hardware claims audited separately; not all citations checked.", { size: 18 }))] },
    7: { children: [para(run("Bonilla Ataides et al., The XZZX surface code, Nature Communications 12, 2172 (2021). Thresholds are noise- and decoder-dependent.", { size: 18 }))] },
    8: { children: [para(run(`Acharya et al., Quantum error correction below the surface code threshold, arXiv:${qec.google.arxiv}; Nature 2025, DOI 10.1038/s41586-024-08449-y.`, { size: 18 }))] },
    9: { children: [para(run("Bluvstein et al., Logical quantum processor based on reconfigurable atom arrays, Nature 626, 58–65 (2024), DOI 10.1038/s41586-023-06927-3. 48 logical qubits use 3D [[8,3,2]] blocks; d=7 surface-code Bell pairs are separate.", { size: 18 }))] },
  },
  sections: [{
    properties: { page: { margin: { top: 1200, bottom: 1200, left: 1200, right: 1200 } } },
    headers: {
      default: new Header({
        children: [para(run("TOE-SYLVA · DMRG 与量子纠错 · 证据边界", { size: 18, color: palette.primary }), {
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
