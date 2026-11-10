import fs from "node:fs";
import path from "node:path";
import {
  AlignmentType,
  Document,
  Footer,
  FootnoteReferenceRun,
  Header,
  HeadingLevel,
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
  spacing: { after: 140, line: 290 },
  ...options,
  children: Array.isArray(children) ? children : [children],
});
const body = (text, options = {}) => para(run(text), { indent: { firstLine: 420 }, ...options });
const citedBody = (text, footnoteId) => para([
  run(text),
  new FootnoteReferenceRun(footnoteId),
], { indent: { firstLine: 420 } });
const heading = (text, level = 1) => para(run(text, {
  bold: true,
  size: level === 1 ? 30 : 26,
  color: palette.dark,
}), {
  heading: level === 1 ? HeadingLevel.HEADING_1 : HeadingLevel.HEADING_2,
  spacing: { before: 260, after: 140 },
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
  children: [para(run(text, { size: 17, bold: header }), {
    spacing: { after: 0, line: 230 },
  })],
  width: { size: widths[index], type: WidthType.DXA },
  margins: { top: 90, bottom: 90, left: 90, right: 90 },
  shading: header ? { type: ShadingType.CLEAR, fill: palette.fill } : undefined,
});
const makeTable = (headers, rows, widths) => new Table({
  width: { size: widths.reduce((a, b) => a + b, 0), type: WidthType.DXA },
  columnWidths: widths,
  rows: [
    new TableRow({ tableHeader: true, children: headers.map((text, index) => cell(text, index, widths, true)) }),
    ...rows.map((row) => new TableRow({ children: row.map((text, index) => cell(text, index, widths, false)) })),
  ],
});
const subscript = (sub) => new MathSubScript({
  children: [new MathRun("C")],
  subScript: [new MathRun(sub)],
});
const constantEquation = () => para(new MathEquation({ children: [
  subscript("upper"),
  new MathRun(` ≈ ${data.evidence.eliashberg.upper_bound_multiplier} `),
  subscript("sharp"),
  new MathRun(` ≈ ${data.evidence.eliashberg.upper_bound_coefficient.toFixed(6)}`),
] }), { alignment: AlignmentType.CENTER, spacing: { before: 120, after: 180 } });

const sectionTitles = [
  "一、血缘裁决与总判断",
  "二、五个方法方向，而非五个新理论",
  "三、可复核的更正与证据边界",
  "四、Floquet-LaH₁₀：压力顺序与近似角色",
  "五、Eliashberg：严格界、非最优上界与经验公式",
  "六、Lean：草案，不是机器证明",
  "七、SI：模板，不是已完成的补充信息",
  "八、范围外缺陷与后续优先级",
  "九、验证范围与禁止升格",
];
const f = data.evidence.floquet;
const d = data.evidence.dmrg;
const m = data.evidence.lasc2h24;
const e = data.evidence.eliashberg;
const lean = data.evidence.lean;
const si = data.evidence.si;
const floquetRows = [
  ...f.dfpt_estimates.map((row) => ({ ...row, method: "Floquet-DFPT + Allen–Dynes 直接估计", role: "理论估计，非实验" })),
  ...f.dos_scaling_estimates.map((row) => ({ ...row, method: "DOS-scaling", role: "下界，不是准确点预测" })),
];

