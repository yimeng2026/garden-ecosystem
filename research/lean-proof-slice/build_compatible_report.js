import fs from "node:fs";
import path from "node:path";
import {
  AlignmentType, Document, Footer, FootnoteReferenceRun, Header, HeadingLevel,
  ImageRun, ImportedXmlComponent, Math as MathEquation, MathRun, Packer,
  PageBreak, PageNumber, Paragraph, ShadingType, Table, TableCell, TableRow,
  TextRun, WidthType,
} from "docx";

const outputPath = process.argv[2];
if (!outputPath) throw new Error("Usage: node build_compatible_report.js /absolute/path/COMPATIBLE_DEFINITIONS.docx");
const audit = path.dirname(outputPath);
const data = JSON.parse(fs.readFileSync(path.join(audit, "compatible-definitions.json"), "utf8"));
const font = { ascii: "Times New Roman", hAnsi: "Times New Roman", cs: "Times New Roman", eastAsia: "SimSun" };
const palette = { dark: "263238", primary: "455A64", light: "78909C", fill: "EEF3F6" };
const run = (text, options = {}) => new TextRun({ text: String(text), font, size: 20, ...options });
const para = (children, options = {}) => new Paragraph({ spacing: { after: 100, line: 270 }, ...options, children: Array.isArray(children) ? children : [children] });
const body = (text, options = {}) => para(run(text), { indent: { firstLine: 400 }, ...options });
const citedBody = (text, footnoteId) => para([run(text), new FootnoteReferenceRun(footnoteId)], { indent: { firstLine: 400 } });
const heading = (text, level = 1) => para(run(text, { bold: true, size: level === 1 ? 29 : 25, color: palette.dark }), {
  heading: level === 1 ? HeadingLevel.HEADING_1 : HeadingLevel.HEADING_2,
  spacing: { before: 220, after: 120 }, keepNext: true,
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
  width: { size: widths.reduce((a, b) => a + b, 0), type: WidthType.DXA }, columnWidths: widths,
  rows: [
    new TableRow({ tableHeader: true, cantSplit: true, children: headers.map((text, index) => cell(text, index, widths, true, size)) }),
    ...rows.map((row) => new TableRow({ cantSplit: true, children: row.map((text, index) => cell(text, index, widths, false, size)) })),
  ],
});
const equation = (text) => para(new MathEquation({ children: [new MathRun(text)] }), { alignment: AlignmentType.CENTER, spacing: { before: 80, after: 100 } });
const footnote = (text) => para(run(text, { size: 15 }), { spacing: { after: 30, line: 190 } });
const titles = ["一、两个兼容定义与真实编译", "二、局部清偿与开放边界", "三、工具链与后续"];
const children = [
  para(run("Lean 兼容性清偿切片", { bold: true, size: 38, color: palette.dark }), { heading: HeadingLevel.TITLE, alignment: AlignmentType.CENTER, spacing: { before: 600, after: 220 } }),
  para(run("常量、绑定与显式 Debye 类型", { bold: true, size: 29, color: palette.primary }), { alignment: AlignmentType.CENTER, spacing: { after: 280 } }),
  para(run("2 个定义 · 2 个 rfl · 标准三公理", { size: 21, color: palette.light }), { alignment: AlignmentType.CENTER, spacing: { after: 220 } }),
  para(run("2026-11-11　定义通过 ≠ 物理证明", { size: 19 }), { alignment: AlignmentType.CENTER, spacing: { after: 330 } }),
  heading("目录"),
  para(run("以下页码为可见缓存；在 Word/WPS 中更新域可刷新。", { size: 17, italics: true, color: palette.light })),
  toc(titles.map((title, index) => ({ title, level: 1, page: [2, 3, 3][index] }))),
  pageBreak(),

  heading(titles[0]),
  equation("2 definitions + 2 rfl = 2 machine checks"),
  citedBody("bcsCriticalTemp 与 debyeModel 在真实 Lean 4.35.0 下编译退出码为 0。两个展开定理均只依赖标准三公理，没有 sorryAx 或额外公理。", 3),
  makeTable(
    ["新定理", "证明", "sorryAx", "公理依赖"],
    Object.entries(data.dependencies).map(([name, row]) => [name, "rfl", String(row.sorryAx), row.axioms.join("、")]),
    [3500, 1000, 1200, 3806], 13,
  ),
  citedBody("bcsCriticalTemp 使用 Real.eulerMascheroniConstant；该名称已在当前 Mathlib 的 Gamma/Digamma.lean 源码中直接定位，而非凭记忆选择。", 2),
  para(new ImageRun({ type: "png", data: fs.readFileSync(path.join(audit, "compatible-definitions.png")), transformation: { width: 610, height: 283 } }), { alignment: AlignmentType.CENTER, keepNext: true }),
  para(run("图 1　局部兼容清偿与开放边界。两个定义通过不表示原文件或全部问题解决。", { size: 18, italics: true }), { alignment: AlignmentType.CENTER }),
  body("debyeModel 显式给出 ω₀ : ℝ 与 ℝ → ℝ 函数类型，输入 M : ℝ 时返回 ω₀ / Real.sqrt M。ASCII lam 继续沿用前述清洁定义切片；本文件不包含 HasEquiv。"),
  pageBreak(),

  heading(titles[1]),
  makeTable(
    ["项目", "局部结果", "仍未完成"],
    [
      ["Euler 常量", "使用 Real.eulerMascheroniConstant", "原文件尚未修改，需另行评估"],
      ["ASCII 绑定", "lam 已用于清洁定义", "原文件的 λ 标识符问题仍存在"],
      ["Debye 类型", "ω₀ : ℝ，debyeModel : ℝ → ℝ", "同位素比值定理未证明"],
      ["HasEquiv ℝ", "未引入", "命题语义开放，禁止虚假实例"],
    ],
    [2300, 3500, 3706], 14,
  ),
  citedBody("原文件未修改，原文件直译仍不兼容，原三条定理的 sorryAx 审计仍不可用。清洁定义只验证展开，不是对原三条物理定理的证明。", 1),
  makeTable(
    ["开放边界", "状态", "后续"],
    [
      ["original_file_compiled", "false", "完成原文件兼容清偿后重新编译"],
      ["original_theorems_proven", "false", "需要真实定义、命题与证明"],
      ["physical_validity_verified", "false", "需要物理推导、参数与实验证据"],
      ["all_compatibility_complete", "false", "HasEquiv 与原文件问题未闭合"],
    ],
    [3200, 1000, 5306], 14,
  ),
  heading(titles[2]),
  makeTable(
    ["工具与边界", "当前结果", "说明"],
    [
      ["Lean", "4.35.0", "真实定义编译与 #print axioms"],
      ["Mathlib", data.toolchain.mathlib_rev, "固定提交，不使用浮动分支"],
      ["构建位置", data.toolchain.build_copy, "D 盘隔离副本；系统 PATH 未修改"],
      ["原文件", data.original.sha256, "复制一致；源文件未修改"],
    ],
    [2100, 4800, 2606], 12,
  ),
  body("后续先审议 HasEquiv ℝ 的命题形式，再决定使用等式、极限或显式误差估计。弱耦合极限、同位素比值和 Floquet 增强仍需真实定义、命题与证明；材料预测和实验复现另行推进。"),
  body("实际命令与原始输出见 compatible-run.log、compatible-compile.log 和 compatible-definitions.json。本切片不宣称项目级 Lean 验证、物理证明或实验验证完成。"),
];

