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
const tcEquation = () => para(new MathEquation({ children: [
  sub("T", "c"), new MathRun(" = "),
  new MathFraction({ numerator: [sub("ω", "log")], denominator: [new MathRun("1.2")] }),
  new MathRun(" exp(E)"),
] }), { alignment: AlignmentType.CENTER, spacing: { before: 100, after: 100 } });
const exponentEquation = () => para(new MathEquation({ children: [
  new MathRun("E = −"),
  new MathFraction({
    numerator: [new MathRun("1.04(1 + λ)")],
    denominator: [new MathRun("λ − μ*(1 + 0.62λ)")],
  }),
] }), { alignment: AlignmentType.CENTER, spacing: { before: 80, after: 160 } });

const assets = data.evidence.assets;
const science = data.evidence.science;
const metadata = data.evidence.metadata;
const titles = [
  "一、血缘裁决与四个发展方向",
  "二、状态矛盾与实际资产",
  "三、科学验证仍不闭合",
  "四、分档勘误与验收任务",
  "五、验证范围与开放边界",
];
const children = [
  para(run("技术文档交付与验证", { bold: true, size: 38, color: palette.dark }), {
    heading: HeadingLevel.TITLE,
    alignment: AlignmentType.CENTER,
    spacing: { before: 620, after: 230 },
  }),
  para(run("资产、状态和未竟工作审计", { bold: true, size: 30, color: palette.primary }), {
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
  toc(titles.map((title, index) => ({ title, level: 1, page: [2, 2, 3, 4, 4][index] }))),
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
  citedBody("最终报告写完成状态 100%，但 A／D 两路仍运行中、质量深化仍进行中、整合清单仍为 TEMPLATE／PARTIAL／PLACEHOLDERS。状态不能直接合并为最终交付。", 4),
  makeTable(
    ["资产", "当前结果", "验收裁决"],
    [
      ["room_temp_sc_paper_FINAL_v2.tar.gz", "未找到；63KB 和 MD5 不可验证", "资产未验证，重新生成后计算新哈希"],
      ["六张图", "未找到", "不写可视化已完成"],
      ["references_enhanced.bib", "未找到", "不写 99 条引用已齐备"],
      ["manuscript_prl.tex 与所称 Markdown 对应文件", "未找到", "多版本只部分存在，不写全格式完成"],
      ["四个 LaTeX 文件", "已存在", "保留，但不自动等于科学验证"],
      ["替代 Lean 与 SI 文件", "已存在", "Lean 未编译；SI 有 31 处占位，仍是草案／模板"],
    ],
    [3300, 3300, 2906],
  ),
  para(new ImageRun({
    type: "png",
    data: fs.readFileSync(path.join(audit, data.figure.png)),
    transformation: { width: 610, height: Math.round(610 * 1584 / 2816) },
  }), { alignment: AlignmentType.CENTER, keepNext: true }),
  para(run(`${data.figure.caption}。图件位于资产清单表之后、结果解释之前；不把 100% 当成可验证完成度。`, { size: 19, italics: true }), {
    alignment: AlignmentType.CENTER,
  }),
  citedBody("最终报告还声称 99 条引用和六张 Nature 标准图表，但当前 references_enhanced.bib 和图件均未找到，不能按完成资产计算。", 2),
  citedBody("进度报告中的 A／D 运行中和质量深化进行中进一步否定静态 100% 状态，必须按时间戳和任务状态机重新验收。", 3),
  citedBody("整合检查清单明确保留 TEMPLATE／PARTIAL／PLACEHOLDERS，因此整合与交付仍未完成。", 5),
  citedBody("实际资产清单同时保留四个 LaTeX 文件、替代 Lean 和 SI 文件；缺失只按当前路径记录，不把部分存在写成全部缺失。", 6),

  heading(titles[2]),
  tcEquation(),
  exponentEquation(),
  makeTable(
    ["项目", "实际结果", "不能升级为"],
    [
      ["H₃S 公式", `复算约 ${science.h3s_computed_tc_k.toFixed(6)} K，文中为 ${science.h3s_claimed_tc_k.toFixed(0)} K`, "不能写公式链或材料预测已验证"],
      ["验证评分", "没有公开可复算规则", "不能把百分比当科学验证结果"],
      ["Lean", "未编译且存在证明债务", "不能写机器证明完成或不会报错"],
      ["SI", "31 处占位；DFT 输入、声子谱、收敛日志未提供", "不能写计算验证完成"],
      ["Song／PNAS", "直接 Meissner 和独立复现未确立；PNAS 是理论预测", "不能写完美实验验证或投稿保证"],
    ],
    [1700, 4600, 3206],
  ),
  para([
    run("H₃S 的文内参数按同一公式复算约为 161.081844 K，而不是 203 K；验证百分比又没有公开评分规则，因此 B／C 路的完成不能等同科学验证完成。"),
    new FootnoteReferenceRun(8),
    run("简化 McMillan 参数条件也不自动具有普适物理必然性。"),
    new FootnoteReferenceRun(10),
  ], { indent: { firstLine: 420 } }),
  citedBody("Lean 未编译且存在证明债务，SI 有 31 处既定模式占位，DFT 输入、声子谱和收敛日志未提供，不能写机器证明或计算验证完成。", 9),
  citedBody("Song 的直接 Meissner 和独立正向复现未确立；PNAS 是理论预测，不是实验验证。", 7),
  citedBody(`交付日期 ${metadata.delivery_date} 早于所引 ${metadata.cited_breakthrough_month} 突破，构成元数据时间矛盾，需核对版本血缘而不判造假。`, 1),

  heading(titles[3]),
  makeTable(
    ["级别", "已观察问题", "建议动作"],
    data.corrections.map((row) => [row.severity, row.finding, row.action]),
    [900, 4400, 4206],
  ),
  bodyAfterTable("后续验收采用四列：资产路径与哈希、执行命令、退出码、复核边界。任何失败项保持未完成，直到真实资产和科学证据同时闭合。"),

  heading(titles[4]),
  makeTable(
    ["边界", "状态", "含义"],
    Object.entries(data.open_boundaries).map(([key, value]) => [key, String(value), "当前未完成，不得由完成叙事、文件存在或局部复算推定完成。"]),
    [3700, 1000, 4806],
  ),
  bodyAfterTable("本批使用十项冻结来源、实际资产清单和独立复核。命令与退出码见 run.log；Word 渲染状态见 word-qa/report.json。"),
  body("本批没有重跑计算或实验，没有重建压缩包或图件，没有修改五份原文。全库审计尚未完成。"),
];

const document = new Document({
  creator: "TOE-SYLVA",
  title: "技术文档交付与验证：资产、状态和未竟工作审计",
  description: "资产存在性、状态一致性、科学验证与交付治理。",
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
    1: { children: [para(run("Source: organized/10-技术文档/01-交付摘要.md; delivery date and version lineage.", { size: 16 }), { spacing: { after: 40, line: 200 } })] },
    2: { children: [para(run("Source: organized/10-技术文档/02-最终报告.md; 100% claim, 99 references and six figures.", { size: 16 }), { spacing: { after: 40, line: 200 } })] },
    3: { children: [para(run("Source: organized/10-技术文档/03-进度报告.md; A/D routes remain running.", { size: 16 }), { spacing: { after: 40, line: 200 } })] },
    4: { children: [para(run("Source: organized/10-技术文档/04-质量进展.md; quality deepening remains in progress.", { size: 16 }), { spacing: { after: 40, line: 200 } })] },
    5: { children: [para(run("Source: organized/10-技术文档/05-整合检查清单.md; integration remains TEMPLATE/PARTIAL/PLACEHOLDERS.", { size: 16 }), { spacing: { after: 40, line: 200 } })] },
    6: { children: [para(run("Source: sources/artifact-inventory.json; current-workspace inventory only.", { size: 16 }), { spacing: { after: 40, line: 200 } })] },
    7: { children: [para(run("Source: main-claims/review.json; Song arXiv:2510.01273 is author-reported; PNAS is theoretical prediction.", { size: 16 }), { spacing: { after: 40, line: 200 } })] },
    8: { children: [para(run("Source: validation-materials/review.json; H3S printed-parameter spot check; Kruglov article 024508.", { size: 16 }), { spacing: { after: 40, line: 200 } })] },
    9: { children: [para(run("Source: room-temp-methods/review.json; Lean not built; SI has 31 placeholders and lacks DFT evidence.", { size: 16 }), { spacing: { after: 40, line: 200 } })] },
    10: { children: [para(run("Source: handbook-chapters/review.json; simplified McMillan conditions are not universal.", { size: 16 }), { spacing: { after: 40, line: 200 } })] },
  },
  sections: [{
    properties: { page: { margin: { top: 1200, bottom: 1200, left: 1200, right: 1200 } } },
    headers: {
      default: new Header({
        children: [para(run("TOE-SYLVA · 技术文档交付与验证 · 证据边界", { size: 18, color: palette.primary }), {
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