const children = [
  para(run("room_temp_sc 方法与形式化小组", { bold: true, size: 38, color: palette.dark }), {
    heading: HeadingLevel.TITLE,
    alignment: AlignmentType.CENTER,
    spacing: { before: 640, after: 240 },
  }),
  para(run("证据角色与未竟工作审计", { bold: true, size: 31, color: palette.primary }), {
    alignment: AlignmentType.CENTER,
    spacing: { after: 320 },
  }),
  para(run("一个研究纲领 · 五个方法方向 · 四项明确更正", { size: 22, color: palette.light }), {
    alignment: AlignmentType.CENTER,
    spacing: { after: 260 },
  }),
  para(run("2026-11-10　只读审计　不新增材料预测、全局拟合或 Lean 证明", { size: 20 }), {
    alignment: AlignmentType.CENTER,
    spacing: { after: 380 },
  }),
  heading("目录"),
  toc(sectionTitles.map((title) => ({ title, level: 1 }))),
  new Paragraph({ children: [new PageBreak()] }),

  heading(sectionTitles[0]),
  body("五份文档属于同一 room_temp_sc 研究纲领，分别承担 Floquet 证据、Eliashberg 边界、Lean 形式化、研究综述和 SI 基础设施五种角色。它们不是五个独立新理论，书目修正也不等于新的科学突破。"),
  body("当前最重要的结论不是“理论已经被证明”，而是：两组书目/数值错误可以明确纠正；严格数学界与经验公式必须分工；Lean 和 SI 都仍有实质未竟工作。"),
  ...data.sources.map((source) => para([
    run(`${source.id}：`, { bold: true, size: 18 }),
    run(`${source.path}；SHA-256 ${source.sha256}（只读）。`, { size: 18 }),
  ], { spacing: { after: 100, line: 240 } })),

  heading(sectionTitles[1]),
  makeTable(
    ["方向与角色", "已闭合的局部审计", "未竟工作与下一步"],
    data.directions.map((row) => [
      `${row.id}：${row.role}`,
      row.closed,
      `${row.unfinished} 下一步：${row.next}`,
    ]),
    [3100, 2700, 3706],
  ),
  body("方向计数不按文档或章节机械累加。五个方法方向共享一个研究纲领，也不表示每条路线都已完成或具有外部首创性。"),

  heading(sectionTitles[2]),
  makeTable(
    ["编号／级别", "原记录", "审计裁决", "依据"],
    data.corrections.map((row) => [
      `${row.id}／${row.severity}`,
      row.observed,
      row.corrected,
      row.reason,
    ]),
    [1800, 2300, 2800, 2606],
  ),
  heading("DMRG／t-t′-J：正确书目与有限尺寸边界", 2),
  citedBody(`正确书目是 ${d.journal} ${d.volume}, ${d.article}，发表于 ${d.published}，DOI ${d.doi}，不是 PRL 132, 066002。官方摘要限定圆柱宽度最多 W=${d.max_cylinder_width}，最低到 T/J≈${d.minimum_temperature_t_over_j}。t′/t>0 时出现${d.positive_t_prime_behavior}，特征温度最高约 ${d.max_characteristic_tc_star_over_j}J；t′/t<0 时${d.negative_t_prime_behavior}。这些结果不等于铜氧化物高温超导已被完整解释。`, 2),
  heading("LaSc₂H₂₄：预测不是实验纪录", 2),
  citedBody(`正确书目是 PNAS ${m.volume}(${m.issue}), ${m.article}。167 GPa 下预测最高 316 K，250 GPa 下预测最高 331 K；非谐效应使动力学稳定延伸到 ${m.anharmonic_dynamic_stability_down_to_gpa} GPa。这些值来自结构搜索、第一性原理、SSCHA 与各向同性 Eliashberg 计算，是理论预测，不是实验证实，不能升级为当前最高实验纪录。`, 3),

  heading(sectionTitles[3]),
  citedBody("220 GPa → 320 K；250 GPa → 322 K。资料表原先把这两个结果对调。下表同时保留平衡态、驱动态、场强、方法和证据角色。", 1),
  makeTable(
    ["压力（GPa）", "平衡态 Tc（K）", "驱动态 Tc（K）", "方法与场强", "证据角色"],
    floquetRows.map((row) => [
      String(row.pressure_gpa),
      String(row.equilibrium_tc_k),
      String(row.driven_tc_k),
      `${row.method}；${row.field_mv_per_angstrom} mV/Å`,
      row.role,
    ]),
    [1100, 1400, 1400, 3600, 2006],
  ),
  body("150 GPa 的 285 K 和 200 GPa 的 301 K 来自 DOS-scaling。Xie 原文明确说它们不应被视为准确预测，而是 Floquet-DFPT 结果的下界；不能和 320/322 K 混成同等级、无条件精确预测。原文还明确并非所有被考察氢化物都超过室温。上述均为理论计算，不是实验确认。"),

  heading(sectionTitles[4]),
  citedBody(`Kiessling 等给出的 sharp constant 为 ${e.sharp_constant}…；另一个非最优上界的渐近系数约为其 ${e.upper_bound_multiplier} 倍。两者不是同一个常数，也不承担同一个证明角色。`, 4),
  constantEquation(),
  body("Kiessling 的严格下界、非最优上界与 Allen–Dynes 经验公式必须分别写明假设、归一化和适用域；经验公式不能替代严格证明，非最优上界不能改名为 sharp constant，更不能由此直接推出“室温超导必然性”。"),

  heading(sectionTitles[5]),
  body(`Markdown 形式化文档有 ${lean.markdown_proof_hole_count} 处行首 admit/sorry 标记；独立 Lean 文件中定位到 ${lean.standalone_sorry_count} 个带显式证明位 sorry 的定理：${lean.standalone_sorry_theorems.join("、")}。`),
  body("弱耦合条目把 λ → 0 和逻辑箭头用于命题陈述，不是正确的极限或等式表达；Floquet 条目自身注释仅给 CONFIDENCE: 0.05。因此这里只能登记为草案，不是机器证明。本批没有运行 Lean 编译，也不声称构建通过。"),
  body("综述中的 15,000 行、845 证明项、127 实例、43 秒及“完整陈数基础设施”缺少精确实现版本与构建记录，本批标为未核实，不据此判真或判假。"),
  body("下一步应先修正命题类型和物理假设，再逐定理清偿证明，记录真实构建与 #print axioms；禁止用新公理、证明位占位或空真定理制造绿色状态。"),

  heading(sectionTitles[6]),
  body(`当前 SI 含有 ${si.placeholder_count} 处按既定模式计数的导入、待指定、待补充或占位标记。DFT 参数、声子网格、Eliashberg 函数、材料预测表、灵敏度表、数据仓库和代码清单均未形成可审计资产。`),
  body("因此它是模板，不是已完成的补充信息。模板列出 phonon_spectra/ 等目录不证明这些文件存在。下一步应选一个材料做最小可复现垂直切片：冻结结构和输入，记录软件版本与赝势，完成 k/q/截断能收敛，保存声子和 Eliashberg 输出，并提供独立重跑脚本与哈希清单。"),

  heading(sectionTitles[7]),
  makeTable(
    ["路径与行号", "级别／状态", "问题与后续动作"],
    data.out_of_scope_findings.map((row) => [
      `${row.path}；${row.lines}`,
      `${row.severity}／${row.status}`,
      `${row.finding} 下一步：${row.next}`,
    ]),
    [3300, 1800, 4406],
  ),
  body("这些条目只登记实际读到的高风险内容。未回源的文献不判为虚构，范围外文件不计入本批五份文档的完成量。"),
  body("优先级一：另开原文修订分支，先修正 Floquet 压力映射，再处理主论文/手册的实验—预测和证明—草案错位。优先级二：完成一个材料的输入—收敛—声子—Tc—日志垂直闭环。优先级三：先修 Lean 命题，再清偿证明；严格界与经验公式分轨。优先级四：为每条综述记录 DOI、原文定位、证据等级和最后核验日期。"),

  heading(sectionTitles[8]),
  makeTable(
    ["边界", "状态", "含义"],
    Object.entries(data.open_boundaries).map(([key, value]) => [
      key,
      String(value),
      "本批没有完成该项，不得由文档存在或局部审计推定完成。",
    ]),
    [3600, 1000, 4906],
  ),
  body("本报告使用冻结哈希、原始论文/官方摘要和机器合同。最终命令、实际退出码和关键输出见 run.log；Word 结构验证及最终视图结果见 word-qa/report.json。"),
  body("本批没有重跑 Floquet-DFPT、DMRG、DFT、SSCHA 或 Lean，也没有新增材料预测或证明。全库审计尚未完成。本批只闭合五份方法/形式化文档的选定问题；room_temp_sc 其他文档和全库未竟工作仍需分批推进。"),
];

