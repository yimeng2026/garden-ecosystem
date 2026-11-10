import fs from "node:fs";
import path from "node:path";
import {
  AlignmentType, Document, Footer, FootnoteReferenceRun, Header, HeadingLevel,
  ImageRun, ImportedXmlComponent, Math as MathEquation, MathRun, Packer,
  PageBreak, PageNumber, Paragraph, ShadingType, Table, TableCell, TableRow,
  TextRun, WidthType,
} from "docx";

const outputPath = process.argv[2];
if (!outputPath) throw new Error("Usage: node build_report.js /absolute/path/PROOF_SLICE.docx");
const audit = path.dirname(outputPath);
const data = JSON.parse(fs.readFileSync(path.join(audit, "proof-slice.json"), "utf8"));
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
const titles = ["一、定义切片与真实结果", "二、原文件不兼容与既有债务", "三、工具链与剩余边界"];
const children = [
  para(run("Lean 独立清洁定义切片", { bold: true, size: 38, color: palette.dark }), { heading: HeadingLevel.TITLE, alignment: AlignmentType.CENTER, spacing: { before: 600, after: 220 } }),
  para(run("真实编译、公理依赖与原文件边界", { bold: true, size: 29, color: palette.primary }), { alignment: AlignmentType.CENTER, spacing: { after: 280 } }),
  para(run("3 个定义展开 · 仅 rfl · 标准三公理", { size: 21, color: palette.light }), { alignment: AlignmentType.CENTER, spacing: { after: 220 } }),
  para(run("2026-11-11　定义通过 ≠ 物理证明", { size: 19 }), { alignment: AlignmentType.CENTER, spacing: { after: 330 } }),
  heading("目录"),
  para(run("以下页码为可见缓存；在 Word/WPS 中更新域可刷新。", { size: 17, italics: true, color: palette.light })),
  toc(titles.map((title, index) => ({ title, level: 1, page: [2, 3, 3][index] }))),
  pageBreak(),

  heading(titles[0]),
  equation("3 definitions + 3 rfl = 3 machine checks"),
  citedBody("清洁定义切片在真实 Lean 4.35.0 下编译退出码为 0。三个新定理只依赖标准三公理，没有 sorryAx，也没有额外公理。", 2),
  makeTable(
    ["新定理", "证明", "sorryAx", "公理依赖"],
    Object.entries(data.dependencies.new_theorems).map(([name, row]) => [name, "rfl", String(row.sorryAx), row.axioms.join("、")]),
    [3600, 1000, 1200, 3706], 13,
  ),
  para(new ImageRun({ type: "png", data: fs.readFileSync(path.join(audit, "lean-proof-slice.png")), transformation: { width: 610, height: 305 } }), { alignment: AlignmentType.CENTER, keepNext: true }),
  para(run("图 1　真实编译：定义切片通过 ≠ 原文件通过。左轨只表示定义切片，右轨保留原文件错误与债务。", { size: 18, italics: true }), { alignment: AlignmentType.CENTER }),
  body("本次只验证三个定义展开，不调用原三条物理定理，不证明弱耦合极限、同位素效应或 Floquet 增强命题。物理有效性、材料预测、数值模型和实验验证均未验证。"),
  pageBreak(),

  heading(titles[1]),
  citedBody("原文件复制件与原文件的 SHA-256 完全一致，原文件未修改。静态扫描保留第 93、112、185 行共 3 处既有 sorry。", 1),
  makeTable(
    ["已观察错误／债务", "当前状态", "不得升级为"],
    [
      ["eulerMascheroni", "未定义", "原文件可直接编译"],
      ["λ 与 ω_D", "标识符与绑定错误", "只存在证明占位、没有语法问题"],
      ["HasEquiv ℝ", "实例缺失", "物理命题已经内核接受"],
      ["3 处 sorry", "原定理审计因编译失败不可用", "把 sorryAx 状态写成已确认或已清除"],
    ],
    [2400, 3600, 3506], 14,
  ),
  citedBody("原文件直接编译失败，错误同时包含未知标识、希腊字母 λ 的标识符问题、ω_D 未绑定和 HasEquiv ℝ 实例缺失。原始错误日志完整保留。", 3),
  body("因此本报告不声称原文件编译通过，也不伪造原三条定理的 sorryAx 审计。清洁定义是独立切片，不是对原文件语法错误或物理证明债务的修复。"),
  heading(titles[2]),
  makeTable(
    ["工具与证据", "当前结果", "边界"],
    [
      ["Lean", "4.35.0", "只用于本次真实定义编译"],
      ["Mathlib", data.toolchain.mathlib_rev, "固定提交，不使用浮动分支"],
      ["elan 资产", data.toolchain.elan_asset_sha256, "官方 Windows 资产，大小与哈希先验证后执行"],
      ["构建位置", data.toolchain.build_copy, "D 盘隔离副本；系统 PATH 未修改"],
      ["原文件", data.original.sha256, "复制一致；源文件未修改"],
    ],
    [2100, 5000, 2406], 12,
  ),
  citedBody("官方 elan 资产先核对 2508099 字节和 SHA-256，再解压执行。Lean、Lake、Mathlib、缓存和构建副本均位于 D 盘，系统 PATH 未修改。", 4),
  makeTable(
    ["剩余边界", "状态", "后续任务"],
    [
      ["原文件语法与模块兼容", "未解决", "另行建立版本兼容和错误清偿计划，不改写本次证据"],
      ["三条物理定理", "未证明", "需要真实定义、命题和证明，不得用 rfl 冒充"],
      ["材料预测与数值模型", "未验证", "需要原始输入、参数与可重跑计算"],
      ["独立实验与 Meissner", "未完成", "需要跨实验室正向复现与直接磁测量"],
    ],
    [2700, 1500, 5306], 14,
  ),
  body("本切片只完成最小真实定义验证，不宣称项目级 Lean 验证、物理证明或实验复现完成。完整命令和原始输出见 run.log、original-compile.log、clean-compile.log 和 proof-slice.json。"),
];

