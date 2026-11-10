import fs from "node:fs";
import path from "node:path";
import {
  AlignmentType,
  Document,
  Footer,
  Header,
  HeadingLevel,
  ImageRun,
  ImportedXmlComponent,
  Math as MathEquation,
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
const heading = (text, level = 1) => para(run(text, { bold: true, size: level === 1 ? 30 : 26, color: palette.dark }), {
  heading: level === 1 ? HeadingLevel.HEADING_1 : HeadingLevel.HEADING_2,
  spacing: { before: 240, after: 130 },
});

const xmlEscape = (value) => String(value)
  .replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;");
const toc = (entries) => {
  const cached = entries.map(({ title, level }) => `<w:p><w:pPr><w:pStyle w:val="TOC${level}"/>
    <w:tabs><w:tab w:val="right" w:leader="dot" w:pos="9000"/></w:tabs></w:pPr>
    <w:r><w:t>${xmlEscape(title)}</w:t></w:r></w:p>`).join("");
  return ImportedXmlComponent.fromXmlString(`<w:sdt xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
    <w:sdtPr><w:alias w:val="目录"/></w:sdtPr><w:sdtContent>
      <w:p><w:r><w:fldChar w:fldCharType="begin" w:dirty="true"/>
        <w:instrText xml:space="preserve"> TOC \\o &quot;1-2&quot; \\h \\z \\u </w:instrText>
        <w:fldChar w:fldCharType="separate"/></w:r></w:p>
      ${cached}<w:p><w:r><w:fldChar w:fldCharType="end"/></w:r></w:p>
    </w:sdtContent></w:sdt>`).root[0];
};

const makeTable = (headers, rows, widths) => new Table({
  width: { size: widths.reduce((a, b) => a + b, 0), type: WidthType.DXA },
  columnWidths: widths,
  rows: [
    new TableRow({ tableHeader: true, children: headers.map((text, index) => cell(text, index, widths, true)) }),
    ...rows.map((row) => new TableRow({ children: row.map((text, index) => cell(text, index, widths, false)) })),
  ],
});
const cell = (text, index, widths, header) => new TableCell({
  children: [para(run(text, { size: 18, bold: header }), { spacing: { after: 0, line: 240 } })],
  width: { size: widths[index], type: WidthType.DXA },
  margins: { top: 80, bottom: 80, left: 80, right: 80 },
  shading: header ? { type: ShadingType.CLEAR, fill: palette.fill } : undefined,
});
const chiSquare = (subscript) => new MathSuperScript({
  children: [new MathSubScript({ children: [new MathRun("χ")], subScript: [new MathRun(subscript)] })],
  superScript: [new MathRun("2")],
});
const nativeDelta = () => para(new MathEquation({ children: [
  new MathRun("Δ"),
  chiSquare("zero"),
  new MathRun(" − "),
  chiSquare("ΛCDM"),
] }), { alignment: AlignmentType.CENTER, spacing: { before: 120, after: 180 } });

const children = [
  para(run("物理直觉两份文档", { bold: true, size: 40, color: palette.dark }), {
    heading: HeadingLevel.TITLE,
    alignment: AlignmentType.CENTER,
    spacing: { before: 600, after: 220 },
  }),
  para(run("方向、血缘与未竟工作审计", { bold: true, size: 30, color: palette.primary }), {
    alignment: AlignmentType.CENTER,
    spacing: { after: 340 },
  }),
  para(run("一个研究纲领 · 四个候选问题族 · 证据边界", { size: 22, color: palette.light }), {
    alignment: AlignmentType.CENTER,
    spacing: { after: 300 },
  }),
  heading("目录"),
  toc([
    { title: "一、来源与血缘裁决", level: 1 },
    { title: "二、四个候选问题族", level: 1 },
    { title: "三、固定零模型的负向证据", level: 1 },
    { title: "四、H0 单变量切片", level: 1 },
    { title: "五、跨代码系统误差", level: 1 },
    { title: "六、物理直觉工程化尚未验收", level: 1 },
    { title: "七、验证命令与范围", level: 1 },
  ]),
  new Paragraph({ children: [new PageBreak()] }),
  heading("一、来源与血缘裁决"),
  body("两份文档属于同一研究纲领，合订本不是独立新理论。以下哈希在生成时重新计算并与清单一致；主文档虽含未提交修改，审计只读当前内容，提供方其他修改保持原状。"),
  ...data.sources.map((source) => body(`${source.id}：${source.sha256}（只读）。`)),
  body("36 节不机械拆成 36 个方向，而归为四个候选问题族。候选方向不自动意味着外部首创，也不表示四条路线均已完成。"),
  heading("二、四个候选问题族"),
  makeTable(
    ["问题族", "角色与已闭合的局部工作", "未竟工作与下一步"],
    data.directions.map((row) => [`${row.id}：${row.role}`, row.closed, `${row.unfinished}下一步：${row.next}`]),
    [2300, 3500, 3706],
  ),
  heading("三、固定零模型的负向证据"),
  body("固定输入零模型的比较定义为："),
  nativeDelta(),
  body(`Planck 2018 边缘化透镜的三条实现给出 Δχ² 为 ${data.evidence.planck_lensing.minimum_delta_chi_squared.toFixed(6)} 至 ${data.evidence.planck_lensing.maximum_delta_chi_squared.toFixed(6)}，固定零模型受到强烈排除。完整 CMB 的 HyRec 扩展搜索结果为 Δχ²＝${data.evidence.full_cmb_hyrec.delta_chi_squared_total.toFixed(6)}，但这里只允许报告已找到并复验的局部 nuisance profile。`),
  makeTable(
    ["证据通道", "实际结果", "结论边界"],
    [
      ["Planck 透镜", `Δχ² 范围 ${data.evidence.planck_lensing.minimum_delta_chi_squared.toFixed(6)}–${data.evidence.planck_lensing.maximum_delta_chi_squared.toFixed(6)}`, data.evidence.planck_lensing.scope],
      ["完整 CMB（HyRec）", `Δχ²＝${data.evidence.full_cmb_hyrec.delta_chi_squared_total.toFixed(6)}`, data.evidence.full_cmb_hyrec.scope],
      ["PRIMAT BBN", `最大绝对 Δχ²＝${data.evidence.bbn.maximum_absolute_delta_chi_squared.toFixed(12)}`, data.evidence.bbn.scope],
    ],
    [1900, 3000, 4606],
  ),
  body("以上结果不是整个无 CDM 模型族的排除，也不是全参数后验或全局最优证明。"),
  heading("四、H0 单变量切片"),
  makeTable(
    ["H0（km/s/Mpc）", "零模型总 χ²", "ΛCDM 总 χ²", "零模型−基线 Δχ²"],
    data.evidence.h0_scan.rows.map((row) => [
      String(row.h0),
      row.zero_chi_squared_total.toFixed(3),
      row.baseline_chi_squared_total.toFixed(3),
      row.delta_chi_squared_total.toFixed(3),
    ]),
    [1400, 2600, 2600, 2906],
  ),
  para(new ImageRun({
    type: "png",
    data: fs.readFileSync(path.join(audit, "h0-scan-comparison.png")),
    transformation: { width: 610, height: Math.round(610 * 1210 / 2728) },
  }), { alignment: AlignmentType.CENTER, keepNext: true }),
  para(run("图 1　五点 H0 单变量切片；不是全参数拟合。图件位于五点数据表之后、结果解释之前。", { size: 19, italics: true }), {
    alignment: AlignmentType.CENTER,
  }),
  body(`最小配对差出现在 H0＝${data.evidence.h0_scan.minimum_h0}，为 ${data.evidence.h0_scan.minimum_delta_chi_squared}。该值仍远高于计算跟进阈值 10，未触发扩展扫描；阈值不是 p 值或 σ 显著性。`),
  body(`BBN 的三组观测选择中，零模型与基线的最大绝对 Δχ² 仅为 ${data.evidence.bbn.maximum_absolute_delta_chi_squared.toFixed(12)}，近似一致，不能抵消 CMB 排除。`),
  heading("五、跨代码系统误差"),
  body("TT 透镜口径、若干插值与共动映射错误已经纠正；k800 与 ultra 的全部 5878 个共享 q 节点和共动密度逐位一致，最高带对数变化为 0，说明输出加密没有求解精度收益。AccuracyBoost=8 多次触及 300 秒前台时限且没有数值结果，不能写成已完成。"),
  body("极端相位序列、深谷点值、复合实现差异和非线性仍未闭合。相邻精度稳定、规范修正或单变量零差异不能升级为全谱、观测或跨代码闭合。"),
  heading("六、物理直觉工程化尚未验收"),
  body("物理直觉引擎尚未验证有效。当前只有混合工作流、双方法评委、任务包和证据卡设计，不能据此证明程序存在、模型有效或跨领域直觉可靠。下一步必须先实现最小引擎，再使用未见任务、常规模型对照、消融、许可清单和失败分布评估相对增益。"),
  body("数学—物理观与 AI 研究治理同样需要以实际任务覆盖、成本面板和冻结后评估检验，不能将结构化文档等同于已完成的制度。"),
  heading("七、验证命令与范围"),
  body(`基线命令：${data.evidence.unit_tests.command}`),
  body("实际为 41/41 通过。审计合同运行 python test_physical_intuition_audit.py -v；Word 使用 docx.py build／validate 与 doc-k 最终视图逐页验收，命令和退出码见 run.log 与 word-qa/report.json。"),
  body("本审计只覆盖这两份文档，不代表全库审计完成，也不替代非线性、全参数、独立实现和物理直觉引擎的后续验证。"),
];

const document = new Document({
  creator: "TOE-SYLVA",
  title: "物理直觉两份文档：方向、血缘与未竟工作审计",
  description: "一个研究纲领与四个候选问题族；固定零模型与物理直觉工程的证据边界。",
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
  sections: [{
    properties: { page: { margin: { top: 1200, bottom: 1200, left: 1200, right: 1200 } } },
    headers: {
      default: new Header({
        children: [para(run("TOE-SYLVA · 物理直觉方向审计 · 证据边界", { size: 18, color: palette.primary }), {
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