const document = new Document({
  creator: "TOE-SYLVA",
  title: "room_temp_sc 方法与形式化小组：证据角色与未竟工作审计",
  description: "五份方法文档与一份 Lean 资产的证据角色、明确更正、证明债务和未竟工作。",
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
    1: { children: [para(run(`C. Xie et al. Dynamical approach to realize room-temperature superconductivity in LaH10. npj Computational Materials 11, 227 (2025). DOI 10.1038/s41524-025-01725-z. ${f.source_url}`, { size: 18 }))] },
    2: { children: [para(run(`D.-W. Qu et al. ${d.title}. Physical Review Letters 133, 256003 (2024). DOI 10.1103/PhysRevLett.133.256003. ${d.source_url}`, { size: 18 }))] },
    3: { children: [para(run(`Predicted hot superconductivity in LaSc2H24 under pressure. PNAS 121(26), e2401840121 (2024). DOI 10.1073/pnas.2401840121. ${m.source_url}`, { size: 18 }))] },
    4: { children: [para(run(`M. K.-H. Kiessling, B. L. Altshuler, E. A. Yuzbashyan. Bounds on Tc in the Eliashberg theory of Superconductivity II: Dispersive phonons. arXiv:2409.00532v3. ${e.source_url}`, { size: 18 }))] },
  },
  sections: [{
    properties: { page: { margin: { top: 1200, bottom: 1200, left: 1200, right: 1200 } } },
    headers: {
      default: new Header({
        children: [para(run("TOE-SYLVA · 室温超导方法审计 · 证据边界", { size: 18, color: palette.primary }), {
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