const document = new Document({
  creator: "TOE-SYLVA",
  title: "Lean 独立清洁定义切片：真实编译与原文件边界",
  description: "三个定义展开、标准公理、原文件不兼容和剩余物理证明债务。",
  features: { updateFields: true },
  styles: {
    paragraphStyles: [1, 2].map((level) => ({
      id: `TOC${level}`, name: `TOC ${level}`, basedOn: "Normal", next: "Normal", quickFormat: true,
      run: { font, size: 19, color: palette.dark },
      paragraph: { spacing: { after: 70, line: 240 }, indent: { left: (level - 1) * 360 } },
    })),
  },
  footnotes: {
    1: { children: [footnote("Source: room_temp_sc_Formalization.lean and read-only copy; original SHA-256 and three static sorry lines.")] },
    2: { children: [footnote("Source: clean-compile.log; actual clean definition compilation and #print axioms output.")] },
    3: { children: [footnote("Source: original-compile.log; actual original compilation failure and source incompatibility markers.")] },
    4: { children: [footnote("Source: bootstrap-result.json; official asset hash, D: isolated Lean 4.35.0 and Lake versions.")] },
  },
  sections: [{
    properties: { page: { margin: { top: 1050, bottom: 1050, left: 1050, right: 1050 } } },
    headers: { default: new Header({ children: [para(run("TOE-SYLVA · Lean 定义切片 · 定义通过≠物理证明", { size: 17, color: palette.primary }), { alignment: AlignmentType.CENTER })] }) },
    footers: { default: new Footer({ children: [para(new TextRun({ children: [PageNumber.CURRENT], font, size: 17 }), { alignment: AlignmentType.CENTER })] }) },
    children,
  }],
});

fs.writeFileSync(outputPath, await Packer.toBuffer(document));