const document = new Document({
  creator: "TOE-SYLVA",
  title: "Lean 兼容性清偿切片：常量、绑定与 Debye 类型",
  description: "两个独立定义、真实编译、公理依赖和开放边界。",
  features: { updateFields: true },
  styles: {
    paragraphStyles: [1, 2].map((level) => ({
      id: `TOC${level}`, name: `TOC ${level}`, basedOn: "Normal", next: "Normal", quickFormat: true,
      run: { font, size: 19, color: palette.dark },
      paragraph: { spacing: { after: 70, line: 240 }, indent: { left: (level - 1) * 360 } },
    })),
  },
  footnotes: {
    1: { children: [footnote("Source: room_temp_sc_Formalization.lean and read-only copy; original hash and static proof debt.")] },
    2: { children: [footnote("Source: Mathlib/Analysis/SpecialFunctions/Gamma/Digamma.lean; Real.eulerMascheroniConstant located directly in source.")] },
    3: { children: [footnote("Source: compatible-compile.log; actual compilation and #print axioms output for two definitions.")] },
    4: { children: [footnote("Source: proof-slice.json and clean-compile.log; previous clean definitions use ASCII lam and do not repair the original file.")] },
  },
  sections: [{
    properties: { page: { margin: { top: 1050, bottom: 1050, left: 1050, right: 1050 } } },
    headers: { default: new Header({ children: [para(run("TOE-SYLVA · Lean 兼容定义 · 局部清偿≠物理证明", { size: 17, color: palette.primary }), { alignment: AlignmentType.CENTER })] }) },
    footers: { default: new Footer({ children: [para(new TextRun({ children: [PageNumber.CURRENT], font, size: 17 }), { alignment: AlignmentType.CENTER })] }) },
    children,
  }],
});

fs.writeFileSync(outputPath, await Packer.toBuffer(document));
