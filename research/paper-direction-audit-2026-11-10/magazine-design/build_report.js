import fs from "node:fs";
import path from "node:path";
import {
  AlignmentType, Document, Footer, FootnoteReferenceRun, Header, HeadingLevel,
  ImageRun, ImportedXmlComponent, Math as MathEquation, MathFraction, MathRun,
  Packer, PageBreak, PageNumber, Paragraph, ShadingType, Table, TableCell,
  TableRow, TextRun, WidthType,
} from "docx";

const outputPath = process.argv[2];
if (!outputPath) throw new Error("Usage: node build_report.js /absolute/path/REVIEW.docx");
const audit = path.dirname(outputPath);
const data = JSON.parse(fs.readFileSync(path.join(audit, "review.json"), "utf8"));
const font = { ascii: "Times New Roman", hAnsi: "Times New Roman", cs: "Times New Roman", eastAsia: "SimSun" };
const palette = { dark: "263238", primary: "455A64", light: "78909C", fill: "EEF3F6" };
const run = (text, options = {}) => new TextRun({ text: String(text), font, size: 20, ...options });
const para = (children, options = {}) => new Paragraph({
  spacing: { after: 100, line: 270 },
  ...options,
  children: Array.isArray(children) ? children : [children],
});
const body = (text, options = {}) => para(run(text), { indent: { firstLine: 400 }, ...options });
const citedBody = (text, footnoteId) => para([run(text), new FootnoteReferenceRun(footnoteId)], { indent: { firstLine: 400 } });
const heading = (text, level = 1) => para(run(text, { bold: true, size: level === 1 ? 29 : 25, color: palette.dark }), {
  heading: level === 1 ? HeadingLevel.HEADING_1 : HeadingLevel.HEADING_2,
  spacing: { before: 220, after: 120 },
  keepNext: true,
});
const pageBreak = () => new Paragraph({ children: [new PageBreak()] });
const xmlEscape = (value) => String(value).replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;");
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
const cell = (text, index, widths, header, size = 15) => new TableCell({
  children: [para(run(text, { size, bold: header }), { spacing: { after: 0, line: 200 } })],
  width: { size: widths[index], type: WidthType.DXA },
  margins: { top: 20, bottom: 20, left: 70, right: 70 },
  shading: header ? { type: ShadingType.CLEAR, fill: palette.fill } : undefined,
});
const makeTable = (headers, rows, widths, size = 15) => new Table({
  width: { size: widths.reduce((a, b) => a + b, 0), type: WidthType.DXA },
  columnWidths: widths,
  rows: [
    new TableRow({ tableHeader: true, cantSplit: true, children: headers.map((text, index) => cell(text, index, widths, true, size)) }),
    ...rows.map((row) => new TableRow({ cantSplit: true, children: row.map((text, index) => cell(text, index, widths, false, size)) })),
  ],
});
const equation = (children) => para(new MathEquation({ children }), { alignment: AlignmentType.CENTER, spacing: { before: 80, after: 100 } });
const gridEquation = () => equation([new MathRun("12 × 14 + 11 × 4 = 212 mm ≠ 174 mm")]);
const columnEquation = () => equation([
  new MathRun("w = "),
  new MathFraction({ numerator: [new MathRun("174 − 11 × 4")], denominator: [new MathRun("12")] }),
  new MathRun(" ≈ 10.833333 mm"),
]);
const footnote = (text) => para(run(text, { size: 15 }), { spacing: { after: 30, line: 190 } });
const titles = [
  "一、方向与来源血缘",
  "二、资产与生成链",
  "三、11 份文档逐篇裁决",
  "四、计算、科学与无障碍",
  "五、十二项分级勘误",
  "六、开放边界与后续",
];
const assets = data.evidence.assets;
const generator = data.evidence.generator;
const layout = data.evidence.layout;
const children = [
  para(run("杂志设计系统审计", { bold: true, size: 38, color: palette.dark }), {
    heading: HeadingLevel.TITLE, alignment: AlignmentType.CENTER, spacing: { before: 600, after: 220 },
  }),
  para(run("科学传播、计算一致性与生产溯源", { bold: true, size: 29, color: palette.primary }), {
    alignment: AlignmentType.CENTER, spacing: { after: 280 },
  }),
  para(run("11 份文档 · 四个方向 · 十二项勘误", { size: 21, color: palette.light }), {
    alignment: AlignmentType.CENTER, spacing: { after: 220 },
  }),
  para(run("2026-11-10　只读审计 · 不运行原生成器 · 不修改原文", { size: 19 }), {
    alignment: AlignmentType.CENTER, spacing: { after: 330 },
  }),
  heading("目录"),
  para(run("以下页码为可见缓存；在 Word/WPS 中更新域可刷新。", { size: 17, italics: true, color: palette.light })),
  toc(titles.map((title, index) => ({ title, level: 1, page: [2, 3, 4, 4, 4, 5][index] }))),
  pageBreak(),

  heading(titles[0]),
  body(data.source_lineage.decision),
  makeTable(
    ["方向与角色", "已闭合的局部审计", "未竟工作与下一步"],
    data.directions.map((row) => [`${row.id}：${row.role}`, row.closed, `${row.unfinished} 下一步：${row.next}`]),
    [3000, 2800, 3706], 14,
  ),
  citedBody("七份组织后设计文档在 CRLF 统一为 LF 后，MD5 与原始校验清单 7/7 一致；原始字节 MD5 的差异只来自换行，不能据此推断内容丢失。", 1),
  citedBody("历史 file_index.json 记录了七份原文件的大小与时间，但历史索引不能证明当前原路径仍存在；当前七项原路径均缺失，组织后 11 份文档均存在。", 2),
  makeTable(
    ["来源 ID", "只读路径", "SHA-256"],
    data.sources.map((row) => [row.id, row.path, row.sha256]),
    [1700, 4500, 3306], 11,
  ),
  pageBreak(),

  heading(titles[1]),
  makeTable(
    ["资产／合同", "当前观察", "裁决"],
    [
      ["现有 PDF", "6 份，7–118 页；首页均 A4", "存在可记录，不等于目标版本或内容验收"],
      ["PDF/X 与 Output Intent", "当前未检出", "不能宣称 PDF/X-4 或印前合规"],
      ["InDesign 模板／VI 资源包", "未找到", "不写模板和资源包已交付"],
      ["67 KB 压缩包及 MD5", "当前路径未找到", "历史报告可留痕，当前压缩包不可验证"],
      ["七个原始 Markdown 路径", "缺失；组织后内容保留", "修复路径合同，不重写内容"],
      ["generate_pdf.py", "500 字预览；覆写三份说明文档", "禁止在原目录运行，需重构"],
    ],
    [2700, 3200, 3606], 14,
  ),
  citedBody("交付报告声称 67 KB 压缩包、七个设计文档和校验清单已经交付；当前只确认报告与校验清单存在，所称压缩包未找到。", 4),
  citedBody("generate_pdf.py 对每份设计文档只取 content[:500] 生成预览，run() 又调用三个说明文档重建函数，会覆写原目录内容。本批没有执行该脚本。", 3),
  makeTable(
    ["PDF 文件", "页数"],
    Object.entries(assets.pdf_pages).map(([name, pages]) => [name, String(pages)]),
    [7600, 1906], 14,
  ),
  para(new ImageRun({
    type: "png",
    data: fs.readFileSync(path.join(audit, data.figure.png)),
    transformation: { width: 610, height: 343 },
  }), { alignment: AlignmentType.CENTER, keepNext: true }),
  para(run(`${data.figure.caption}。图件位于资产与血缘表之后、逐文档裁决之前；不显示完成百分比。`, { size: 18, italics: true }), {
    alignment: AlignmentType.CENTER,
  }),
  pageBreak(),

  heading(titles[2]),
  body("每一篇都对应设计或传播任务，但没有任何一篇因此成为独立新理论。下表保留各文档的价值，同时列出真实未竟工作。"),
  makeTable(
    ["文档", "方向", "角色", "未竟工作与下一步"],
    data.document_assessments.map((row) => [
      row.title,
      row.direction_ids.join("／"),
      row.role,
      `${row.unfinished} 下一步：${row.next}`,
    ]),
    [1250, 1900, 2150, 4206], 12,
  ),
  heading(titles[3]),
  gridEquation(),
  columnEquation(),
  makeTable(
    ["检查项", "标称／声明", "复算与验收"],
    [
      ["05 排版系统", "栏宽 14mm、文本宽 174mm", `总宽 ${layout.layout_grid_width_mm}mm；若保留文本宽，栏宽约 ${layout.layout_correct_column_mm.toFixed(6)}mm`],
      ["09 页面设计", "栏宽 11mm、文本宽 165mm", `总宽 ${layout.page_grid_width_mm}mm；若保留文本宽，栏宽约 ${layout.page_correct_column_mm.toFixed(6)}mm`],
      ["页数", "106／60；封面故事 14 页", "细项 16 页；现有 PDF 为 7–118 页，需版本清单"],
      ["霓虹紫／深色背景", "普通文本对比度 ≥4.5:1", "4.137746，未通过普通文本门槛"],
      ["弱化灰／深色背景", "普通文本对比度 ≥4.5:1", "3.202044，未通过普通文本门槛"],
    ],
    [2100, 3100, 4306], 14,
  ),
  citedBody("杂志简介把 McMillan 公式写成严格证明，并把 LaSc₂H₂₄ 的 298 K 写成数学必然，还复述 13 次重复实验和仅 6% 误差。这些措辞必须回到原始证据等级。", 5),
  citedBody("既有手册审计明确保留三条件、实验必然性、直接磁测量和独立正向复现等开放边界；简化公式与作者预印本不能升级为普遍证明或独立实验验证。", 6),
  citedBody("页面设计的数据表把 H₂S 的 155 GPa 放在“临界磁场”列。GPa 是压力单位，应移至压力列并补来源；磁场需要另列并注明条件。", 7),
  citedBody("网页手册自己要求普通文本对比度至少 4.5:1，但霓虹紫与弱化灰的实际复算不满足；文档还没有 prefers-reduced-motion。", 8),
  citedBody("网聊手册包含量子通信“绝对安全”、直接引语和长按交互。引文需回源，绝对安全需限定，长按时长与手势必须提供键盘等效操作。", 9),
  citedBody("内容架构标记 READY_FOR_PRODUCTION，但事实核查、真实采访、页数、资产与印前验收均未闭合，状态应退回草案。", 10),
  heading(titles[4]),
  makeTable(
    ["级别", "已观察问题", "建议动作"],
    data.corrections.map((row) => [row.severity, row.finding, row.action]),
    [800, 4400, 4306], 13,
  ),
  body("优先级不是删除设计，而是先阻断错误科学声明和生产放行，再修几何、资产与无障碍，最后统一品牌细节。"),
  heading(titles[5]),
  makeTable(
    ["开放边界", "状态", "当前含义"],
    Object.entries(data.open_boundaries).map(([key, value]) => [key, String(value), "未完成；不能由规范文本、PDF 存在、历史索引或风格化勾选标记推定完成。"]),
    [3400, 900, 5206], 14,
  ),
  citedBody("前批技术文档审计同样要求把资产存在、完成叙事和科学验证分开。本批继承这一原则，但不把前批审计当作本批事实的替代来源。", 11),
  body("后续最小垂直切片：①建立逐句科学证据卡；②冻结唯一版本与网格令牌；③完成对比度、键盘和减弱动效测试；④把生成器改为只读输入、独立输出、完整内容和失败非零退出；⑤再做 PDF/X、授权和印前验收。"),
  body("本批使用 17 项冻结来源、7 项独立来源测试和只读 PDF 元数据。没有运行原生成器，没有修改 11 份原文，没有生成新印刷 PDF，没有完成外部事实逐项回源。全库审计尚未完成。"),
];

const document = new Document({
  creator: "TOE-SYLVA",
  title: "杂志设计系统：科学传播、计算一致性与生产溯源审计",
  description: "11 份杂志设计文档的方向、未竟工作、计算一致性与生产资产审计。",
  features: { updateFields: true },
  styles: {
    paragraphStyles: [1, 2].map((level) => ({
      id: `TOC${level}`,
      name: `TOC ${level}`,
      basedOn: "Normal",
      next: "Normal",
      quickFormat: true,
      run: { font, size: 19, color: palette.dark },
      paragraph: { spacing: { after: 70, line: 240 }, indent: { left: (level - 1) * 360 } },
    })),
  },
  footnotes: {
    1: { children: [footnote("Sources: magazine/checksums.md5 and organized design files; LF-normalized MD5 comparison.")] },
    2: { children: [footnote("Source: magazine/file_index.json; historical index only, not current-path proof.")] },
    3: { children: [footnote("Source: magazine/generate_pdf.py; static inspection only, script not executed.")] },
    4: { children: [footnote("Source: magazine/DELIVERY_REPORT.md; claimed 67 KB archive and delivery checklist.")] },
    5: { children: [footnote("Source: organized/11-杂志设计/02-杂志简介.md; necessity and experimental wording.")] },
    6: { children: [footnote("Source: handbook-chapters/review.json; conditional model and experimental open boundaries.")] },
    7: { children: [footnote("Source: organized/11-杂志设计/09-页面设计.md; H2S 155 GPa under the magnetic-field column.")] },
    8: { children: [footnote("Source: organized/11-杂志设计/07-网页风格排版.md; contrast target and motion rules.")] },
    9: { children: [footnote("Source: organized/11-杂志设计/08-网聊文化融入.md; quotations, absolute security and gestures.")] },
    10: { children: [footnote("Source: organized/11-杂志设计/06-内容架构.md; READY_FOR_PRODUCTION and page allocation.")] },
    11: { children: [footnote("Source: technical-docs/review.json; separation of artifacts, status narratives and scientific validation.")] },
  },
  sections: [{
    properties: { page: { margin: { top: 1050, bottom: 1050, left: 1050, right: 1050 } } },
    headers: {
      default: new Header({
        children: [para(run("TOE-SYLVA · 杂志设计审计 · 证据与生产边界", { size: 17, color: palette.primary }), {
          alignment: AlignmentType.CENTER,
        })],
      }),
    },
    footers: {
      default: new Footer({
        children: [para(new TextRun({ children: [PageNumber.CURRENT], font, size: 17 }), {
          alignment: AlignmentType.CENTER,
        })],
      }),
    },
    children,
  }],
});

fs.writeFileSync(outputPath, await Packer.toBuffer(document));
